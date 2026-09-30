# Data notice

## Shareability decision

The source project states that licensed, proprietary, credential-bearing, and large datasets must remain out of Git and that only code, documentation, schemas, and small non-sensitive summaries belong in version control. Private repository visibility does not establish redistribution rights.

Accordingly, this repository includes only:

1. reviewed dashboard code, presentation-layer tests, and documentation;
2. small aggregate model-selection, evaluation, robustness, and profile summaries;
3. feature/theme/Scale display contracts and QA summaries;
4. one previously approved static dashboard preview; and
5. six explicitly reviewed, presentation-safe captures under `assets/screenshots/`, subject to the narrow, screenshot-specific boundary below.

It excludes raw or near-raw licensed data and full issuer-level derived output files for which sharing rights remain uncertain. The authorized presentation exception allows selected model-derived values in flattened screenshots, not the underlying files or raw financial values. No replacement scientific evidence was fabricated.

Financial data source: Compustat North America via WRDS. Event data comes from the project's licensed/authorized historical sources. Displayed model rankings and SHAP analyses are author-generated research outputs. Naming a source does not extend the source-data license or establish unlimited redistribution rights.

## Required local-only files

Place required files below in `data/private/` only after an authorized data owner confirms that local use is permitted. Git ignores this directory. Ten files are required by the current review UI; the previously listed theme-SHAP dependency remains excluded but is no longer read by this UI.

For temporary authorized testing, `M12_PRIVATE_DATA_DIR` may point to a separate directory containing the same files. The default remains the repository-local ignored directory.

`M12_M0_FORENSIC_PATH` can point to the exact separately authorized M0 CSV without copying it into the M12 directory. There is no source-directory auto-discovery. Public summaries and the dictionary are always read from `data/public/`.

| File | Bytes | SHA-256 | Classification and reason excluded |
|---|---:|---|---|
| `historical_M12_ensemble_predictions.parquet` | 11,179,766 | `324f2b9a508252bb9e2c429e2da02c1f68757f884abb8122efc86b3d847f16ba` | Issuer-level derived model output; redistribution rights uncertain. |
| `historical_M12_all_evaluation_raw_shap.parquet` | 23,668,437 | `0ef8beaed4a406569f053a5ef3bbfea40ed298c896253b9044d1c82ddd4fd2ee` | Issuer-feature-level derived vendor data and SHAP; rights uncertain. |
| `historical_M12_all_evaluation_theme_shap.parquet` | 14,976,545 | `184b99c8a2424e5cf4ec15c6ac8780dd4514dbe5df924392b5b231503eb5ef2d` | Issuer-theme-level derived model output; rights uncertain. |
| `historical_M12_inline_remainder_rows.parquet` | 40,088,087 | `8996b372694a47d9eb1aa0993890ab472652ba506bd46a344dea918d6484d497` | Issuer-feature-level derived vendor data; also exceeds 25 MB. |
| `historical_M12_top_visible_raw_drivers.parquet` | 9,949,511 | `ee7055fccb37b494bcc685d4786c3f301292afe1dc60050a77c496f8b3a74fb5` | Issuer-feature-level values and SHAP; rights uncertain. |
| `historical_M12_2020Q2_top15_comparison_long.csv` | 281,382 | `d6994e5f6fcf2a3333377e34205263f65a6ecaca9095471593a506bcac7f5c8b` | Named issuer raw/model values and SHAP; rights uncertain. |
| `historical_M12_named_company_rank_and_shap_audit.csv` | 5,102 | `c5461239bca13980b2e82601c66dab0fd905c6b27afe1d687e61cb7073d55cce` | Named issuer ranks and SHAP; rights uncertain. |
| `historical_M12_label_conflict_reconciliation.csv` | 10,555 | `04ee73dc7b396e7ca1128404920d0cc11eb627bdc7425f6f7d7f942f0858c639` | Issuer/event-window reconciliation; rights uncertain. |
| `historical_M11_M0_SPX_75_feature_forensic.csv` | 85,140 | `a48bb88aeab012e1298eaf4c624b86963731b1028dcb6e4351d23c25476c4022` | Named issuer near-raw Compustat values; licensed-data risk. |

Two additional files are required locally, but are not copied to Git:

- `historical_M12_preregistration_contract.json`: exact selected ordered-feature contract. The complete research contract remains local rather than republishing unrelated provenance or workflow metadata.
- `historical_M12_selected_ensemble_model_manifest.json`: exact saved five-seed baseline and ordered-feature hash. It contains fitted numerical baselines and model provenance; no restricted values are copied into code or public data.

Their sizes and SHA-256 hashes are recorded as excluded dependencies in `MANIFEST.csv`. No model binary is required. The old theme-SHAP Parquet remains excluded and is optional/unused by the revised UI.

The application checks required file presence, then validates selected-candidate identity, cohort, ordered-feature hash, exact seed membership, dictionary scale membership, and saved SHAP/score reconciliation. Before review, compare supplied file bytes with the dependency hashes. Missing files produce a code-only notice; malformed or incompatible artifacts fail closed without fallback calculations.

## Explicitly prohibited from this repository

- Any M12 audit ZIP, model artifact, checkpoint, canonical feature panel, training dataset, full prediction/SHAP archive, or full source provenance.
- Raw Compustat, WRDS, CRSP, DMA, FactSet, or Pandects extracts.
- M0–M11 outputs except the single local-only M0 forensic dependency listed above.
- Credentials, tokens, cookies, browser profiles, `.env`, or `.streamlit/secrets.toml`.

Until the ten current local-only dependencies are separately authorized and supplied, the interactive dashboard is not fully reproducible from Git alone. Runtime tables, downloadable issuer-level outputs and screenshots outside the specific reviewed exception below remain local. Private visibility is not general permission to upload data or derived outputs.

## Narrow screenshot-gallery disclosure boundary

The six gallery PNGs were revised under the September 30, 2026 presentation authorization. That authorization permits selected existing company identities and model-derived outputs to make the research workflow legible. It supersedes the earlier gallery's broader visual masking for these six captures only. It does not authorize new science, redistribution of full issuer-level files, or disclosure of reconstructable licensed source data.

| View | Permitted presentation content | Content withheld |
|---|---|---|
| Overview | Actual saved company names/tickers, original ranks, percentile/Top X%, uncalibrated score, and signed Scale/Non-scale SHAP contributions | Raw financial/model-input values, complete downloadable issuer tables and local paths |
| Business View | Actual selected-company identity, rank, percentile, score, information date/forecast window, driver names and signed SHAP contribution | Raw and imputed financial values, reconstructable source-value tables and downloads |
| Beyond Size & Robustness | Existing aggregate candidate/comparator metrics, missingness/frequency diagnostics and seed stability, with caveats | Any raw issuer-level model inputs or full output files |
| Company Comparison | Selected actual names, rankings, timing and comparable derived model/SHAP outputs | Raw financial/model-input values and complete issuer-level comparison files |
| Historical Population & M0 | Existing descriptive aggregate findings, explicitly separated from live prediction validation | Protected M0/SPX raw issuer financial values and downloadable forensic tables |
| Dictionary & Scientific Audit | Already-approved feature definitions/mnemonics, target text, contract structure and qualified saved-check statuses | Local evidence paths, raw financial values and complete reconciliation/output files |

Raw vendor financial values must not appear in any gallery image. Raw vendor field names are restricted to the already-approved feature dictionary context; company driver views use descriptive names rather than exposing source tables. The display adapter suppresses downloads and raw/imputed model-input columns before capture, and only a bounded selection of existing model-derived outputs is displayed. Individual ex-post outcomes remain OFF. No synthetic company predictions, financial values, replacement SHAP bars or scientific evidence are fabricated.

This is a screenshot-only display transformation. The reviewed application, stored research results and code-only entry point are unchanged. Only flattened raster captures are included, with no private source tables, browser state, local adapter, DOM dumps, credentials or image metadata. The prior approved `assets/dashboard_preview.png` is retained unchanged and grants no broader display permission. Reuse outside this private research-review repository requires its own authorization.

## Historical evidence is not scientific approval

Existing aggregate files are preserved historical snapshots. Later evidence-closure review withdrew unqualified leakage-safe and GS-ready claims because timing, label maturity, and negative-label coverage remain unresolved. Numerical reconciliation and UI tests do not resolve those issues. This code checkpoint grants no new scientific approval or sharing authorization.
