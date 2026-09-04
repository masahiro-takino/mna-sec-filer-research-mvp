# Sanitization and smoke-test QA

## Packaging checks

- Runtime dependency trace starts from `app.py` and covers all 24 data reads from the accepted M12 source dashboard.
- Fifteen small aggregate/contract/QA dependencies are included under `data/public/`.
- Nine issuer-level or near-raw dependencies are excluded and listed with exact sizes and SHA-256 hashes in `DATA_NOTICE.md` and `MANIFEST.csv`.
- No ZIP, model, checkpoint, canonical feature panel, training data, source provenance, raw extract, credential, browser profile, environment file, secret file, or cache is included.
- Static scans found no personal filesystem path, email address, private-key marker, API-key assignment, token assignment, or source-repository runtime backreference.
- Every trackable file is represented in `MANIFEST.csv`; the manifest’s self-row explains why a self-hash cannot be embedded.
- No trackable file exceeds 25 MB.

## Fresh-environment smoke test

The test used a new Python 3.12.13 virtual environment outside both repositories. Only `requirements.txt` was installed.

Verified versions: Streamlit 1.59.1, pandas 3.0.5, NumPy 2.5.2, and PyArrow 25.0.1.

Code-only mode:

- Streamlit health endpoint returned HTTP 200 / `ok`.
- The sanitized data-safety notice, clean preview, and exact missing-file list rendered.
- No Python traceback or browser-console error occurred.

Temporary authorized-data mode:

- Streamlit health endpoint returned HTTP 200 / `ok`.
- The default 2020Q2 Business View rendered for SPX Technologies.
- Company switching to Rambus updated rank, score, issuer explanation, Scale/Non-scale chart, and driver values.
- The positive contribution/remainder section rendered.
- The negative contribution/remainder section rendered.
- No Python traceback or browser-console error occurred.
- The nine temporary issuer-level copies were deleted after the test and never added to the repository.

## Reproducibility outcome

The Git-safe repository is intentionally code-only. It launches successfully from Git alone but requires separately authorized local-only data to reproduce the interactive scientific dashboard.
