"""Presentation-only review of frozen M12Q predictions and saved SHAP values."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from dashboard import m12_review_ui_helpers as h
from dashboard.sharing_paths import PUBLIC_DATA, PRIVATE_DATA, artifact_path, missing_private_files

OUT = PRIVATE_DATA
VIEWS = [
    "Overview", "Business View", "Beyond Size & Robustness", "Company Comparison",
    "Historical Population & M0", "Dictionary & Scientific Audit",
]
STATUS = (
    "Historical research prototype. Timing and label-coverage validation remain under review. "
    "Ranking scores are uncalibrated."
)
HISTORICAL = "Stored historical diagnostics — validation under review"
RANK_HELP = (
    "Inclusive position share = 100 × original rank / all stored rows in this cohort. "
    "Search, Top-N and pagination do not change the denominator. Equal scores retain "
    "the stored deterministic issuer-key ordering; this is not the stored score percentile."
)
SHAP_HELP = (
    "Signed group subtotals may contain offsetting individual effects. The diamond marks "
    "their signed net, not the total bar span. These are model associations, not causal "
    "effects or probability points."
)


@st.cache_data(show_spinner=False, max_entries=3)
def predictions(quarter):
    return h.load_predictions(OUT, quarter)


@st.cache_data(show_spinner=False, max_entries=1)
def contract():
    return h.load_contract(OUT, PUBLIC_DATA)


@st.cache_data(show_spinner=False, max_entries=24)
def raw_rows(quarter, ids, filename="historical_M12_all_evaluation_raw_shap.parquet"):
    return h.read_rows(OUT, filename, quarter, ids)


@st.cache_data(show_spinner=False, max_entries=24)
def contributions(quarter, ids):
    cohort = predictions(quarter)
    subset = cohort[cohort.issuer_quarter_row.isin(ids)]
    return h.aggregate_contributions(subset, raw_rows(quarter, ids), contract())


@st.cache_data(show_spinner=False, max_entries=24)
def csv_data(filename, m11=False):
    path = artifact_path(filename)
    if not path.is_file():
        raise h.ReviewDataError(f"Required saved artifact is missing: {path}")
    return pd.read_csv(path)


@st.cache_data(show_spinner=False, max_entries=8)
def json_data(filename):
    path = artifact_path(filename)
    if not path.is_file():
        raise h.ReviewDataError(f"Required saved artifact is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def change_cohort():
    st.session_state.review_selection = None
    st.session_state.review_focus = None
    st.session_state.review_filters = {"query": "", "mode": "Top 15", "page": 1}
    for key, value in [("filter_query", ""), ("filter_mode", "Top 15"), ("filter_page", 1)]:
        st.session_state[key] = value
    st.session_state.review_epoch += 1
    st.session_state.review_processed_event = None


def change_view():
    # A new chart instance on return cannot replay a prior selection event.
    st.session_state.review_epoch += 1
    st.session_state.review_processed_event = None


def navigate(view):
    st.session_state.review_view = view
    change_view()


def change_filter(field, widget):
    filters = dict(st.session_state.review_filters)
    filters[field] = st.session_state[widget]
    if field != "page":
        filters["page"] = 1
        st.session_state.filter_page = 1
    st.session_state.review_filters = filters
    change_view()


def select_table(widget, displayed_keys):
    key = h.key_from_table_event(st.session_state[widget], displayed_keys)
    if key is not None:
        st.session_state.review_selection = key
        st.session_state.review_focus = None


def select_chart(widget, quarter, allowed_keys, epoch):
    if epoch != st.session_state.review_epoch or st.session_state.review_view != "Overview":
        return
    event = h.key_from_chart_event(st.session_state[widget], quarter, allowed_keys)
    if event is None:
        return
    token = (epoch, *event)
    if st.session_state.review_processed_event == token:
        return
    st.session_state.review_processed_event = token
    st.session_state.review_selection, st.session_state.review_focus = event
    st.session_state.review_view = "Business View"
    st.session_state.review_epoch += 1


def select_company():
    st.session_state.review_selection = st.session_state.company_picker
    st.session_state.review_focus = None


def company_label(row):
    return f"#{int(row['rank']):,} | {row['ticker_display']} | {row['conm']}"


def signed_chart(summary, interactive=False):
    segments = h.chart_segments(summary)
    order = segments.drop_duplicates("row_key").label.tolist()
    y = alt.Y("label:N", title=None, sort=order, axis=alt.Axis(labelLimit=155))
    tooltip = [
        alt.Tooltip("conm:N", title="Company"), alt.Tooltip("rank:Q", title="Original rank"),
        alt.Tooltip("calendar_quarter:N", title="Cohort"),
        alt.Tooltip("group:N", title="Group"),
        alt.Tooltip("contribution:Q", title="Signed group subtotal", format="+.6f"),
        alt.Tooltip("total_net:Q", title="Signed total net", format="+.6f"),
        alt.Tooltip("base_value:Q", title="Stored baseline", format="+.6f"),
        alt.Tooltip("raw_output:Q", title="Stored raw output", format="+.6f"),
        alt.Tooltip("ranking_score:Q", title="Ranking score (uncalibrated)", format=".6f"),
    ]
    bars = alt.Chart(segments).mark_bar(size=17, cursor="pointer" if interactive else "default").encode(
        x=alt.X("start:Q", title="Contribution to raw model output (SHAP)", axis=alt.Axis(tickCount=5)),
        x2="end:Q", y=y,
        color=alt.Color("group:N", title=None, scale=alt.Scale(
            domain=["Scale", "Non-scale"], range=["#3274A1", "#D68A2D"]),
            legend=alt.Legend(orient="top", direction="horizontal")),
        tooltip=tooltip,
    )
    if interactive:
        bars = bars.add_params(alt.selection_point(
            name="open_company", fields=["row_key", "calendar_quarter", "group"],
            on="click", clear=False, toggle=False,
        ))
    net = alt.Chart(segments[segments.group.eq("Scale")]).mark_point(
        shape="diamond", filled=True, color="#B5BAC5", size=65,
    ).encode(x="total_net:Q", y=y, tooltip=[item for item in tooltip if item.shorthand not in {"group:N", "contribution:Q"}])
    zero = alt.Chart(pd.DataFrame({"zero": [0]})).mark_rule(color="#7B8494").encode(x="zero:Q")
    # Reserve room for the legend and axes in Streamlit's fit-height chart.
    return (zero + bars + net).properties(height=max(148, len(summary) * 28 + 120)).configure_axis(
        labelFontSize=12, titleFontSize=12,
    ).configure_view(stroke=None)


def no_outcomes(frame):
    return frame.drop(columns=["issuer_label", "historical_event_in_window"], errors="ignore")


def show_metadata(row, detail=None):
    records = {
        "Stable row key": row.row_key, "Issuer key": row.issuer_key,
        "GVKEY": row.gvkey, "Normalized CIK": row.valid_cik,
        "Identity status": "CIK unavailable; row retained" if pd.isna(row.valid_cik) else "Stored CIK; historical linkage is not independently certified",
        "Fiscal period date": str(pd.Timestamp(row.fiscal_period_date).date()),
        "Information available (model-defined)": str(pd.Timestamp(row.information_available_date).date()),
        "Forecast start (exclusive)": str(pd.Timestamp(row.forecast_window_start_exclusive).date()),
        "Forecast end (inclusive)": str(pd.Timestamp(row.forecast_window_end_inclusive).date()),
        "Stored score percentile (unchanged)": row.score_percentile,
    }
    if detail is not None:
        records["Missing selected inputs"] = f"{int(detail['missing'].sum())} / {len(detail)}"
    st.dataframe(pd.DataFrame({"Field": list(records), "Stored value / interpretation": [str(v) for v in records.values()]}), hide_index=True)
    st.caption("The information date is the row's model-defined date, not a training cutoff or proof of point-in-time validity. The stored window is after that date through +92 calendar days inclusive.")


st.set_page_config(page_title="M12 research review", page_icon="◇", layout="wide", initial_sidebar_state="collapsed")
defaults = {
    "review_view": "Overview", "review_cohort": "2020Q2", "review_selection": None,
    "review_focus": None, "review_epoch": 0, "review_processed_event": None,
    "review_filters": {"query": "", "mode": "Top 15", "page": 1}, "show_outcomes": False,
}
for state_key, default in defaults.items():
    st.session_state.setdefault(state_key, default)

st.header("M12 research review")
st.caption(STATUS)
missing_private = missing_private_files()
if missing_private:
    st.warning("Code-only checkpoint: authorized local-only artifacts are unavailable. No model, prediction or SHAP calculation will run.")
    st.write("Private GitHub visibility does not grant data redistribution rights. See DATA_NOTICE.md for the exact local dependencies and authorization requirements.")
    st.subheader("Missing local-only runtime files")
    st.code("\n".join(missing_private), language=None)
    st.caption("The approved legacy preview is retained in the repository; it is not evidence of the revised UI or scientific approval.")
    st.stop()
with st.container(horizontal=True, vertical_alignment="bottom"):
    quarter = st.selectbox("Fiscal reporting cohort", h.COHORTS, key="review_cohort", on_change=change_cohort, width=210)
    show_outcomes = st.toggle("Show individual ex-post outcomes", key="show_outcomes", width=320,
                              help="Off by default. These are fixed-corpus historical labels, not independently verified event absence.")
    st.caption("M12Q · 36 features · five-seed ensemble · local review only")

try:
    cohort = predictions(quarter)
    selected_contract = contract()
except (h.ReviewDataError, FileNotFoundError, ValueError, KeyError) as exc:
    st.error(f"Cannot display the saved research artifacts: {exc}. No replacement predictions were generated.")
    st.stop()

st.session_state.review_selection = h.resolve_selection(st.session_state.review_selection, cohort)
selected_key = st.session_state.review_selection
selected = None if selected_key is None else cohort.set_index("row_key", drop=False).loc[selected_key]
tabs = st.tabs(VIEWS, key="review_view", on_change=change_view)

try:
    if tabs[0].open:
        with tabs[0]:
            st.subheader(f"{quarter} · {len(cohort):,} stored issuer rows")
            st.caption("Rank 1 first. Issuer information dates differ within this fiscal-reporting cohort; this is not a same-date portfolio or a verified US-listed universe. Missing identifiers remain in the population.")
            filters = st.session_state.review_filters
            for field, widget in [("query", "filter_query"), ("mode", "filter_mode"), ("page", "filter_page")]:
                st.session_state.setdefault(widget, filters[field])
            with st.container(horizontal=True, vertical_alignment="bottom"):
                mode = st.selectbox("Show", ["Top 15", "Top 25", "Top 50", "Top 100", "Full list"],
                                    key="filter_mode", on_change=change_filter, args=("mode", "filter_mode"), width=150)
                query = st.text_input("Search company or ticker", key="filter_query", placeholder="Search the full cohort",
                                      on_change=change_filter, args=("query", "filter_query"))
                limit = None if mode == "Full list" else int(mode.split()[-1])
                displayed, matches, page_count = h.select_overview(cohort, query, limit, filters["page"])
                if st.session_state.filter_page > page_count:
                    st.session_state.filter_page = page_count
                st.number_input("Page", min_value=1, max_value=max(1, page_count), step=1, key="filter_page",
                                on_change=change_filter, args=("page", "filter_page"), width=100)
            if displayed.empty:
                st.info("No matching companies. Clear the search or choose another cohort. No company details are shown for this empty result.")
            else:
                st.caption(f"Showing {len(displayed):,} of {matches:,} {'search matches' if query.strip() else 'rows in this view'} · page {st.session_state.filter_page} of {page_count} · rank-share denominator stays {len(cohort):,}.")
                identity = hashlib.sha256("|".join(displayed.row_key).encode()).hexdigest()[:12]
                epoch = st.session_state.review_epoch
                table_key = f"overview_table_{quarter}_{identity}_{epoch}"
                chart_key = f"overview_chart_{quarter}_{identity}_{epoch}"
                keys = tuple(displayed.row_key)
                ids = tuple(int(v) for v in displayed.issuer_quarter_row)
                summary = contributions(quarter, ids)
                left, right = st.columns([1.5, 1], gap="medium")
                with left:
                    st.markdown("**Ranked companies**")
                    st.dataframe(
                        h.overview_columns(displayed), hide_index=True, key=table_key,
                        selection_mode="single-row", on_select=lambda: select_table(table_key, keys),
                        selection_default={"selection": {"rows": [keys.index(selected_key)] if selected_key in keys else []}},
                        height=min(630, 38 + 35 * len(displayed)),
                        column_config={
                            "Rank": st.column_config.NumberColumn(width=48, pinned=True),
                            "Ticker": st.column_config.TextColumn(width=70),
                            "Company name": st.column_config.TextColumn(width=220),
                            "Top X% of cohort": st.column_config.TextColumn(help=RANK_HELP, width=130),
                            "Ranking score (uncalibrated)": st.column_config.NumberColumn(format="%.6f", help="Original stored uncalibrated ranking score; not an event probability.", width=200),
                        },
                    )
                    if selected is not None:
                        st.markdown(f"**Current selection:** {company_label(selected)}")
                        if selected_key not in keys:
                            st.caption("This preserved selection is outside the displayed page. Select a visible row to change it.")
                        st.button("Open company details", type="primary", on_click=navigate, args=("Business View",))
                        with st.expander("Selected row: dates, identity and missingness"):
                            show_metadata(selected, raw_rows(quarter, (int(selected.issuer_quarter_row),)))
                with right:
                    st.markdown("**Scale and non-scale contributions**")
                    st.caption("Click either colored segment to open that company. Diamond = signed net.")
                    # Bound the scroll container, not the chart: a fixed chart height
                    # would compress Top-100 rows instead of retaining readable spacing.
                    with st.container(height=min(680, 150 + len(summary) * 28), border=False):
                        st.altair_chart(signed_chart(summary, interactive=True), key=chart_key,
                                        on_select=lambda: select_chart(chart_key, quarter, keys, epoch),
                                        selection_mode=["open_company"], width="stretch")
                    st.caption(SHAP_HELP)
                with st.expander("Signed subtotals and numerical reconciliation"):
                    st.dataframe(summary[["rank", "conm", "scale_net", "non_scale_net", "total_net", "base_value", "raw_output", "ranking_score", "raw_error", "score_error"]], hide_index=True)
                    st.caption("Stored five-seed mean baseline + Scale + Non-scale = raw output; expit(raw output) matches the saved score within absolute tolerance 1e-10. No model was executed.")

    if tabs[1].open:
        with tabs[1]:
            st.button("Back to Overview", on_click=navigate, args=("Overview",))
            if cohort.empty:
                st.info("No stored rows in this cohort.")
            else:
                lookup = cohort.set_index("row_key", drop=False)
                labels = {key: company_label(row) for key, row in lookup.iterrows()}
                st.session_state.company_picker = selected_key
                st.selectbox("Selected company", list(labels), format_func=labels.get, key="company_picker", on_change=select_company)
                st.subheader(str(selected.conm))
                st.caption(f"{quarter} · {selected.ticker_display} · row identity {selected.row_key} · SEC-filer/participant announcement in the stored 92-day window; not a buyer/target/seller role prediction.")
                ids = (int(selected.issuer_quarter_row),)
                detail = raw_rows(quarter, ids)
                summary = contributions(quarter, ids)
                contribution = summary.iloc[0]
                m1, m2, m3, m4 = st.columns([1, 1, 1, 1.35])
                with m1.container(border=True):
                    st.metric("Rank", f"{int(selected['rank']):,} / {len(cohort):,}", help=RANK_HELP)
                    st.caption(h.format_top_share(int(selected['rank']), len(cohort)))
                m2.metric("Ranking score (uncalibrated)", f"{selected.ensemble_uncalibrated_score:.6f}", border=True,
                          help="Stored ranking score, not a calibrated event probability.")
                m3.metric("Information available", str(pd.Timestamp(selected.information_available_date).date()), border=True,
                          help="The row's model-defined information date, not the training cutoff. Timing validation remains unresolved.")
                with m4.container(border=True):
                    st.caption("Forecast window (92 calendar days)")
                    st.write(f"After {pd.Timestamp(selected.forecast_window_start_exclusive).date()}")
                    st.write(f"through {pd.Timestamp(selected.forecast_window_end_inclusive).date()} inclusive")
                if st.session_state.review_focus:
                    st.caption(f"Opened from the {st.session_state.review_focus} segment. All signed contributions and detailed drivers remain visible below.")
                st.write(f"Scale {contribution.scale_net:+.6f} + Non-scale {contribution.non_scale_net:+.6f} = net {contribution.total_net:+.6f}. Stored baseline {contribution.base_value:+.6f} + net = raw output {contribution.raw_output:+.6f}.")
                if show_outcomes:
                    label = pd.read_parquet(OUT / "historical_M12_ensemble_predictions.parquet", columns=["issuer_label"], filters=[("calendar_quarter", "=", quarter), ("candidate", "=", h.SELECTED), ("diagnostic_kind", "=", "candidate"), ("issuer_quarter_row", "=", ids[0])]).issuer_label.iloc[0]
                    st.caption("Stored individual ex-post label: " + ("linked SEC-filer event in the fixed corpus." if label else "fixed-corpus nonmatch; not verified absence of an M&A announcement."))
                a, b = st.columns([1, 1.4])
                with a:
                    st.markdown("**Scale versus non-scale**")
                    st.altair_chart(signed_chart(summary), width="stretch")
                    st.caption(SHAP_HELP)
                with b:
                    st.markdown("**Top stored non-scale drivers**")
                    strongest = detail[~detail.feature_name.isin(h.SCALE_FEATURES)].sort_values("shap_value", key=lambda v: v.abs(), ascending=False).head(5)
                    st.dataframe(strongest[["display_concept", "primary_business_theme", "raw_economic_value", "shap_value"]].rename(columns={"display_concept": "Economic concept", "primary_business_theme": "Executive theme", "raw_economic_value": "Raw value", "shap_value": "Raw-margin SHAP"}), hide_index=True,
                                 column_config={"Raw value": st.column_config.NumberColumn(format="%.4f"), "Raw-margin SHAP": st.column_config.NumberColumn(format="%+.6f")})
                top = raw_rows(quarter, ids, "historical_M12_top_visible_raw_drivers.parquet")
                remainder = raw_rows(quarter, ids, "historical_M12_inline_remainder_rows.parquet")
                a, b = st.columns(2)
                for side, container in [("positive", a), ("negative", b)]:
                    with container.expander(f"{side.title()} contribution and complete remainder"):
                        visible = top[top.driver_side.eq(side)].sort_values("shap_value", ascending=side == "negative")
                        st.dataframe(visible[["display_concept", "feature_name", "raw_economic_value", "shap_value"]], hide_index=True)
                        rem = remainder[remainder.remainder_side.eq(side)].sort_values("shap_value", ascending=side == "negative")
                        st.markdown(f"**{side.title()} remainder:** {rem.shap_value.sum():+.12f} across {rem.feature_name.nunique()} raw features")
                        st.dataframe(rem[["display_concept", "feature_name", "primary_business_theme", "raw_economic_value", "shap_value"]], hide_index=True)
                with st.expander("Dates, identity, missingness and reconciliation"):
                    show_metadata(selected, detail)
                    st.dataframe(summary, hide_index=True)
                    st.caption("Raw and score reconciliation tolerance: 1e-10. Exact arithmetic agreement is not proof of causal effects, direct grouped/Owen attribution, temporal validity, regime stability or redistribution rights.")
                st.download_button("Download selected-company raw SHAP", (detail if show_outcomes else no_outcomes(detail)).to_csv(index=False).encode(), f"M12_{quarter}_{selected.gvkey}_raw_shap.csv", "text/csv")

    if tabs[2].open:
        with tabs[2]:
            st.subheader("Beyond Size, missingness, and multi-seed robustness")
            st.warning(HISTORICAL)
            st.caption("Unchanged retrospective fixed-corpus metrics. Later evidence identified timing and label-coverage limitations; these are not certified out-of-time performance estimates.")
            metrics = csv_data("historical_M12_ensemble_metrics.csv")
            st.dataframe(metrics[(metrics.candidate.eq(h.SELECTED)) & metrics.diagnostic_kind.isin(["candidate", "scale_only", "non_size", "missingness"])][["quarter", "diagnostic_kind", "holdout_rows", "holdout_positives", "base_rate", "average_precision", "roc_auc", "positives_at_50", "lift_at_50"]], hide_index=True)
            st.markdown("**Five-seed rank stability**")
            stable = csv_data("historical_M12_rank_stability_summary.csv")
            st.dataframe(stable[stable.candidate.eq(h.SELECTED) & stable.diagnostic_kind.eq("candidate")], hide_index=True)
            st.markdown("**Missingness and imputation stress**")
            stress = csv_data("historical_M12_missingness_and_imputation_stress.csv")
            st.dataframe(stress[stress.candidate.eq(h.SELECTED)], hide_index=True)
            st.markdown("**Paired issuer-level bootstrap**")
            bootstrap = csv_data("historical_M12_paired_bootstrap_comparisons.csv")
            st.dataframe(bootstrap[bootstrap.candidate.eq(h.SELECTED)], hide_index=True)
            with st.expander("Separate common-as-of diagnostic", expanded=True):
                common = csv_data("historical_M12_common_asof_ensemble_metrics.csv")
                st.dataframe(common[common.candidate.eq(h.SELECTED)], hide_index=True)
                st.caption("A separate shared quarter-end cutoff and 92-day window. This does not replace the primary fiscal-reporting cohort or resolve its training/coverage limitations.")

    if tabs[3].open:
        with tabs[3]:
            st.subheader("Cross-company comparison")
            st.caption("Saved 2020Q2 Top-15 comparison only, independent of the cohort control. Original scores, ranks and percentiles are preserved.")
            top15 = csv_data("historical_M12_2020Q2_top15_comparison_long.csv")
            headers = top15[["company_header", "rank"]].drop_duplicates().sort_values("rank").company_header.tolist()
            selected_headers = st.multiselect("Companies", headers, default=headers[:8], max_selections=15)
            measure = st.segmented_control("Measure", ["Raw economic value", "Model value", "SHAP", "Percentile", "Missingness"], default="Raw economic value")
            source = {"Raw economic value": "raw_economic_value", "Model value": "model_value_after_full_population_median", "SHAP": "shap_value", "Percentile": "score_percentile", "Missingness": "missing"}.get(measure, "raw_economic_value")
            compare = top15[top15.company_header.isin(selected_headers)]
            if compare.empty:
                st.info("Select at least one company to compare.")
            else:
                matrix = compare.pivot_table(index=["display_concept", "feature_name", "primary_business_theme", "units"], columns="company_header", values=source, aggfunc="first").reset_index()
                st.dataframe(matrix, hide_index=True, height=430)
                st.markdown("**Information and forecast-window metadata**")
                st.dataframe(compare[["company_header", "conm", "tic", "rank", "score_percentile", "information_available_date", "forecast_window_start_exclusive", "forecast_window_end_inclusive"]].drop_duplicates().sort_values("rank"), hide_index=True)
            st.download_button("Download Top-15 comparison", no_outcomes(top15).to_csv(index=False).encode(), "historical_M12_2020Q2_top15_comparison.csv", "text/csv")

    if tabs[4].open:
        with tabs[4]:
            st.subheader("Historical SEC Filer population profile")
            st.warning(HISTORICAL)
            st.caption("Aggregate outcome-stratified associations, not causal effects. Original negative labels are fixed-corpus nonmatches, not newly certified non-events.")
            st.dataframe(csv_data("historical_M12_sec_filer_population_findings.csv"), hide_index=True)
            st.subheader("Protected M0 forensic / SPX 75-feature view")
            st.caption("Separate historical M0 lineage; not the selected M12Q model or the selected company's new prediction.")
            st.dataframe(csv_data("historical_M11_M0_SPX_75_feature_forensic.csv", m11=True), hide_index=True, height=420)

    if tabs[5].open:
        with tabs[5]:
            st.subheader("Dictionary and scientific audit")
            st.markdown(f"**Target:** {json_data('historical_M12_target_time_contract.json')['exact_definition']}")
            st.warning("Historical check statuses below are saved engineering checks, not current scientific certification. Unqualified leakage-safe and GS-ready claims were withdrawn by the completed evidence-closure review.")
            checks = [("Gate 0", "gate0"), ("Time / feature contract", "contract"), ("Multi-seed fit / selector", "fit"), ("Exact ensemble SHAP", "explanation")]
            status_rows = [{"Historical check": name, "Stored status (unchanged)": json_data(f"historical_M12_{file}_qa.json")["status"]} for name, file in checks]
            st.dataframe(pd.DataFrame(status_rows), hide_index=True)
            st.caption("Evidence: mna-refresh-preflight/m12_evidence_closure_2026q1/EVIDENCE_CLOSURE_REPORT.md. Future-information/label-maturity exposure and negative-label coverage remain unresolved. UI checks do not certify redistribution rights.")
            dictionary = selected_contract["dictionary"]
            st.markdown("**Selected 36-feature semantic dictionary**")
            st.dataframe(dictionary[["feature_name", "display_concept", "primary_business_theme", "scale_feature", "formula", "raw_mnemonics", "units", "verification_status"]], hide_index=True, height=370)
            st.download_button("Download dictionary", dictionary.to_csv(index=False).encode(), "historical_M12_selected_dictionary.csv", "text/csv")
            with st.expander("All 20 corrected legacy engineered mappings"):
                st.dataframe(csv_data("historical_M12_legacy_20_feature_mapping.csv"), hide_index=True)
            with st.expander("All 32 label-conflict reconciliations"):
                st.caption("Saved audit evidence, not a new adjudication of outcomes.")
                st.dataframe(csv_data("historical_M12_label_conflict_reconciliation.csv"), hide_index=True)
            with st.expander("Named-company rank and SHAP audit"):
                named = csv_data("historical_M12_named_company_rank_and_shap_audit.csv")
                named = named if show_outcomes else no_outcomes(named)
                st.dataframe(named, hide_index=True)
                st.download_button("Download named-company audit", named.to_csv(index=False).encode(), "historical_M12_named_company_audit.csv", "text/csv")
except (h.ReviewDataError, FileNotFoundError, ValueError, KeyError) as exc:
    st.error(f"Saved-data display stopped: {exc}. No replacement predictions or explanations were generated.")
