"""Documented sharing entry point for the isolated Overview-first review UI."""

from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
runpy.run_path(str(ROOT / "dashboard" / "historical_m12_review_ui.py"), run_name="__main__")
