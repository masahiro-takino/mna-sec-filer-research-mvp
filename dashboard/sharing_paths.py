"""Explicit public/private routing; never discover or download research data."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DATA = ROOT / "data" / "public"
PRIVATE_DATA = Path(os.environ.get("M12_PRIVATE_DATA_DIR", ROOT / "data" / "private")).resolve()
M0_FILE = "historical_M11_M0_SPX_75_feature_forensic.csv"
M0_PATH = Path(os.environ.get("M12_M0_FORENSIC_PATH", PRIVATE_DATA / M0_FILE)).resolve()

# The two complete contracts stay local: the manifest contains fitted baselines
# and model provenance. No values are inferred or substituted when absent.
PRIVATE_RUNTIME_FILES = (
    "historical_M12_ensemble_predictions.parquet",
    "historical_M12_all_evaluation_raw_shap.parquet",
    "historical_M12_inline_remainder_rows.parquet",
    "historical_M12_top_visible_raw_drivers.parquet",
    "historical_M12_2020Q2_top15_comparison_long.csv",
    "historical_M12_named_company_rank_and_shap_audit.csv",
    "historical_M12_label_conflict_reconciliation.csv",
    "historical_M12_preregistration_contract.json",
    "historical_M12_selected_ensemble_model_manifest.json",
    M0_FILE,
)


def artifact_path(filename):
    """Resolve private names first; only already tracked summaries are public."""
    if filename != Path(filename).name:
        raise ValueError("Artifact names must not contain directory components.")
    if filename == M0_FILE:
        return M0_PATH
    if filename in PRIVATE_RUNTIME_FILES:
        return PRIVATE_DATA / filename
    return PUBLIC_DATA / filename


def missing_private_files():
    return [name for name in PRIVATE_RUNTIME_FILES if not artifact_path(name).is_file()]
