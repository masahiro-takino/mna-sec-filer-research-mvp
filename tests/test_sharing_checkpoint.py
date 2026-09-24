"""Code-only packaging checks; synthetic failures never stand in for research data."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from dashboard import sharing_paths

ROOT = Path(__file__).resolve().parents[1]


def test_documented_entry_point_starts_safely_without_private_data(tmp_path, monkeypatch):
    monkeypatch.setattr(sharing_paths, "PRIVATE_DATA", tmp_path)
    monkeypatch.setattr(sharing_paths, "M0_PATH", tmp_path / sharing_paths.M0_FILE)
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    assert not app.exception and not app.error
    assert any("Code-only checkpoint" in item.value for item in app.warning)
    assert any("Timing and label-coverage" in item.value for item in app.caption)
    assert set(sharing_paths.PRIVATE_RUNTIME_FILES).issubset(set(app.code[0].value.splitlines()))
    assert not app.dataframe and not app.get("vega_lite_chart")
    assert not app.tabs


def test_private_contracts_and_issuer_data_are_never_public_routes():
    for name in sharing_paths.PRIVATE_RUNTIME_FILES:
        assert sharing_paths.artifact_path(name).parent != sharing_paths.PUBLIC_DATA
        assert not (sharing_paths.PUBLIC_DATA / name).exists()
    assert sharing_paths.artifact_path("historical_M12_feature_concept_theme_scale_contract.csv").parent == sharing_paths.PUBLIC_DATA


@pytest.mark.parametrize("name", ["../outside.csv", "nested/file.csv", "nested\\file.csv"])
def test_artifact_names_cannot_traverse_directories(name):
    with pytest.raises(ValueError):
        sharing_paths.artifact_path(name)


def test_entry_point_only_executes_the_review_ui():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert '"historical_m12_review_ui.py"' in source
    assert "runpy.run_path" in source
    assert "historical_m12_prototype" not in source
