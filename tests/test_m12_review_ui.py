"""Presentation-only checks against frozen M12Q outputs; never fit or infer a model."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from scipy.special import expit

from dashboard import m12_review_ui_helpers as ui
from dashboard.sharing_paths import PRIVATE_DATA, PUBLIC_DATA, missing_private_files


ROOT = Path(__file__).resolve().parents[1]
OUT = PRIVATE_DATA
APP = ROOT / "dashboard" / "historical_m12_review_ui.py"
RAW_FILE = "historical_M12_all_evaluation_raw_shap.parquet"
EXPECTED_COUNTS = {"2018Q4": 11278, "2019Q2": 11621, "2020Q2": 11769}
RAW_COLUMNS = [
    "calendar_quarter", "issuer_quarter_row", "feature_name", "shap_value",
    "base_value", "raw_model_output", "uncalibrated_score", "seed_count",
    "scale_feature",
]


@pytest.fixture(scope="module")
def contract():
    if missing_private_files():
        pytest.skip("Authorized local-only M12 artifacts not supplied; no replacement data generated.")
    return ui.load_contract(OUT, PUBLIC_DATA)


@pytest.fixture(scope="module")
def predictions():
    if missing_private_files():
        pytest.skip("Authorized local-only M12 artifacts not supplied; no replacement data generated.")
    return {quarter: ui.load_predictions(OUT, quarter) for quarter in ui.COHORTS}


@pytest.mark.parametrize("quarter", EXPECTED_COUNTS)
def test_predictions_preserve_every_stored_row_score_rank_and_date(predictions, quarter):
    actual = predictions[quarter]
    source = pd.read_parquet(
        OUT / "historical_M12_ensemble_predictions.parquet",
        columns=ui.PREDICTION_COLUMNS,
        filters=[
            ("candidate", "=", ui.SELECTED),
            ("diagnostic_kind", "=", "candidate"),
            ("calendar_quarter", "=", quarter),
        ],
    ).sort_values("rank", kind="stable").reset_index(drop=True)
    assert len(actual) == EXPECTED_COUNTS[quarter]
    pd.testing.assert_frame_equal(actual[source.columns].reset_index(drop=True), source)
    assert actual.row_key.is_unique
    assert actual.row_key.tolist() == [f"{quarter}:{value}" for value in source.issuer_quarter_row]
    assert actual["rank"].tolist() == list(range(1, len(actual) + 1))
    assert "issuer_label" not in actual.columns
    assert actual.seed_count.eq(5).all()
    assert actual.candidate.eq(ui.SELECTED).all()
    assert actual.diagnostic_kind.eq("candidate").all()
    assert actual.valid_cik.isna().sum() == source.valid_cik.isna().sum()
    assert actual.tic.isna().sum() == source.tic.isna().sum()


def test_fixed_four_scale_contract_and_selected_ensemble(contract):
    assert len(contract["features"]) == len(set(contract["features"])) == 36
    assert tuple(contract["scale_features"]) == ui.SCALE_FEATURES
    assert set(contract["scale_features"]) == {"log_assets", "log_sales", "log_ppent", "log_shares"}
    assert len(set(contract["features"]) - set(contract["scale_features"])) == 32
    assert contract["manifest"]["selected_model"] == ui.SELECTED


@pytest.mark.parametrize("rank,count,expected", [(1, 11769, 100 / 11769), (451, 11769, 45100 / 11769), (11769, 11769, 100), (1, 1, 100)])
def test_top_share_is_inclusive_original_rank_position(rank, count, expected):
    assert ui.top_share(rank, count) == pytest.approx(expected, rel=0, abs=1e-12)
    assert ui.format_top_share(rank, count) != "Top 0.00%"


def test_top_share_display_examples_and_very_large_denominator():
    assert "0.01%" in ui.format_top_share(1, 11769)
    assert "3.83%" in ui.format_top_share(451, 11769)
    assert "100" in ui.format_top_share(11769, 11769)
    assert "0.00%" not in ui.format_top_share(1, 1000000)


@pytest.mark.parametrize("rank,count", [(0, 10), (-1, 10), (11, 10), (1, 0)])
def test_invalid_top_share_inputs_fail_explicitly(rank, count):
    with pytest.raises((ValueError, ui.ReviewDataError)):
        ui.top_share(rank, count)


@pytest.mark.parametrize("limit", [15, 25, 50, 100])
def test_top_n_keeps_scores_ranks_and_full_cohort_denominator(predictions, limit):
    full = predictions["2020Q2"]
    selected, _, _ = ui.select_overview(full, limit=limit)
    pd.testing.assert_frame_equal(selected.reset_index(drop=True), full.head(limit).reset_index(drop=True))
    np.testing.assert_allclose(selected.top_share_pct, 100 * selected["rank"] / len(full), rtol=0, atol=1e-12)


def test_full_pagination_reaches_every_issuer_once_in_original_rank_order(predictions):
    full = predictions["2020Q2"]
    first, count, pages = ui.select_overview(full, limit=None, page=1, page_size=100)
    keys = first.row_key.tolist()
    for page in range(2, pages + 1):
        part, this_count, this_pages = ui.select_overview(full, limit=None, page=page, page_size=100)
        assert (this_count, this_pages) == (count, pages)
        keys.extend(part.row_key.tolist())
    assert count == len(full)
    assert keys == full.row_key.tolist()
    assert len(keys) == len(set(keys))


def test_search_reaches_company_outside_top15_and_keeps_original_metrics(predictions):
    full = predictions["2020Q2"]
    selected = full.loc[full["rank"].eq(451)].iloc[0]
    found, count, _ = ui.select_overview(full, query=str(selected.conm).lower(), limit=15)
    match = found.loc[found.row_key.eq(selected.row_key)].iloc[0]
    assert count >= 1
    assert match["rank"] == 451
    assert match.ensemble_uncalibrated_score == selected.ensemble_uncalibrated_score
    assert match.top_share_pct == selected.top_share_pct
    ticker_found, _, _ = ui.select_overview(full, query="rmbs", limit=15)
    assert "RMBS" in ticker_found.tic.tolist()


def test_no_match_is_empty_and_small_cohort_and_ties_are_not_reranked(predictions):
    full = predictions["2020Q2"]
    empty, count, _ = ui.select_overview(full, query="no-such-issuer-__987654321__")
    assert empty.empty and count == 0
    assert ui.resolve_selection(full.row_key.iloc[0], empty) is None
    small = full.head(2).copy()
    small["ensemble_uncalibrated_score"] = 0.5
    small["tic"] = pd.NA
    small["valid_cik"] = pd.NA
    chosen, count, _ = ui.select_overview(small, limit=100)
    assert count == 2
    assert chosen["rank"].tolist() == [1, 2]
    assert chosen.row_key.tolist() == small.row_key.tolist()
    assert chosen.top_share_pct.tolist() == small.top_share_pct.tolist()


def test_missing_ticker_and_ids_remain_reachable_with_fallbacks_and_tied_scores(predictions, monkeypatch):
    # Small synthetic edge case only: no new file or market-result artifact is created.
    sample = predictions["2020Q2"].head(3)[ui.PREDICTION_COLUMNS].copy()
    sample.loc[:, "tic"] = pd.NA
    sample.loc[sample.index[1], "gvkey"] = pd.NA
    sample.loc[:, "valid_cik"] = pd.NA
    sample.loc[:, "ensemble_uncalibrated_score"] = 0.5
    monkeypatch.setattr(pd, "read_parquet", lambda *args, **kwargs: sample.copy())
    result = ui.load_predictions(OUT, "2020Q2")
    assert len(result) == 3
    assert result.ticker_display.iloc[0] == f"GVKEY {sample.gvkey.iloc[0]}"
    assert result.ticker_display.iloc[1] == f"Issuer row {sample.issuer_quarter_row.iloc[1]}"
    assert result.ticker_display.str.len().gt(0).all()
    assert result["rank"].tolist() == [1, 2, 3]
    assert result.valid_cik.isna().all()
    assert result.row_key.is_unique
    assert result.ensemble_uncalibrated_score.eq(0.5).all()
    assert result.top_share_pct.tolist() == pytest.approx([100 / 3, 200 / 3, 100])


def test_overview_only_exposes_the_five_requested_primary_columns(predictions):
    shown = ui.overview_columns(predictions["2020Q2"].head(15))
    assert list(shown.columns) == ["Rank", "Ticker", "Company name", "Top X% of cohort", "Ranking score (uncalibrated)"]
    assert len(shown) == 15
    assert not any("outcome" in name.lower() or "label" in name.lower() for name in shown.columns)


def test_table_event_uses_original_payload_position_not_display_label(predictions):
    rows = predictions["2020Q2"].iloc[[10, 2, 7]]
    keys = rows.row_key.tolist()
    assert ui.key_from_table_event({"selection": {"rows": [1]}}, keys) == keys[1]
    for event in ({}, {"selection": {"rows": []}}, {"selection": {"rows": [99]}}, {"selection": {"rows": [-1]}}):
        assert ui.key_from_table_event(event, keys) is None


@pytest.mark.parametrize("group", ["Scale", "Non-scale"])
def test_chart_payload_identifies_either_segment_with_cohort_and_stable_key(predictions, group):
    rows = predictions["2020Q2"]
    key = rows.row_key.iloc[4]
    event = {"selection": {"open_company": [{"row_key": key, "calendar_quarter": "2020Q2", "group": group}]}}
    assert ui.key_from_chart_event(event, "2020Q2", set(rows.row_key)) == (key, group)
    assert ui.key_from_chart_event(event, "2019Q2", set(predictions["2019Q2"].row_key)) is None
    assert ui.key_from_chart_event(event, "2020Q2", {rows.row_key.iloc[0]}) is None


def test_missing_and_malformed_chart_events_cannot_select_company(predictions):
    keys = set(predictions["2020Q2"].row_key)
    for event in ({}, {"selection": {"open_company": []}}, {"selection": {"open_company": [{"row_key": "2020Q2:bad", "calendar_quarter": "2020Q2", "group": "Scale"}]}}, {"selection": {"open_company": [{"row_key": next(iter(keys)), "calendar_quarter": "2020Q2", "group": "Unknown"}]}}):
        assert ui.key_from_chart_event(event, "2020Q2", keys) is None


def test_selection_preserves_identity_and_resets_incompatible_cohort(predictions):
    current = predictions["2020Q2"]
    key = current.row_key.iloc[15]
    assert ui.resolve_selection(key, current.sample(frac=1, random_state=3)) == key
    earlier = predictions["2019Q2"]
    assert ui.resolve_selection(key, earlier) == earlier.row_key.iloc[0]
    assert ui.resolve_selection(None, current) == current.row_key.iloc[0]


@pytest.mark.parametrize("quarter", EXPECTED_COUNTS)
def test_every_stored_company_signed_shap_reconciles_without_model_execution(predictions, contract, quarter):
    full = predictions[quarter]
    # Projection and an issuer-bounded batch keep the audit below one whole explanation table.
    for start in range(0, len(full), 1000):
        part = full.iloc[start:start + 1000]
        raw = ui.read_rows(OUT, RAW_FILE, quarter, part.issuer_quarter_row.tolist(), columns=RAW_COLUMNS)
        actual = ui.aggregate_contributions(part, raw, contract)
        assert actual.row_key.tolist() == part.row_key.tolist()
        assert actual.raw_error.abs().max() <= 1e-10
        assert actual.score_error.abs().max() <= 1e-10
        independent = raw.assign(is_scale=raw.feature_name.isin(ui.SCALE_FEATURES))
        scale = independent.loc[independent.is_scale].groupby("issuer_quarter_row").shap_value.sum()
        non_scale = independent.loc[~independent.is_scale].groupby("issuer_quarter_row").shap_value.sum()
        ids = actual.issuer_quarter_row
        np.testing.assert_allclose(actual.scale_net, scale.reindex(ids), rtol=0, atol=1e-12)
        np.testing.assert_allclose(actual.non_scale_net, non_scale.reindex(ids), rtol=0, atol=1e-12)
        np.testing.assert_allclose(actual.total_net, actual.scale_net + actual.non_scale_net, rtol=0, atol=1e-12)
        np.testing.assert_allclose(actual.base_value + actual.total_net, part.ensemble_raw_model_output, rtol=0, atol=1e-10)
        np.testing.assert_allclose(expit(actual.raw_output), part.ensemble_uncalibrated_score, rtol=0, atol=1e-12)


@pytest.mark.parametrize("defect", ["missing_feature", "duplicate_feature", "wrong_quarter", "wrong_seed_count", "wrong_baseline", "uniform_wrong_baseline", "wrong_scale_flag", "wrong_raw_margin", "wrong_score"])
def test_alignment_errors_fail_closed(predictions, contract, defect):
    part = predictions["2020Q2"].head(1)
    raw = ui.read_rows(OUT, RAW_FILE, "2020Q2", part.issuer_quarter_row.tolist(), columns=RAW_COLUMNS)
    if defect == "missing_feature":
        raw = raw.iloc[1:].copy()
    elif defect == "duplicate_feature":
        raw = pd.concat([raw, raw.head(1)], ignore_index=True)
    elif defect == "wrong_quarter":
        raw.loc[:, "calendar_quarter"] = "2019Q2"
    elif defect == "wrong_seed_count":
        raw.loc[:, "seed_count"] = 4
    elif defect == "wrong_baseline":
        raw.loc[raw.index[0], "base_value"] += 0.01
    elif defect == "uniform_wrong_baseline":
        raw.loc[:, "base_value"] += 0.01
    elif defect == "wrong_scale_flag":
        raw.loc[raw.index[0], "scale_feature"] = not raw.loc[raw.index[0], "scale_feature"]
    elif defect == "wrong_raw_margin":
        raw.loc[:, "raw_model_output"] += 0.01
    elif defect == "wrong_score":
        raw.loc[:, "uncalibrated_score"] += 0.01
    with pytest.raises(ui.ReviewDataError):
        ui.aggregate_contributions(part, raw, contract)


def test_signed_segments_preserve_opposing_signs_zeros_and_original_order(predictions, contract):
    part = predictions["2020Q2"].head(1)
    raw = ui.read_rows(OUT, RAW_FILE, "2020Q2", part.issuer_quarter_row.tolist(), columns=RAW_COLUMNS)
    sample = ui.aggregate_contributions(part, raw, contract)
    # Synthetic subtotals exercise chart geometry only and are never exposed as market data.
    edge_cases = pd.concat([sample] * 5, ignore_index=True)
    edge_cases["rank"] = [5, 4, 3, 2, 1]
    edge_cases["scale_net"] = [2.0, -2.0, 2.0, -2.0, 0.0]
    edge_cases["non_scale_net"] = [3.0, -3.0, -3.0, 3.0, 0.0]
    edge_cases["total_net"] = edge_cases.scale_net + edge_cases.non_scale_net
    segments = ui.chart_segments(edge_cases)
    assert segments["rank"].tolist() == [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]
    for rank, rows in segments.groupby("rank", sort=False):
        assert rows.group.tolist() == ["Scale", "Non-scale"]
        np.testing.assert_allclose(rows.end - rows.start, rows.contribution, rtol=0, atol=0)
        assert rows.contribution.sum() == rows.total_net.iloc[0]
        scale, non_scale = rows.iloc[0], rows.iloc[1]
        assert scale.start == 0
        if scale.contribution * non_scale.contribution < 0:
            assert non_scale.start == 0
        elif scale.contribution != 0:
            assert non_scale.start == scale.end
        assert all("Net " in value for value in rows.net_label)
    assert segments.loc[segments["rank"].eq(1), ["start", "end", "contribution"]].eq(0).all().all()


def test_explanation_identity_dates_cannot_drift_from_selected_prediction(predictions, contract):
    part = predictions["2020Q2"].head(1)
    columns = RAW_COLUMNS + ["information_available_date", "conm"]
    raw = ui.read_rows(OUT, RAW_FILE, "2020Q2", part.issuer_quarter_row.tolist(), columns=columns)
    raw.loc[:, "information_available_date"] += pd.Timedelta(days=1)
    with pytest.raises(ui.ReviewDataError, match="date differs"):
        ui.aggregate_contributions(part, raw, contract)


def test_missing_artifacts_and_disallowed_paths_fail_without_synthetic_data(tmp_path):
    with pytest.raises(ui.ReviewDataError):
        ui.load_predictions(tmp_path, "2020Q2")
    with pytest.raises(ui.ReviewDataError):
        ui.load_contract(tmp_path)
    with pytest.raises(ui.ReviewDataError):
        ui.read_rows(OUT, "../unapproved.parquet", "2020Q2", [1])
    if (OUT / RAW_FILE).is_file():
        assert ui.read_rows(OUT, RAW_FILE, "2020Q2", [], columns=RAW_COLUMNS).empty


def test_protected_read_dependencies_match_before_hashes():
    manifest = os.environ.get("M12_PRESERVATION_MANIFEST")
    if not manifest:
        pytest.skip("Source preservation manifest is local-only and not supplied.")
    record = json.loads(Path(manifest).read_text(encoding="utf-8-sig"))
    assert record["protected_file_count"] == len(record["protected_files"])
    for item in record["protected_files"]:
        path = Path(item["path"])
        assert path.stat().st_size == item["bytes"], str(path)
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        assert digest == item["sha256"], str(path)


def test_review_source_does_not_import_model_training_or_inference_modules():
    for path in (APP, ROOT / "dashboard" / "m12_review_ui_helpers.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(alias.name.split(".")[0] in {"shap", "sklearn", "joblib"} for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith(("shap", "sklearn", "joblib", "src.historical_m12_fit"))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"fit", "predict", "predict_proba", "shap_values"}


class SessionState(dict):
    """Minimal synthetic state for testing the actual pure UI callback bodies."""

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def callbacks(state):
    names = {"change_cohort", "change_view", "navigate", "change_filter", "select_table", "select_chart", "select_company"}
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    functions = ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names], type_ignores=[])
    namespace = {"st": SimpleNamespace(session_state=state), "h": ui}
    exec(compile(functions, str(APP), "exec"), namespace)
    assert names.issubset(namespace)
    return namespace


@pytest.mark.parametrize("group", ["Scale", "Non-scale"])
def test_actual_chart_callback_navigates_and_blocks_replay_after_back(predictions, group):
    key = predictions["2020Q2"].row_key.iloc[7]
    state = SessionState(
        review_view="Overview", review_cohort="2020Q2", review_epoch=4,
        review_selection=predictions["2020Q2"].row_key.iloc[0], review_focus=None,
        review_processed_event=None, review_filters={"query": "", "mode": "Top 15", "page": 1},
        chart={"selection": {"open_company": [{"row_key": key, "calendar_quarter": "2020Q2", "group": group}]}},
    )
    functions = callbacks(state)
    functions["select_chart"]("chart", "2020Q2", predictions["2020Q2"].row_key.tolist(), 4)
    assert (state.review_view, state.review_selection, state.review_focus) == ("Business View", key, group)
    assert state.review_cohort == "2020Q2"
    functions["navigate"]("Overview")
    epoch = state.review_epoch
    functions["select_chart"]("chart", "2020Q2", [key], 4)
    assert state.review_view == "Overview" and state.review_epoch == epoch
    assert state.review_selection == key
    functions["select_chart"]("chart", "2020Q2", [key], epoch)
    assert state.review_view == "Business View" and state.review_selection == key


def test_actual_table_action_and_cohort_callback_preserve_or_reset_correct_state(predictions):
    key = predictions["2020Q2"].row_key.iloc[12]
    state = SessionState(
        review_view="Overview", review_cohort="2020Q2", review_epoch=0,
        review_selection=None, review_focus="Scale", review_processed_event=None,
        review_filters={"query": "RAMBUS", "mode": "Full list", "page": 2},
        table={"selection": {"rows": [1]}},
    )
    functions = callbacks(state)
    functions["select_table"]("table", [predictions["2020Q2"].row_key.iloc[0], key])
    assert state.review_selection == key and state.review_focus is None
    assert state.review_view == "Overview"
    functions["navigate"]("Business View")
    functions["navigate"]("Overview")
    assert state.review_selection == key
    assert state.review_filters == {"query": "RAMBUS", "mode": "Full list", "page": 2}
    state.review_cohort = "2018Q4"
    functions["change_cohort"]()
    assert state.review_selection is None and state.review_focus is None
    assert state.review_filters == {"query": "", "mode": "Top 15", "page": 1}
    assert state.review_processed_event is None


def app_test():
    from streamlit.testing.v1 import AppTest

    if missing_private_files():
        pytest.skip("Full UI requires authorized local-only artifacts; code-only startup is tested separately.")
    return AppTest.from_file(ROOT / "app.py", default_timeout=60).run()


def assert_app_clean(app):
    assert not app.exception, [value.message for value in app.exception]
    assert not app.error, [value.value for value in app.error]


def test_apptest_cold_start_navigation_defaults_and_outcomes_off():
    app = app_test()
    assert_app_clean(app)
    assert app.session_state["review_view"] == "Overview"
    assert app.selectbox(key="review_cohort").value == "2020Q2"
    assert app.toggle(key="show_outcomes").value is False
    assert [tab.label for tab in app.tabs] == [
        "Overview", "Business View", "Beyond Size & Robustness", "Company Comparison",
        "Historical Population & M0", "Dictionary & Scientific Audit",
    ]
    assert len(app.sidebar) == 0
    assert app.dataframe[0].value["Rank"].tolist() == list(range(1, 16))
    assert "issuer_label" not in app.dataframe[0].value.columns
    assert any("Timing and label-coverage validation remain under review" in value.value for value in app.caption)
    assert not any(metric.label == "Percentile" for metric in app.metric)


def test_apptest_search_open_company_rank_dates_selector_and_back(predictions):
    app = app_test()
    expected = predictions["2020Q2"].loc[predictions["2020Q2"]["rank"].eq(451)].iloc[0]
    app.text_input(key="filter_query").input(str(expected.conm)).run()
    assert_app_clean(app)
    assert 451 in app.dataframe[0].value["Rank"].tolist()
    # AppTest lacks browser dataframe/chart selection. Set only the authoritative
    # identity here; actual row and segment clicks belong to the browser QA.
    app.session_state["review_selection"] = expected.row_key
    app.run()
    next(button for button in app.button if button.label == "Open company details").click().run()
    assert_app_clean(app)
    assert app.session_state["review_view"] == "Business View"
    assert app.selectbox(key="company_picker").value == expected.row_key
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Rank"] == "451 / 11,769"
    assert metrics["Ranking score (uncalibrated)"] == f"{expected.ensemble_uncalibrated_score:.6f}"
    assert metrics["Information available"] == str(pd.Timestamp(expected.information_available_date).date())
    assert "Percentile" not in metrics
    assert any(value.value == "Top 3.83%" for value in app.caption)
    assert any(value.value == str(expected.conm) for value in app.subheader)
    assert not any("Stored individual ex-post label:" in value.value for value in app.caption)
    next(button for button in app.button if button.label == "Back to Overview").click().run()
    assert_app_clean(app)
    assert app.session_state["review_view"] == "Overview"
    assert app.session_state["review_selection"] == expected.row_key
    assert app.text_input(key="filter_query").value == str(expected.conm)


def test_apptest_full_list_page_search_empty_and_cohort_reset(predictions):
    app = app_test()
    app.selectbox(key="filter_mode").set_value("Full list").run()
    app.number_input(key="filter_page").set_value(2).run()
    assert_app_clean(app)
    assert app.dataframe[0].value["Rank"].tolist() == list(range(26, 51))
    app.text_input(key="filter_query").input("no-such-issuer-__987654321__").run()
    assert_app_clean(app)
    assert any("No matching companies" in value.value for value in app.info)
    assert not any(button.label == "Open company details" for button in app.button)
    assert len(app.dataframe) == 0
    app.selectbox(key="review_cohort").set_value("2019Q2").run()
    assert_app_clean(app)
    assert app.session_state["review_selection"] == predictions["2019Q2"].row_key.iloc[0]
    assert app.text_input(key="filter_query").value == ""
    assert app.selectbox(key="filter_mode").value == "Top 15"
    assert app.dataframe[0].value["Rank"].tolist() == list(range(1, 16))


def test_apptest_business_searchable_picker_updates_identity_and_metrics(predictions):
    app = app_test()
    next(button for button in app.button if button.label == "Open company details").click().run()
    expected = predictions["2020Q2"].iloc[70]
    app.selectbox(key="company_picker").set_value(expected.row_key).run()
    assert_app_clean(app)
    assert app.session_state["review_selection"] == expected.row_key
    assert app.selectbox(key="company_picker").value == expected.row_key
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Rank"] == "71 / 11,769"
    assert metrics["Ranking score (uncalibrated)"] == f"{expected.ensemble_uncalibrated_score:.6f}"
    assert any(value.value == str(expected.conm) for value in app.subheader)


def test_apptest_top100_keeps_readable_chart_rows_inside_a_scroll_container():
    app = app_test()
    app.selectbox(key="filter_mode").set_value("Top 100").run()
    assert_app_clean(app)
    assert len(app.dataframe[0].value) == 100
    chart = app.get("vega_lite_chart")[0]
    specification = json.loads(chart.proto.spec)
    assert specification["height"] == 100 * 28 + 120
    chart_containers = [
        block for block in app.get("flex_container")
        if block.proto.height_config.pixel_height == 680
        and len(block.get("vega_lite_chart")) == 1
    ]
    assert len(chart_containers) == 1
    # A fixed Streamlit chart height overrides Vega's row spacing. Only its
    # surrounding scroll container may cap the vertical viewport.
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "altair_chart":
            assert "height" not in {argument.arg for argument in node.keywords}
    diamond = specification["layer"][2]
    tooltip_fields = {item["field"] for item in diamond["encoding"]["tooltip"]}
    assert "total_net" in tooltip_fields
    assert not {"group", "contribution"} & tooltip_fields


def test_apptest_all_six_destinations_render_without_runtime_errors():
    app = app_test()
    for view in ["Business View", "Beyond Size & Robustness", "Company Comparison", "Historical Population & M0", "Dictionary & Scientific Audit", "Overview"]:
        app.session_state["review_view"] = view
        app.run()
        assert_app_clean(app)
        assert app.session_state["review_view"] == view
        assert app.toggle(key="show_outcomes").value is False
