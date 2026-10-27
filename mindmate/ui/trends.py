from mindmate.i18n import t
"""Shared evidence views for live dashboard and immutable report snapshots."""
import pandas as pd
import plotly.express as px
import streamlit as st
from mindmate.services.reports import formatted
from mindmate.ui.theme import chart_style


def render_evidence(e):
    a, b, c = st.columns(3)
    a.metric(t("Recorded check-ins"), e["count"])
    b.metric(t("Recent mood"), f"{e['recent']} / 5" if e["recent"] is not None else "No data")
    c.metric(t("Average mood"), formatted(e["average"]))
    a, b, c = st.columns(3)
    a.metric(t("Median mood"), formatted(e["median"]))
    b.metric(t("Recorded days"), f"{e['recorded_days']} / {e['days']}")
    c.metric(t("Missing days"), e["missing_days"])
    st.caption(t("All dates are inclusive UTC. Recent mood = latest recorded score in this period. Mood scale: 1 Very low to 5 Very good."))
    if not e["count"]:
        st.info(t("No check-ins in this date range yet. Add a check-in from Mood tracker, or choose a range with saved entries."))
    if e["small_sample"] and e["count"]:
        st.warning(t("Small sample: fewer than five check-ins. Treat these summaries cautiously."))
    st.caption(f"Unrecorded elapsed days: {e['missing_elapsed_days']}; future calendar days: {e['future_days']}.")
    if not e["period_ended"]:
        st.info(t("Ongoing/incomplete period. Future and unrecorded days are unobserved."))
    st.caption(f"Coverage: {e['coverage']:.1%}. Missing days are gaps, never zero scores.")
    st.subheader(t("Mood over time"))
    if e["daily_trend_supported"]:
        frame = pd.DataFrame(e["daily"])
        fig = px.line(frame, x="date", y="mean_mood", markers=True, title="Daily mood (gaps are missing days)", hover_data=["check_ins"], labels={"date": "UTC date", "mean_mood": "Mean mood (1-5)"})
        fig.update_traces(connectgaps=False)
        fig.update_yaxes(range=[.8, 5.2], dtick=1)
        st.plotly_chart(chart_style(fig), width="stretch", config={"displaylogo": False, "scrollZoom": False})
    else:
        st.caption(t("A daily chart will appear after check-ins on at least two distinct days. Missing days remain gaps."))
    with st.expander(t("Daily values (table alternative to the chart)")):
        st.dataframe(pd.DataFrame(e["daily"]).rename(columns={"date":"UTC date", "mean_mood":"Average mood (1-5)", "check_ins":"Check-ins"}), hide_index=True, width="stretch")
    weekly = pd.DataFrame(e["weekly"])
    if e["weekly_trend_supported"]:
        # Weeks with fewer than three check-ins are gaps in the trend line.
        weekly["trend_mean"] = weekly.apply(lambda r: r["average"] if r["count"] >= 3 else None, axis=1)
        fig = px.line(weekly, x="date", y="trend_mean", markers=True, title="Weekly mean mood", hover_data=["count", "recorded_days", "label"], labels={"date": "Week starting Monday (UTC)", "trend_mean": "Mean mood (1-5)"})
        fig.update_traces(connectgaps=False)
        fig.update_yaxes(range=[.8, 5.2], dtick=1)
        st.plotly_chart(chart_style(fig), width="stretch", config={"displaylogo": False, "scrollZoom": False})
    else:
        st.caption(t("A weekly trend needs at least two weeks with three check-ins each. You can still inspect weekly values below."))
    with st.expander(t("Weekly values and data coverage")):
        st.dataframe(weekly[["date", "count", "average", "median", "recorded_days", "label"]].rename(columns={"date":"Week starting (UTC)", "count":"Check-ins", "average":"Average mood", "median":"Median mood", "recorded_days":"Recorded days", "label":"Coverage note"}), hide_index=True, width="stretch")
    comparison = e["comparison"]
    st.subheader(t("Period comparison"))
    st.caption(comparison["explanation"])
    if comparison["supported"]:
        st.write(f"Previous period {comparison['previous_start']} to {comparison['previous_end']}: {comparison['previous_count']} check-ins, {comparison['previous_coverage']:.1%} coverage. Previous average {comparison['previous_average']:.2f}; descriptive change {comparison['average_change']:+.2f} mood points.")
    for label, key in [("Selected emotions", "emotions"), ("User-reported stressor labels", "triggers"), ("Activities rated helpful", "helpful_activities")]:
        st.subheader(label)
        if e[key]:
            st.dataframe(pd.DataFrame(e[key]).rename(columns={"label":"Reported label", "count":"Records", "average_helpfulness":"Average helpfulness (1-5)"}), hide_index=True, width="stretch")
        else:
            st.caption(t("None recorded in this period."))
    st.caption(t("Emotion/stressor counts refer to check-ins, not intensity. Recurring means at least two records. Helpful activities are self-rated 4 or 5; unrated activities are excluded. These records do not establish causes or treatment effects."))
    with st.expander(t("How every metric is calculated")):
        st.write(e["methods"])
