"""Pure, read-only adapters for the frozen M12 presentation-layer review UI.

These helpers never load a fitted model or generate predictions or SHAP. The
logistic transform is used only to reconcile already saved explanation values.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.special import expit


SELECTED = "M12Q_quarterly_only_full_population_median"
COHORTS = ("2020Q2", "2019Q2", "2018Q4")
SCALE_FEATURES = ("log_assets", "log_sales", "log_ppent", "log_shares")
SEEDS = (11, 23, 42, 71, 101)
PREDICTION_COLUMNS = [
    "issuer_quarter_row", "issuer_key", "gvkey", "valid_cik", "cik", "conm",
    "tic", "calendar_quarter", "freq", "panel_row_number", "fiscal_period_date",
    "information_available_date", "forecast_window_start_exclusive",
    "forecast_window_end_inclusive", "candidate", "diagnostic_kind", "seed_count",
    "ensemble_raw_model_output", "ensemble_uncalibrated_score", "rank",
    "score_percentile", "is_selected_default",
]
EXPLANATION_FILES = frozenset({
    "historical_M12_all_evaluation_raw_shap.parquet",
    "historical_M12_all_evaluation_concept_shap.parquet",
    "historical_M12_all_evaluation_theme_shap.parquet",
    "historical_M12_top_visible_raw_drivers.parquet",
    "historical_M12_inline_remainder_rows.parquet",
    "historical_M12_scale_non_scale_shap_subtotals.parquet",
})
CONTRIBUTION_COLUMNS = [
    "row_key", "calendar_quarter", "issuer_quarter_row", "rank", "ticker_display",
    "conm", "scale_net", "non_scale_net", "total_net", "base_value", "raw_output",
    "ranking_score", "raw_error", "score_error",
]


class ReviewDataError(ValueError):
    """A required saved artifact is missing or cannot be aligned safely."""


def _require_file(path: Path) -> Path:
    if not path.is_file():
        raise ReviewDataError(f"Required saved artifact is unavailable: {path}")
    return path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], label: str) -> None:
    missing = set(columns).difference(frame.columns)
    if missing:
        raise ReviewDataError(f"{label} is missing required columns: {', '.join(sorted(missing))}")


def _quarter(quarter: str) -> str:
    if quarter not in COHORTS:
        raise ReviewDataError(f"Unsupported stored fiscal reporting cohort: {quarter}")
    return quarter


def _integer(value: object, label: str, minimum: int = 0) -> int:
    if isinstance(value, (bool, np.bool_)):
        raise ReviewDataError(f"{label} must be an integer, not a boolean.")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ReviewDataError(f"{label} must be a finite integer.") from exc
    if not math.isfinite(number) or not number.is_integer() or number < minimum:
        raise ReviewDataError(f"{label} must be an integer of at least {minimum}.")
    return int(number)


def _text(value: object) -> str:
    return "" if pd.isna(value) else str(value).strip()


def _bool(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, str) and value in {"True", "False"}:
        return value == "True"
    raise ReviewDataError(f"Expected an explicit boolean flag, received {value!r}.")


def top_share(rank: int, n: int) -> float:
    """Return inclusive stored-rank position in the unchanged full cohort."""
    size = _integer(n, "Cohort size", 1)
    position = _integer(rank, "Stored rank", 1)
    if position > size:
        raise ReviewDataError("Stored rank cannot exceed the full cohort size.")
    return 100.0 * position / size


def format_top_share(rank: int, n: int) -> str:
    value = top_share(rank, n)
    formatted = f"{value:.2f}"
    return "Top <0.01%" if formatted == "0.00" else f"Top {formatted}%"


def load_predictions(out: Path, quarter: str) -> pd.DataFrame:
    """Read the exact selected candidate without loading individual outcomes."""
    quarter = _quarter(quarter)
    path = _require_file(Path(out) / "historical_M12_ensemble_predictions.parquet")
    frame = pd.read_parquet(path, columns=PREDICTION_COLUMNS, filters=[
        ("candidate", "=", SELECTED), ("diagnostic_kind", "=", "candidate"),
        ("calendar_quarter", "=", quarter),
    ])
    _require_columns(frame, PREDICTION_COLUMNS, "Stored predictions")
    if frame.empty:
        raise ReviewDataError(f"No saved selected-candidate predictions exist for {quarter}.")
    if not (frame.candidate.eq(SELECTED) & frame.diagnostic_kind.eq("candidate")
            & frame.calendar_quarter.eq(quarter)).all():
        raise ReviewDataError("Stored prediction selection mixes models or fiscal cohorts.")
    ids = frame.issuer_quarter_row.map(lambda value: _integer(value, "Issuer-row identity"))
    ranks = frame["rank"].map(lambda value: _integer(value, "Stored rank", 1))
    if ids.duplicated().any() or ranks.duplicated().any() or set(ranks) != set(range(1, len(frame) + 1)):
        raise ReviewDataError("Stored issuer identities or full-cohort ranks are not unique and complete.")
    numeric = frame[["ensemble_raw_model_output", "ensemble_uncalibrated_score"]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all() or not frame.seed_count.eq(len(SEEDS)).all():
        raise ReviewDataError("Stored predictions contain invalid numbers or a different seed ensemble.")
    if not frame.ensemble_uncalibrated_score.between(0, 1, inclusive="both").all():
        raise ReviewDataError("A stored ranking score lies outside the logistic-output range.")
    frame = frame.sort_values("rank", kind="stable").copy()
    frame["row_key"] = [f"{quarter}:{int(value)}" for value in frame.issuer_quarter_row]
    frame["top_share_pct"] = frame["rank"].map(lambda rank: top_share(rank, len(frame)))
    frame["ticker_display"] = [
        _text(ticker) or (f"GVKEY {_text(gvkey)}" if _text(gvkey) else f"Issuer row {int(row_id)}")
        for ticker, gvkey, row_id in zip(frame.tic, frame.gvkey, frame.issuer_quarter_row)
    ]
    return frame.reset_index(drop=True)


def _manifest_base(manifest: dict, quarter: str) -> float:
    if manifest.get("selected_model") != SELECTED:
        raise ReviewDataError("The explanation manifest is not the selected M12Q candidate.")
    records = [item for item in manifest.get("seed_models", []) if item.get("quarter") == quarter]
    if len(records) != len(SEEDS) or sorted(item.get("seed") for item in records) != list(SEEDS):
        raise ReviewDataError(f"The saved ensemble manifest has incompatible seeds for {quarter}.")
    try:
        bases = np.asarray([item["base_value"] for item in records], dtype=float)
    except (KeyError, TypeError, ValueError) as exc:
        raise ReviewDataError("A saved per-seed SHAP baseline is unavailable.") from exc
    if not np.isfinite(bases).all():
        raise ReviewDataError("A saved per-seed SHAP baseline is not finite.")
    return float(np.mean(bases))


def load_contract(out: Path, public_out: Path | None = None) -> dict:
    """Validate the saved selected feature order and explicit baseline manifest."""
    out = Path(out)
    prereg = json.loads(_require_file(out / "historical_M12_preregistration_contract.json").read_text(encoding="utf-8"))
    manifest = json.loads(_require_file(out / "historical_M12_selected_ensemble_model_manifest.json").read_text(encoding="utf-8"))
    try:
        features = list(prereg["candidates"][SELECTED]["features"])
    except (KeyError, TypeError) as exc:
        raise ReviewDataError("The selected M12Q ordered feature contract is unavailable.") from exc
    if not features or len(features) != len(set(features)) or not all(isinstance(item, str) for item in features):
        raise ReviewDataError("The ordered feature contract contains missing or duplicate representations.")
    digest = hashlib.sha256("\n".join(features).encode("utf-8")).hexdigest()
    if manifest.get("ordered_feature_name_sha256") != digest or manifest.get("feature_count") != len(features):
        raise ReviewDataError("The ordered feature contract does not match the saved ensemble manifest.")
    for quarter in COHORTS:
        _manifest_base(manifest, quarter)
    dictionary_out = out if public_out is None else Path(public_out)
    dictionary = pd.read_csv(_require_file(dictionary_out / "historical_M12_feature_concept_theme_scale_contract.csv"))
    _require_columns(dictionary, ["feature_name", "scale_feature"], "Saved feature dictionary")
    if dictionary.feature_name.duplicated().any() or not set(features).issubset(dictionary.feature_name):
        raise ReviewDataError("The saved dictionary does not map every selected feature exactly once.")
    dictionary = dictionary.set_index("feature_name").loc[features].reset_index()
    flags = dictionary.scale_feature.map(_bool)
    scale_features = dictionary.loc[flags, "feature_name"].tolist()
    if set(scale_features) != set(SCALE_FEATURES):
        raise ReviewDataError("The selected M12Q scale membership is not the fixed four-feature contract.")
    return {"features": features, "scale_features": scale_features, "manifest": manifest, "dictionary": dictionary}


def read_rows(out: Path, filename: str, quarter: str, ids: Sequence[int], columns: Sequence[str] | None = None) -> pd.DataFrame:
    """Read only requested stored explanation rows using Parquet projection."""
    quarter = _quarter(quarter)
    if filename not in EXPLANATION_FILES:
        raise ReviewDataError("Only the explicit frozen explanation artifact names are allowed.")
    path = _require_file(Path(out) / filename)
    requested_ids = sorted({_integer(value, "Issuer-row identity") for value in ids})
    available = pq.read_schema(path).names
    projection = list(columns) if columns is not None else available
    if not set(projection).issubset(available):
        raise ReviewDataError(f"Requested columns are absent from {filename}.")
    if not requested_ids:
        return pd.DataFrame(columns=projection)
    return pd.read_parquet(path, columns=projection, filters=[
        ("calendar_quarter", "=", quarter), ("issuer_quarter_row", "in", requested_ids),
    ])


def aggregate_contributions(predictions: pd.DataFrame, raw: pd.DataFrame, contract: dict, tolerance: float = 1e-10) -> pd.DataFrame:
    """Sum saved signed SHAP values and reconcile against saved predictions."""
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ReviewDataError("Reconciliation tolerance must be finite and positive.")
    _require_columns(predictions, ["row_key", "calendar_quarter", "issuer_quarter_row", "rank",
                                  "ticker_display", "conm", "ensemble_raw_model_output",
                                  "ensemble_uncalibrated_score"], "Displayed predictions")
    if predictions.empty and raw.empty:
        return pd.DataFrame(columns=CONTRIBUTION_COLUMNS)
    _require_columns(raw, ["calendar_quarter", "issuer_quarter_row", "feature_name", "shap_value",
                          "scale_feature", "base_value", "raw_model_output", "uncalibrated_score",
                          "seed_count"], "Saved raw SHAP")
    features = list(contract["features"])
    scale = set(contract["scale_features"])
    if len(features) != len(set(features)) or scale != set(SCALE_FEATURES) or not scale.issubset(features):
        raise ReviewDataError("Raw SHAP aggregation requires the exact four scale members and unique features.")
    keys = ["calendar_quarter", "issuer_quarter_row"]
    if predictions.duplicated(keys).any() or predictions.row_key.duplicated().any():
        raise ReviewDataError("Displayed prediction identities are duplicated.")
    expected_keys = set(predictions[keys].itertuples(index=False, name=None))
    observed_keys = set(raw[keys].itertuples(index=False, name=None))
    if expected_keys != observed_keys or raw.duplicated(keys + ["feature_name"]).any():
        raise ReviewDataError("Saved SHAP issuer membership is missing, duplicated, or outside the displayed set.")
    if not raw.seed_count.eq(len(SEEDS)).all():
        raise ReviewDataError("Saved SHAP does not belong to the five-seed ensemble.")
    numeric = raw[["shap_value", "base_value", "raw_model_output", "uncalibrated_score"]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ReviewDataError("Saved SHAP contains non-finite contribution or reconciliation values.")
    expected_flags = raw.feature_name.isin(scale).to_numpy()
    if not np.array_equal(raw.scale_feature.map(_bool).to_numpy(), expected_flags):
        raise ReviewDataError("Saved raw SHAP scale flags disagree with the frozen feature contract.")
    grouped = raw.groupby(keys, sort=False, dropna=False)
    rows = []
    for pred in predictions.to_dict("records"):
        quarter, row_id = pred["calendar_quarter"], _integer(pred["issuer_quarter_row"], "Issuer-row identity")
        _quarter(quarter)
        if pred["row_key"] != f"{quarter}:{row_id}":
            raise ReviewDataError("The selection key does not match the stored issuer and cohort.")
        part = grouped.get_group((quarter, row_id))
        if len(part) != len(features) or set(part.feature_name) != set(features):
            raise ReviewDataError(f"The complete selected feature set is unavailable for {pred['row_key']}.")
        for column in ("issuer_key", "gvkey", "conm", "tic", "fiscal_period_date", "information_available_date",
                       "forecast_window_start_exclusive", "forecast_window_end_inclusive"):
            if column in part.columns and column in pred:
                matching = part[column].isna() if pd.isna(pred[column]) else part[column].eq(pred[column])
                if not matching.all():
                    raise ReviewDataError(f"Stored SHAP identity or date differs from its prediction: {column}.")
        if any(part[column].nunique(dropna=False) != 1 for column in ("base_value", "raw_model_output", "uncalibrated_score")):
            raise ReviewDataError("Saved explanation baseline, raw output, or score differs within one issuer.")
        baseline = _manifest_base(contract["manifest"], quarter)
        saved_base = float(part.base_value.iloc[0])
        if abs(saved_base - baseline) > tolerance:
            raise ReviewDataError("Saved SHAP baseline does not match the mean of the exact quarter's seed baselines.")
        by_feature = part.set_index("feature_name").loc[features]
        scale_net = float(by_feature.loc[by_feature.index.isin(scale), "shap_value"].sum())
        non_scale_net = float(by_feature.loc[~by_feature.index.isin(scale), "shap_value"].sum())
        total_net = scale_net + non_scale_net
        margin = float(pred["ensemble_raw_model_output"])
        score = float(pred["ensemble_uncalibrated_score"])
        if not math.isfinite(margin) or not math.isfinite(score):
            raise ReviewDataError("Stored prediction reconciliation numbers are not finite.")
        raw_error = abs(saved_base + total_net - margin)
        score_error = abs(float(expit(saved_base + total_net)) - score)
        if max(raw_error, score_error, abs(float(part.raw_model_output.iloc[0]) - margin),
               abs(float(part.uncalibrated_score.iloc[0]) - score)) > tolerance:
            raise ReviewDataError(f"Saved SHAP and prediction reconciliation failed for {pred['row_key']}.")
        rows.append({"row_key": pred["row_key"], "calendar_quarter": quarter, "issuer_quarter_row": row_id,
                     "rank": pred["rank"], "ticker_display": pred["ticker_display"], "conm": pred["conm"],
                     "scale_net": scale_net, "non_scale_net": non_scale_net, "total_net": total_net,
                     "base_value": saved_base, "raw_output": margin, "ranking_score": score,
                     "raw_error": raw_error, "score_error": score_error})
    return pd.DataFrame(rows, columns=CONTRIBUTION_COLUMNS)


def select_overview(predictions: pd.DataFrame, query: str = "", limit: int | None = 15,
                    page: int = 1, page_size: int = 25) -> tuple[pd.DataFrame, int, int]:
    """Filter saved ranks without changing their population denominator."""
    page = _integer(page, "Page", 1)
    page_size = _integer(page_size, "Page size", 1)
    _require_columns(predictions, ["rank", "conm", "tic", "gvkey"], "Overview predictions")
    ordered = predictions.sort_values("rank", kind="stable")
    search = str(query).strip().casefold()
    if search:
        mask = pd.Series(False, index=ordered.index)
        for column in ("conm", "tic", "gvkey"):
            mask |= ordered[column].fillna("").astype(str).str.casefold().str.contains(search, regex=False)
        ordered = ordered.loc[mask]
    elif limit is not None:
        ordered = ordered.head(_integer(limit, "Top-company limit", 1))
        return ordered.copy(), len(ordered), 1
    count = len(ordered)
    pages = max(1, math.ceil(count / page_size))
    start = (min(page, pages) - 1) * page_size
    return ordered.iloc[start:start + page_size].copy(), count, pages


def overview_columns(predictions: pd.DataFrame) -> pd.DataFrame:
    """Build the exact five-column Overview table, excluding ex-post outcomes."""
    _require_columns(predictions, ["rank", "ticker_display", "conm", "top_share_pct",
                                  "ensemble_uncalibrated_score"], "Overview predictions")
    def share_label(value: float) -> str:
        if not math.isfinite(float(value)) or not 0 < float(value) <= 100:
            raise ReviewDataError("Overview top-share values must remain within the full cohort bounds.")
        return "Top <0.01%" if f"{float(value):.2f}" == "0.00" else f"Top {float(value):.2f}%"
    return pd.DataFrame({"Rank": predictions["rank"], "Ticker": predictions.ticker_display,
                         "Company name": predictions.conm,
                         "Top X% of cohort": predictions.top_share_pct.map(share_label),
                         "Ranking score (uncalibrated)": predictions.ensemble_uncalibrated_score})


def key_from_table_event(event: Mapping | None, displayed_keys: Sequence[str]) -> str | None:
    """Resolve dataframe original-row positions, never display names or tickers."""
    if not isinstance(event, Mapping) or not isinstance(event.get("selection"), Mapping):
        return None
    rows = event["selection"].get("rows", [])
    if not isinstance(rows, (list, tuple)) or len(rows) != 1:
        return None
    position = rows[0]
    if isinstance(position, (bool, np.bool_)) or not isinstance(position, (int, np.integer)):
        return None
    return displayed_keys[int(position)] if 0 <= position < len(displayed_keys) else None


def key_from_chart_event(event: Mapping | None, cohort: str, allowed_keys: Sequence[str]) -> tuple[str, str] | None:
    """Accept only a stable, allow-listed issuer/cohort/group chart payload."""
    if not isinstance(event, Mapping) or not isinstance(event.get("selection"), Mapping):
        return None
    selected = event["selection"].get("open_company", [])
    if not isinstance(selected, (list, tuple)) or len(selected) != 1 or not isinstance(selected[0], Mapping):
        return None
    item = selected[0]
    key, group = item.get("row_key"), item.get("group")
    if not isinstance(key, str) or not isinstance(group, str):
        return None
    if item.get("calendar_quarter") != cohort or key not in set(allowed_keys) or group not in {"Scale", "Non-scale"}:
        return None
    if not key.startswith(f"{cohort}:"):
        return None
    return key, group


def resolve_selection(key: str | None, predictions: pd.DataFrame) -> str | None:
    if predictions.empty:
        return None
    _require_columns(predictions, ["row_key", "rank"], "Selection predictions")
    if key in set(predictions.row_key):
        return key
    return str(predictions.sort_values("rank", kind="stable").iloc[0].row_key)


def chart_segments(contributions: pd.DataFrame) -> pd.DataFrame:
    """Build two signed stacked segments per company without absolute scaling."""
    _require_columns(contributions, CONTRIBUTION_COLUMNS, "Reconciled contributions")
    rows = []
    for item in contributions.sort_values("rank", kind="stable").to_dict("records"):
        positive, negative = 0.0, 0.0
        ticker = _text(item["ticker_display"])
        short_name = ticker if ticker and not ticker.startswith(("GVKEY ", "Issuer row ")) else _text(item["conm"])
        short_name = short_name if len(short_name) <= 26 else short_name[:23] + "..."
        label = f"#{int(item['rank']):,} · {short_name}"
        for group, field in (("Scale", "scale_net"), ("Non-scale", "non_scale_net")):
            value = float(item[field])
            if not math.isfinite(value):
                raise ReviewDataError("Chart contributions must be finite signed subtotals.")
            start = positive if value >= 0 else negative
            end = start + value
            if value >= 0:
                positive = end
            else:
                negative = end
            rows.append(item | {"group": group, "contribution": value, "start": start, "end": end,
                                "label": label, "net_label": f"Net {float(item['total_net']):+.3f}"})
    return pd.DataFrame(rows, columns=CONTRIBUTION_COLUMNS + ["group", "contribution", "start", "end", "label", "net_label"])
