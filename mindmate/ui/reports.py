from mindmate.i18n import t
"""One-click reports; optional worker scheduling is configured separately."""
from datetime import datetime, timezone, timedelta
import hashlib
import json
import streamlit as st
from mindmate.services.reports import Reports, week_bounds, export_markdown
from mindmate.services.core import DataError
from mindmate.ui.trends import render_evidence
from mindmate.ai.report_narrative import narrative
from mindmate.ai.report_prompts import payload


def reports_view(store, settings):
    st.header(t("Weekly wellbeing reports"))
    st.write(t("A clear, saved view of your week, drawn from your own check-ins and activities."))
    st.caption(t("Local snapshots. Optional in-app scheduling requires explicit consent and a separate worker in Reminders; no email is sent. Regenerating the same week refreshes its existing snapshot."))
    today = datetime.now(timezone.utc).date()
    anchor = st.date_input(t("Choose any day in the reporting week (UTC)"), value=today - timedelta(days=7))
    start, end = week_bounds(anchor)
    st.write(f"Reporting period: {start} to {end}, inclusive UTC (Monday-Sunday).")
    from mindmate.services.vault import UserReports
    reports = UserReports(store) if getattr(store,"secure",False) else Reports(store.path)
    if st.button(t("Generate / refresh weekly report"), key="report_generate", type="primary"):
        report_id = reports.generate(start)
        st.session_state["report_selected"] = report_id
        st.success(t("Weekly report saved. An existing snapshot for this week was refreshed, not duplicated."))
    rows = reports.list()
    if not rows:
        st.info(t("No saved reports. Choose a week and generate one, even if you have no check-ins yet."))
        return
    choices = {r["id"]: r for r in rows}
    if st.session_state.get("report_selected") not in choices:
        st.session_state["report_selected"] = rows[0]["id"]
    selected = st.selectbox(t("Saved report"), list(choices), key="report_selected", format_func=lambda i: choices[i]["period_start"] + " to " + choices[i]["period_end"])
    snapshot = reports.get(selected)
    e = snapshot["evidence"]
    st.subheader(f"Saved week: {e['period_start']} to {e['period_end']}")
    st.caption(f"Snapshot as of {e['as_of']}; last refreshed {choices[selected]['updated_at']} UTC. Later source edits do not change this report until refreshed.")
    render_evidence(e)
    st.subheader(t("A moment to reflect"))
    for question in snapshot["questions"]:
        st.write("Optional question: " + question)
    for step in snapshot["next_steps"]:
        st.write("Optional next step: " + step)
    digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
    if st.session_state.get("report_ai_scope") != digest:
        st.session_state.pop("report_ai_result", None)
        st.session_state["report_ai_scope"] = digest
    st.subheader(t("Optional evidence narrative"))
    st.caption(t("The model may choose descriptive sections; all wording and numbers are rendered from this snapshot. No journals, emotion names, stressor text, dates or activity names are transmitted. Aggregate counts and statistics only are sent to Anthropic if you consent."))
    with st.expander(t("Preview exact aggregate data sent with generic instructions")):
        st.json(payload(e))
    consumed = st.session_state.pop("report_ai_consumed", None)
    if consumed:
        st.session_state[consumed] = False
    consent_key = "report_ai_consent_" + digest
    consent = st.checkbox(t("For this request, I consent to sending these aggregate statistics to Anthropic."), key=consent_key)
    if st.button(t("Add optional narrative"), key="report_ai_request"):
        with st.spinner("Preparing evidence narrative..."):
            st.session_state["report_ai_result"] = narrative(e, settings, consent=consent)
            st.session_state["report_ai_consumed"] = consent_key
            st.rerun()
    result = st.session_state.get("report_ai_result")
    if result:
        st.write(result["text"])
        st.caption(t("Narrative is session-only, labelled by source and included in this download; it is not saved in the report database."))
    try:
        markdown = export_markdown(snapshot, result["text"] if result else None)
        st.download_button(t("Download Markdown report"), data=markdown, file_name=f"mindmate-week-{e['period_start']}.md", mime="text/markdown", key="report_download", type="primary")
    except DataError as error:
        st.error(str(error))
    st.caption(t("Saved reports and downloads can contain sensitive emotion/stressor labels. Deleting source entries does not delete old report snapshots. Delete reports separately or refresh them."))
    confirm = st.checkbox(t("Confirm permanent deletion of this report"), key=f"report_delete_confirm_{selected}")
    if st.button(t("Delete saved report"), disabled=not confirm, key="report_delete"):
        reports.delete(selected)
        st.session_state.clear()
        st.session_state["notice"] = "Saved report deleted. This session was cleared; downloaded copies may remain."
        st.rerun()
