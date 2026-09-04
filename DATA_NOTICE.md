# Data notice

## Shareability decision

The source project states that licensed, proprietary, credential-bearing, and large datasets must remain out of Git and that only code, documentation, schemas, and small non-sensitive summaries belong in version control. Private repository visibility does not establish redistribution rights.

Accordingly, this repository includes only:

1. original dashboard code and documentation;
2. small aggregate model-selection, evaluation, robustness, and profile summaries;
3. feature/theme/Scale display contracts and QA summaries; and
4. one approved static dashboard preview.

It excludes raw or near-raw licensed data and issuer-level derived vendor data for which sharing rights remain uncertain. No replacement scientific evidence was fabricated.

## Required local-only files

Place every file below in `data/private/` only after an authorized data owner confirms that local use is permitted. Git ignores this directory.

For temporary authorized testing, `M12_PRIVATE_DATA_DIR` may point to a separate directory containing the same files. The default remains the repository-local ignored directory.

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

The application verifies only file presence. Before review, compare the supplied files with the hashes above.

## Explicitly prohibited from this repository

- Any M12 audit ZIP, model artifact, checkpoint, canonical feature panel, training dataset, full prediction/SHAP archive, or full source provenance.
- Raw Compustat, WRDS, CRSP, DMA, FactSet, or Pandects extracts.
- M0–M11 outputs except the single local-only M0 forensic dependency listed above.
- Credentials, tokens, cookies, browser profiles, `.env`, or `.streamlit/secrets.toml`.

Until the nine local-only files are separately authorized and supplied, the remote repository is code-only and the interactive dashboard is not fully reproducible from Git alone.
