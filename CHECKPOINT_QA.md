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

## Sanitized screenshot gallery — September 30, 2026

This presentation-only follow-up begins at clean local/remote `main` commit `0461854ebe783932c8f7924fd2dedf1db7b1be73` in the independently verified PRIVATE repository. The earlier code-checkpoint evidence above is retained; its prior counts are not substituted for fresh tests.

The unchanged source `dashboard/historical_m12_review_ui.py` was launched on loopback only with telemetry disabled and the dark theme. All six required destinations were observed in the current reviewed navigation, not the old prototype. An isolated local capture adapter executes that unchanged source and intercepts display arguments only: it replaces restricted cells/text and the entire issuer-SHAP visualization before rendering, disables capture-view downloads, and adds an explicit sanitization banner. The actual application, data, model state, scientific claims and sharing-copy runtime code are unchanged. The capture adapter and local evidence logs are not Git content.

Viewport: 1600 x 1200; coherent application-only crop: 1520 x 1105. Each image is a bounded viewport, not an extremely tall full-page export. Browser chrome and the app toolbar are outside the crop. The browser's JPEG captures are converted to PNG without rescaling or pixel alteration; PNG metadata is omitted. Six final PNGs were opened and visually inspected individually. All use outcomes OFF and visible historical-validation caveats.

| Image | Disclosure review |
|---|---|
| `01_overview.png` | Table headers and workflow retained; all issuer cells, selection identity/rank and SHAP geometry withheld. |
| `02_business_view.png` | Rank/Top X%, score and date/window field labels retained; identities, numbers, ranked driver concepts/values and all SHAP geometry withheld. |
| `03_beyond_size_robustness.png` | Already-included aggregate comparator evidence retained with explicit historical caveat; no issuer data. |
| `04_company_comparison.png` | Public feature definitions/units retained; selected identities, company headers/cells and date/rank metadata withheld. |
| `05_historical_population.png` | Already-included aggregate historical findings retained; private M0/SPX table omitted. |
| `06_dictionary_scientific_audit.png` | Public target/dictionary and qualified saved statuses retained; local path hidden, issuer audit contents unexposed. |

Fresh unchanged sharing-repository tests: **17 passed / 42 skipped** without private data; **58 passed / 1 skipped** with authorized local saved artifacts; zero failures/errors in either run. The preservation-manifest test is skipped because one historical external prompt is now absent; no replacement manifest or weakened test was supplied. Independent before/after checks confirmed all 38 available historical/source referents and seven sharing code/test/old-preview files remained byte-identical. The unavailable external prompt prevents claiming all 39 prior referents were verified. Detailed command/stdout/stderr/JUnit and preservation records remain local.

Publication review checks only the explicit six PNGs and four documentation/manifest files. It excludes private directories, raw/vendor files, binaries, archives, notebook output, credentials, absolute local paths and files over 25 MB. The manifest retains all excluded dependency records and the self-referential exception, using normalized text bytes and exact PNG bytes. README uses relative image links with full-resolution click-through; the older approved preview remains tracked and unchanged. GitHub privacy and remote-main checks must be repeated before and after the normal non-force push.

No training, inference, new SHAP, WRDS, acquisition, research-data mutation, deployment or scientific-validation change is part of this gallery. Streamlit guidance informed the loopback/theme setup; browser/computer-use guidance informed viewport capture and visual review. This is a sanitized presentation checkpoint, not a full-data backup or scientific approval.

## Informative presentation upgrade — September 30, 2026

This follow-up began at clean local/remote `main` commit `ebfb7991a27a16034f3651cb9fa1509e49d9687e` after independent PRIVATE-visibility verification. The earlier gallery and test descriptions above are historical records, not descriptions of the replacement PNGs or new test runs. The new explicit authorization permits bounded screenshots of actual stored company identities, ranks, percentiles, uncalibrated scores, timing fields and SHAP explanations. It does not permit raw financial/model-input values or full issuer-level files. DATA_NOTICE documents the revised narrow boundary.

The unchanged source review entry point was launched on loopback with telemetry disabled. All six destinations were verified. A new local-only presentation adapter executes the source without editing it, removes raw financial input columns before display, restricts Comparison to actual saved SHAP, suppresses explicit output downloads, omits source-linked M0/reconciliation tables and local paths, and retains authorized real rankings and contribution geometry. It shortens table/chart viewport framing only; it does not change scores, ranks, feature values, SHAP values or scientific conclusions. Internal row keys and unnecessary numerical baseline/provenance are not shown. The adapter, tests and logs are not published.

| Final PNG | Displayed | Withheld |
|---|---|---|
| `01_overview.png` | Actual Top-15 issuer names/tickers, ranks, inclusive Top X%, scores and signed Scale/Non-scale bars | Raw financial inputs, complete issuer export and internal identifiers |
| `02_business_view.png` | Actual rank-1 Rambus identity, score, rank, information date/window, signed subtotals, five stored driver names and SHAP values | Raw-value column, fitted baseline/provenance, internal row key and output downloads |
| `03_beyond_size_robustness.png` | Existing all-three-cohort candidate/scale-only/non-size/missingness metrics and seed-stability summary | New calculations or scientific certification |
| `04_company_comparison.png` | First four stored ranked companies, actual signed feature SHAP, original ranks/percentiles and dates | Raw economic values, imputed model inputs, technical feature columns and full comparison export |
| `05_historical_population.png` | Existing aggregate descriptive findings with historical caveat | M0/SPX issuer financial source-value table |
| `06_dictionary_scientific_audit.png` | Public dictionary context, target and qualified saved checks | Local paths and full issuer reconciliation/output files |

All six final PNGs were opened and visually reviewed individually. They use a consistent 1600 x 1200 desktop viewport, a 1520 x 1105 application-only crop, dark theme and individual outcomes OFF. Conversion from browser JPEG to PNG preserves decoded pixels without rescaling and writes no image metadata. Some lower or horizontally wide table content lies outside the bounded capture; README provides full-resolution links. PNG files are under 0.8 MB each. The older approved preview remains unchanged.

Fresh local adapter tests: **17 passed; zero failures, errors or skips**. This includes real saved Top-15 SHAP preservation, removal of raw/model input fields, all six Streamlit AppTest views, SHAP-only Comparison, selected-company identity/rank/score/date agreement, disabled outcomes and absent explicit output-download elements. Tests execute no model and compute no new SHAP. The earlier 17/42 and 58/1 sharing-suite results remain separately dated evidence; they were not rerun or claimed as new results in this presentation-only update. All 38 available protected source referents remain byte-identical before/after; one missing historical external prompt is explicitly unverified.

Fresh browser review confirmed the Overview-to-Business-View button retained rank-1 Rambus and its stored score/date/SHAP totals. Every view was inspected with the correct active tab before capture. Browser logs recorded transient Vega infinite-extent warnings during chart initialization/reloads; final charts rendered finite signed axes and the expected saved bars. No browser errors were observed. This is not a claim of warning-free startup or new scientific validation.

README now explains the target, score interpretation, SHAP units, data sources, collaborative attribution and limitations. Its three-cohort evidence table transcribes the existing aggregate CSV, including zero 2020Q2 Top-15 positives and the 2018Q4 Top-50 tie with scale-only. It does not merge legacy Top-10 results with M12Q or certify the saved cohort as U.S.-listed-only.

Only the six replacement PNGs and four documentation/manifest files are in the explicit publication plan. Manifest hashes follow the existing LF-normalized-text/binary-exact convention, preserve excluded dependencies unchanged and retain the self-hash exception. Publication requires staged-diff review, PRIVATE rechecks, a normal non-force push and independent remote-SHA/image/README verification. No application code, dependency pins, private data, model binaries, archives, notebook output, credentials or real local paths are included in this update. Streamlit guidance informed pre-render column removal; computer-use guidance informed consistent capture and visual verification.
