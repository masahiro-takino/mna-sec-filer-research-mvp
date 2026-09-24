# Reviewed dashboard code checkpoint

## Scope

The documented `app.py` entry point now routes to the isolated Overview-first M12 review UI. Sharing-copy adaptations are limited to imports, public/private paths, missing-data startup, test dependency handling, and documentation. Reviewed feature ordering, selection callbacks, signed SHAP arithmetic, original ranks, and model outputs are unchanged. Streamlit's installed-version guidance informed the entry-point and state compatibility checks.

No model was trained, calibrated, loaded, or executed. No new predictions, SHAP values, features, or labels were generated. No private artifacts were copied into this repository. Existing aggregate public files and the previously approved preview remain unchanged. The original `SANITIZATION_QA.md` and `SOURCE_REPOSITORY_STATE.md` are retained as records of the earlier snapshot; this document describes the new checkpoint.

## Test results

Test runtime: Python 3.12.13; Streamlit 1.59.1; Altair 6.2.2; pandas 3.0.5; NumPy 2.5.2; PyArrow 25.0.1; SciPy 1.18.0; pytest 9.1.1. The existing local environment was reused without installation or modification. This run did not create a fresh virtual environment.

| Scope | Result | Meaning |
|---|---|---|
| Sharing-copy tests without private artifacts | 17 passed; 42 skipped; zero failures/errors | 41 tests require authorized data; one requires the local preservation manifest. Skips are not counted as passes. |
| Same suite with authorized local read-only dependencies and preservation manifest | 59 passed; zero skips/failures/errors | All copied review tests plus code-only/path-routing checks passed through the sharing entry point. |
| Fresh browser, authorized local data | 162 strict-boolean checks passed | Real Scale/Non-scale segment clicks, sorted-table identity, repeat click/Back, search, full-list last page, cohort changes, all six views, original ranks, dates, scores, and signed subtotals. |
| Fresh browser, no private data | Five strict-boolean checks passed | Missing-data notice, historical caveat, missing manifest disclosure, no fabricated table/chart, and no browser errors. |

The full data suite checked all 34,668 stored selected-candidate prediction rows and 1,248,048 corresponding saved raw-SHAP rows using bounded reads. Reconciliation uses the exact saved five-seed mean baseline and absolute tolerance 1e-10, not a new model run. AppTest covers navigation/state; actual chart-click acceptance used installed Microsoft Edge through Playwright at 1440 x 900 and 1366 x 768.

Both browser runs reported no console or page errors. Their temporary localhost servers returned healthy responses and were stopped after testing. No unrelated server was stopped. No new screenshots were generated or uploaded. Detailed logs, JUnit results, browser checks and preservation evidence remain in a temporary local QA directory outside both repositories; data-bearing browser evidence is not Git content.

An initial sandboxed test attempt could not access pytest's temporary directory. The same tests succeeded under the authorized host account; this was an environment permission issue, not an application failure.

## Preservation and publication checks

- Thirty-nine scoped source hashes were verified against the prior reviewed checkpoint: 36 protected read dependencies plus the three reviewed UI/helper/test files. All remain unchanged after testing. This is not a whole-source-tree hash claim.
- The sharing branch began clean at `94b4708fe0214bb19a6d3f462d8ec5219609ea94`, matching remote `main`.
- The expected existing GitHub repository was independently verified PRIVATE. Publication requires a second private-visibility check immediately before push and remote-SHA verification afterwards.
- Only explicitly reviewed code, tests, requirements, documentation, `.gitignore`, and `MANIFEST.csv` are staged. The tracked inventory separates included files from eleven excluded dependencies, of which ten are currently required by the review UI.
- Staged-content review excludes private data, model binaries, raw/vendor data, notebook outputs, archives, new screenshots, credentials, and files exceeding 25 MB. Git ignore rules are defense in depth, not the acceptance test.
- The full preregistration and saved baseline/model manifest remain local-only. Their file identities/hashes are recorded, but their fitted values and provenance are not republished.

## Limits

This is a code checkpoint, not a complete data backup or scientific approval. Timing, historical vintage, label maturity and negative-label coverage remain unresolved; scores are uncalibrated. Existing public aggregate files preserve historical diagnostics rather than certifying current validity. Runtime authorization is distinct from redistribution permission, including for a private GitHub repository.

Interactive use still requires the ten authorized local dependencies in `DATA_NOTICE.md`. Without them the app deliberately displays only the code-only notice. Tests are specific to the installed Windows/Edge environment; no deployment or cross-platform certification is claimed. A broad query in the native virtualized company picker may retain its scroll position; an exact company search narrows the list.
