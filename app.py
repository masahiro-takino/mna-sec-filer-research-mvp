"""M12 historical SEC Filer research dashboard for GS feedback."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
PUBLIC_DATA = ROOT / "data" / "public"
PRIVATE_DATA = Path(os.environ.get("M12_PRIVATE_DATA_DIR", ROOT / "data" / "private")).resolve()
SELECTED = "M12Q_quarterly_only_full_population_median"

PRIVATE_RUNTIME_FILES = [
    "historical_M12_ensemble_predictions.parquet",
    "historical_M12_all_evaluation_raw_shap.parquet",
    "historical_M12_all_evaluation_theme_shap.parquet",
    "historical_M12_inline_remainder_rows.parquet",
    "historical_M12_top_visible_raw_drivers.parquet",
    "historical_M12_2020Q2_top15_comparison_long.csv",
    "historical_M12_named_company_rank_and_shap_audit.csv",
    "historical_M12_label_conflict_reconciliation.csv",
    "historical_M11_M0_SPX_75_feature_forensic.csv",
]

st.set_page_config(page_title="M12 SEC Filer Research", page_icon="◇", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
.block-container {padding-top: .8rem; padding-bottom: 2rem; max-width: 1540px;}
h1 {font-size: 1.75rem !important; margin-bottom: .15rem !important;}
h2 {font-size: 1.25rem !important; margin-top: .5rem !important;}
h3 {font-size: 1.05rem !important;}
[data-baseweb="tab-list"] {gap: .25rem; overflow: visible;}
[data-baseweb="tab"] {height: 2.5rem; padding: 0 .72rem; white-space: nowrap; font-size: .86rem;}
[data-testid="stMetric"] {background: #f5f7fa; border: 1px solid #e2e7ef; border-radius: .5rem; padding: .55rem .7rem;}
[data-testid="stMetricValue"] {font-size: 1.35rem;}
[data-testid="stMetric"] * {color: #132238 !important;}
.m12-hero {border: 1px solid #d8e0eb; border-left: 5px solid #17365d; border-radius: .55rem; padding: .65rem .85rem; background: #f8fafc; margin-bottom: .55rem;}
.m12-kicker {font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; color: #526277; font-weight: 700;}
.m12-title {font-size: 1.03rem; font-weight: 700; color: #132238; margin: .15rem 0;}
.m12-note {font-size: .86rem; color: #45556b; line-height: 1.35;}
.signal {border-radius: .45rem; padding: .55rem .7rem; background:#eef4fb; border:1px solid #d2e1f3; font-size:.88rem;}
.warn {border-radius: .45rem; padding: .5rem .7rem; background:#fff8e8; border:1px solid #efdda8; font-size:.84rem;}
.signal, .signal *, .warn, .warn * {color:#132238 !important;}
.smallcap {font-size:.78rem; color:#58697d;}
.profile-card {border:1px solid #3a414b; border-radius:.5rem; padding:.55rem .7rem; margin-bottom:.5rem; min-height:7.2rem;}
.profile-card-title {font-weight:700; font-size:.92rem; margin-bottom:.2rem;}
.profile-card-line {font-size:.79rem; line-height:1.4; color:#c6cbd3;}
div[data-testid="stDataFrame"] {border: 1px solid #e1e6ed;}
</style>
""", unsafe_allow_html=True)


missing_private = [name for name in PRIVATE_RUNTIME_FILES if not (PRIVATE_DATA / name).is_file()]
if missing_private:
    st.title("Historical SEC Filer research MVP")
    st.caption("M12 · sanitized code-only review snapshot")
    st.warning(
        "The dashboard code and aggregate scientific evidence are present, but issuer-level derived vendor data "
        "is intentionally excluded from Git. Add the approved local-only files described in DATA_NOTICE.md to "
        "data/private/ to enable the interactive Business View."
    )
    st.image(ROOT / "assets" / "dashboard_preview.png", caption="Approved static preview of the M12 Business View")
    st.subheader("Why this repository is code-only")
    st.write(
        "Local project policy keeps licensed, proprietary, and issuer-level derived data out of Git. Private "
        "repository visibility does not establish redistribution rights. No substitute scientific data was fabricated."
    )
    st.subheader("Missing local-only runtime files")
    st.code("\n".join(f"data/private/{name}" for name in missing_private), language=None)
    st.stop()


@st.cache_data(show_spinner=False)
def load_data() -> dict[str, object]:
    selection = json.loads((PUBLIC_DATA / "historical_M12_default_model_selection.json").read_text(encoding="utf-8"))
    target = json.loads((PUBLIC_DATA / "historical_M12_target_time_contract.json").read_text(encoding="utf-8"))
    ensemble = pd.read_parquet(PRIVATE_DATA / "historical_M12_ensemble_predictions.parquet")
    ensemble = ensemble[(ensemble.candidate.eq(SELECTED)) & ensemble.diagnostic_kind.eq("candidate")].copy()
    raw = pd.read_parquet(PRIVATE_DATA / "historical_M12_all_evaluation_raw_shap.parquet")
    theme = pd.read_parquet(PRIVATE_DATA / "historical_M12_all_evaluation_theme_shap.parquet")
    remainders = pd.read_parquet(PRIVATE_DATA / "historical_M12_inline_remainder_rows.parquet")
    top = pd.read_parquet(PRIVATE_DATA / "historical_M12_top_visible_raw_drivers.parquet")
    return {
        "selection": selection,
        "target": target,
        "ensemble": ensemble,
        "raw": raw,
        "theme": theme,
        "remainders": remainders,
        "top": top,
        "metrics": pd.read_csv(PUBLIC_DATA / "historical_M12_ensemble_metrics.csv"),
        "seed_aggregates": pd.read_csv(PUBLIC_DATA / "historical_M12_model_metrics_seed_aggregates.csv"),
        "stability": pd.read_csv(PUBLIC_DATA / "historical_M12_rank_stability_summary.csv"),
        "bootstrap": pd.read_csv(PUBLIC_DATA / "historical_M12_paired_bootstrap_comparisons.csv"),
        "stress": pd.read_csv(PUBLIC_DATA / "historical_M12_missingness_and_imputation_stress.csv"),
        "common": pd.read_csv(PUBLIC_DATA / "historical_M12_common_asof_ensemble_metrics.csv"),
        "profile": pd.read_csv(PUBLIC_DATA / "historical_M12_sec_filer_population_findings.csv"),
        "top15": pd.read_csv(PRIVATE_DATA / "historical_M12_2020Q2_top15_comparison_long.csv"),
        "named": pd.read_csv(PRIVATE_DATA / "historical_M12_named_company_rank_and_shap_audit.csv"),
        "dictionary": pd.read_csv(PUBLIC_DATA / "historical_M12_feature_concept_theme_scale_contract.csv"),
        "mapping": pd.read_csv(PUBLIC_DATA / "historical_M12_legacy_20_feature_mapping.csv"),
        "conflicts": pd.read_csv(PRIVATE_DATA / "historical_M12_label_conflict_reconciliation.csv"),
        "gate0": json.loads((PUBLIC_DATA / "historical_M12_gate0_qa.json").read_text(encoding="utf-8")),
        "contract_qa": json.loads((PUBLIC_DATA / "historical_M12_contract_qa.json").read_text(encoding="utf-8")),
        "fit_qa": json.loads((PUBLIC_DATA / "historical_M12_fit_qa.json").read_text(encoding="utf-8")),
        "explain_qa": json.loads((PUBLIC_DATA / "historical_M12_explanation_qa.json").read_text(encoding="utf-8")),
        "m0": pd.read_csv(PRIVATE_DATA / "historical_M11_M0_SPX_75_feature_forensic.csv"),
    }


data = load_data()
ensemble: pd.DataFrame = data["ensemble"]
raw: pd.DataFrame = data["raw"]

st.title("Historical SEC Filer research MVP")
st.caption("M12 · five-seed quarterly-only ensemble · business interpretation with scientific audit")

quarter = st.sidebar.selectbox("Fiscal reporting cohort", ["2020Q2", "2019Q2", "2018Q4"])
show_individual_outcomes = st.sidebar.toggle("Show individual ex-post outcomes", value=False)
quarter_predictions = ensemble[ensemble.calendar_quarter.eq(quarter)].sort_values("rank").copy()
labels = quarter_predictions.apply(lambda row: f"#{int(row['rank']):,} | {row['tic'] if pd.notna(row['tic']) else row['gvkey']} | {row['conm']}", axis=1).tolist()
spx_matches = [i for i, label in enumerate(labels) if "SPX TECHNOLOGIES" in label]
default_index = spx_matches[0] if spx_matches else 0
selected_label = st.sidebar.selectbox("Selected company", labels, index=default_index)
selected = quarter_predictions.iloc[labels.index(selected_label)]
selected_id = int(selected.issuer_quarter_row)
detail = raw[(raw.calendar_quarter.eq(quarter)) & raw.issuer_quarter_row.eq(selected_id)].copy()
theme_detail: pd.DataFrame = data["theme"]
theme_detail = theme_detail[(theme_detail.calendar_quarter.eq(quarter)) & theme_detail.issuer_quarter_row.eq(selected_id)].copy()
top_detail: pd.DataFrame = data["top"]
top_detail = top_detail[(top_detail.calendar_quarter.eq(quarter)) & top_detail.issuer_quarter_row.eq(selected_id)].copy()
remainder_detail: pd.DataFrame = data["remainders"]
remainder_detail = remainder_detail[(remainder_detail.calendar_quarter.eq(quarter)) & remainder_detail.issuer_quarter_row.eq(selected_id)].copy()
scale_net = float(detail.loc[detail.scale_feature.astype(bool), "shap_value"].sum())
non_scale_net = float(detail.loc[~detail.scale_feature.astype(bool), "shap_value"].sum())
top_non_scale = detail[~detail.scale_feature.astype(bool)].sort_values("shap_value", key=lambda values: values.abs(), ascending=False).head(5)
selected_metrics: pd.DataFrame = data["metrics"]
selected_metrics = selected_metrics[(selected_metrics.candidate.eq(SELECTED)) & selected_metrics.diagnostic_kind.eq("candidate")].sort_values("quarter")

tabs = st.tabs([
    "Business View",
    "Beyond Size & Robustness",
    "Company Comparison",
    "Historical Population & M0",
    "Dictionary & Scientific Audit",
])

with tabs[0]:
    st.markdown(f"""
    <div class="m12-hero">
      <div class="m12-kicker">Exact target · M12Q quarterly-only · five-seed ensemble · 36 features</div>
      <div class="m12-title">SEC Filer/participant announcement in (information date, information date + 92 days]</div>
      <div class="m12-note"><b>Fiscal reporting cohort:</b> issuer information dates can differ inside {quarter}; this is not a same-date portfolio ranking. A separate quarter-end common-as-of diagnostic is reported under Robustness. Model scores are uncalibrated ranking scores—not announcement probabilities.</div>
      <div class="m12-note"><b>Limits:</b> sparse historical labels; missingness dependence is reduced, not eliminated; SHAP is associational and model-specific.</div>
    </div>
    """, unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns([1, 1, 1, 1.15, 1.35])
    m1.metric("Rank", f"{int(selected['rank']):,} / {len(quarter_predictions):,}")
    m2.metric("Percentile", f"{float(selected.score_percentile):.1f}%")
    m3.metric("Uncalibrated score", f"{float(selected.ensemble_uncalibrated_score):.3f}")
    m4.metric("Information available", pd.to_datetime(selected.information_available_date).strftime("%Y-%m-%d"))
    m5.metric("Forecast window", f"> {pd.to_datetime(selected.forecast_window_start_exclusive).strftime('%Y-%m-%d')} to {pd.to_datetime(selected.forecast_window_end_inclusive).strftime('%Y-%m-%d')}")
    strongest = top_non_scale.iloc[0]
    signal_direction = "increased" if non_scale_net > 0 else "reduced"
    top50_text = " · ".join(f"{row.quarter}: {int(row.positives_at_50)} positives / 50 ({row.lift_at_50:.1f}× lift)" for row in selected_metrics.itertuples())
    st.markdown(f"""
    <div class="signal"><b>Why this issuer?</b> The ensemble ranked <b>{selected.conm}</b> at percentile {float(selected.score_percentile):.1f}. Non-scale economics {signal_direction} its raw margin by <b>{non_scale_net:+.3f}</b>; the strongest verified non-size contribution was <b>{strongest.display_concept}</b> ({float(strongest.shap_value):+.3f}). Scale contributed {scale_net:+.3f}. Historical Top-50 evidence: {top50_text}.</div>
    """, unsafe_allow_html=True)
    if show_individual_outcomes:
        st.caption(f"Individual historical outcome: {'SEC Filer event in window' if int(selected.issuer_label) else 'no linked SEC Filer event in window'}. This ex-post field was off by default.")
    left, right = st.columns([.9, 1.6])
    with left:
        st.subheader("Scale versus non-scale")
        contribution = pd.DataFrame({"Signal": ["Scale", "Non-scale economics"], "Raw-margin SHAP": [scale_net, non_scale_net]})
        st.bar_chart(contribution.set_index("Signal"), horizontal=True, height=190)
        st.caption("SHAP values add to the ensemble raw margin. They are neither causal effects nor probability points.")
    with right:
        st.subheader("Top verified non-size drivers")
        driver_table = top_non_scale[["display_concept", "primary_business_theme", "raw_economic_value", "shap_value"]].rename(
            columns={"display_concept": "Economic concept", "primary_business_theme": "Executive theme", "raw_economic_value": "Raw value",
                     "shap_value": "Raw-margin SHAP"})
        st.dataframe(driver_table, width="stretch", hide_index=True, height=220,
                     column_config={"Raw value": st.column_config.NumberColumn(format="%.4f"), "Raw-margin SHAP": st.column_config.NumberColumn(format="%+.4f")})
    pos = top_detail[top_detail.driver_side.eq("positive")].sort_values("shap_value", ascending=False)
    neg = top_detail[top_detail.driver_side.eq("negative")].sort_values("shap_value")
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("Positive contribution and complete remainder", expanded=False):
            st.dataframe(pos[["display_concept", "feature_name", "raw_economic_value", "shap_value"]], width="stretch", hide_index=True)
            rem = remainder_detail[remainder_detail.remainder_side.eq("positive")]
            st.markdown(f"**Positive remainder:** {rem.shap_value.sum():+.12f} across {rem.feature_name.nunique()} raw features")
            st.dataframe(rem[["display_concept", "feature_name", "primary_business_theme", "raw_economic_value", "shap_value"]].sort_values("shap_value", ascending=False), width="stretch", hide_index=True)
    with c2:
        with st.expander("Negative contribution and complete remainder", expanded=False):
            st.dataframe(neg[["display_concept", "feature_name", "raw_economic_value", "shap_value"]], width="stretch", hide_index=True)
            rem = remainder_detail[remainder_detail.remainder_side.eq("negative")]
            st.markdown(f"**Negative remainder:** {rem.shap_value.sum():+.12f} across {rem.feature_name.nunique()} raw features")
            st.dataframe(rem[["display_concept", "feature_name", "primary_business_theme", "raw_economic_value", "shap_value"]].sort_values("shap_value"), width="stretch", hide_index=True)
    st.download_button("Download selected-company raw SHAP", detail.to_csv(index=False).encode("utf-8"), f"M12_{quarter}_{selected.gvkey}_raw_shap.csv", "text/csv")
    st.markdown("<div class='warn'><b>Limitations:</b> sparse historical labels; selected fiscal cohorts are not same-date portfolios; scores are uncalibrated; missingness dependence is reduced, not eliminated; SHAP is associational and model-specific.</div>", unsafe_allow_html=True)

with tabs[1]:
    st.subheader("Beyond Size, missingness, and multi-seed robustness")
    st.write("The candidate, scale-only, non-size, missingness-only, and frequency-only diagnostics use matched populations, labels, sampling seeds, and estimator settings. Full-population medians are frozen before negative sampling.")
    metrics = data["metrics"]
    view = metrics[(metrics.candidate.eq(SELECTED)) & metrics.diagnostic_kind.isin(["candidate", "scale_only", "non_size", "missingness"])][
        ["quarter", "diagnostic_kind", "holdout_rows", "holdout_positives", "base_rate", "average_precision", "roc_auc", "positives_at_50", "lift_at_50"]]
    st.dataframe(view.rename(columns={"diagnostic_kind": "Evidence", "average_precision": "PR-AUC", "roc_auc": "ROC-AUC", "positives_at_50": "Positives@50", "lift_at_50": "Lift@50"}),
                 width="stretch", hide_index=True)
    a, b = st.columns(2)
    with a:
        st.markdown("**Five-seed rank stability**")
        stable = data["stability"]
        stable = stable[(stable.candidate.eq(SELECTED)) & stable.diagnostic_kind.eq("candidate")][
            ["quarter", "median_score_rank_spearman", "min_score_rank_spearman", "median_top50_overlap_fraction", "min_top50_overlap_fraction"]]
        st.dataframe(stable, width="stretch", hide_index=True)
    with b:
        st.markdown("**Missingness and imputation stress**")
        stress = data["stress"]
        stress = stress[stress.candidate.eq(SELECTED)].groupby("quarter", as_index=False).agg(
            candidate_missingness_rank_spearman=("candidate_missingness_rank_spearman", "median"),
            median_distributional_rank_spearman=("median_vs_distributional_rank_spearman", "median"),
            median_distributional_top50_overlap=("median_distributional_top50_overlap_fraction", "median"))
        st.dataframe(stress, width="stretch", hide_index=True)
        st.caption("Missingness dependence is reduced, not eliminated. Distributional imputation uses only the full pre-evaluation training distribution.")
    st.markdown("**Paired issuer-level bootstrap: candidate minus comparator (2,000 valid resamples)**")
    bootstrap = data["bootstrap"]
    bootstrap = bootstrap[bootstrap.candidate.eq(SELECTED)][["quarter", "comparator", "pr_auc_difference_mean", "pr_auc_difference_ci_low", "pr_auc_difference_ci_high", "pr_auc_difference_fraction_above_zero", "roc_auc_difference_mean", "roc_auc_difference_ci_low", "roc_auc_difference_ci_high", "roc_auc_difference_fraction_above_zero"]]
    st.dataframe(bootstrap, width="stretch", hide_index=True)
    with st.expander("Separate common-as-of diagnostic", expanded=True):
        common = data["common"]
        common = common[common.candidate.eq(SELECTED)][["quarter", "holdout_rows", "holdout_positives", "base_rate", "average_precision", "roc_auc", "positives_at_50", "lift_at_50"]]
        st.dataframe(common, width="stretch", hide_index=True)
        st.caption("All issuers share the same quarter-end cutoff and subsequent 92-day label window. The fiscal-cohort-trained model is applied separately; this is diagnostic, not the primary selector population.")

with tabs[2]:
    st.subheader("Cross-company comparison")
    st.caption("Every visible company column is named `Rank | Ticker | Company`. Switch between economic values, model inputs, SHAP, percentile, and missingness.")
    top15: pd.DataFrame = data["top15"]
    headers = top15[["company_header", "rank"]].drop_duplicates().sort_values("rank").company_header.tolist()
    selected_headers = st.multiselect("Companies", headers, default=headers[:8], max_selections=15)
    measure = st.radio("Measure", ["Raw economic value", "Model value", "SHAP", "Percentile", "Missingness"], horizontal=True)
    source_column = {"Raw economic value": "raw_economic_value", "Model value": "model_value_after_full_population_median", "SHAP": "shap_value", "Percentile": "score_percentile", "Missingness": "missing"}[measure]
    compare = top15[top15.company_header.isin(selected_headers)]
    matrix = compare.pivot_table(index=["display_concept", "feature_name", "primary_business_theme", "units"], columns="company_header", values=source_column, aggfunc="first").reset_index()
    st.dataframe(matrix, width="stretch", hide_index=True, height=430)
    metadata = compare[["company_header", "conm", "tic", "rank", "score_percentile", "information_available_date", "forecast_window_start_exclusive", "forecast_window_end_inclusive"]].drop_duplicates().sort_values("rank")
    st.markdown("**Information and forecast-window metadata**")
    st.dataframe(metadata, width="stretch", hide_index=True)
    st.download_button("Download Top-15 comparison", top15.to_csv(index=False).encode("utf-8"), "historical_M12_2020Q2_top15_comparison.csv", "text/csv")

with tabs[3]:
    st.subheader("Historical SEC Filer population profile")
    st.caption("Aggregate historical outcome-stratified findings remain visible even while individual-company ex-post outcomes are off. These are descriptive associations, not causes or calibrated effects.")
    profile: pd.DataFrame = data["profile"]
    profile_columns = st.columns(2)
    for index, finding in profile.reset_index(drop=True).iterrows():
        with profile_columns[index % 2]:
            st.markdown(f"""
            <div class="profile-card">
              <div class="profile-card-title">{finding.feature_title} · {finding.direction}</div>
              <div class="profile-card-line"><b>Medians P / N:</b> {finding.positive_median:.4f} / {finding.negative_median:.4f} &nbsp; <b>Missing P / N:</b> {finding.positive_missing_rate:.1%} / {finding.negative_missing_rate:.1%}</div>
              <div class="profile-card-line"><b>Support P / N:</b> {int(finding.positive_support):,} / {int(finding.negative_support):,} &nbsp; <b>Size-controlled gap:</b> {finding.size_controlled_median_gap:+.4f}</div>
              <div class="profile-card-line"><b>Quarter stability:</b> {int(finding.quarter_stability)} / 3 &nbsp; <b>Class:</b> {finding.feature_class} &nbsp; <b>Theme:</b> {finding.executive_theme}</div>
            </div>
            """, unsafe_allow_html=True)
    if show_individual_outcomes:
        st.markdown("**Individual selected-company outcome (explicitly enabled)**")
        st.write({"company": selected.conm, "quarter": quarter, "historical_event_in_window": bool(selected.issuer_label)})
    else:
        st.info("Individual company outcomes remain hidden. Aggregate direction, medians, missingness, support, size control, stability, and feature class remain visible above.")
    st.subheader("Protected M0 forensic / SPX 75-feature view")
    m0: pd.DataFrame = data["m0"]
    st.dataframe(m0, width="stretch", hide_index=True, height=360)

with tabs[4]:
    st.subheader("Dictionary and scientific audit")
    target = data["target"]
    st.markdown(f"**Target:** {target['exact_definition']}")
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Gate 0", data["gate0"]["status"])
    q2.metric("Time / feature contract", data["contract_qa"]["status"])
    q3.metric("Multi-seed fit / selector", data["fit_qa"]["status"])
    q4.metric("Exact ensemble SHAP", data["explain_qa"]["status"])
    dictionary: pd.DataFrame = data["dictionary"]
    st.markdown("**Selected 36-feature semantic dictionary**")
    selected_dictionary = dictionary[dictionary.feature_name.isin(detail.feature_name.unique())]
    st.dataframe(selected_dictionary[["feature_name", "display_concept", "primary_business_theme", "scale_feature", "formula", "raw_mnemonics", "units", "verification_status"]], width="stretch", hide_index=True, height=370)
    st.download_button("Download dictionary", selected_dictionary.to_csv(index=False).encode("utf-8"), "historical_M12_selected_dictionary.csv", "text/csv")
    with st.expander("All 20 corrected legacy engineered mappings"):
        st.dataframe(data["mapping"], width="stretch", hide_index=True)
    with st.expander("All 32 label-conflict reconciliations"):
        st.dataframe(data["conflicts"], width="stretch", hide_index=True)
    with st.expander("Named-company rank and SHAP audit"):
        named: pd.DataFrame = data["named"]
        st.dataframe(named, width="stretch", hide_index=True)
        st.download_button("Download named-company audit", named.to_csv(index=False).encode("utf-8"), "historical_M12_named_company_audit.csv", "text/csv")
