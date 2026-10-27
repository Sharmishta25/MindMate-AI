from mindmate.i18n import t
"""Core views: forms delegate all persistence and validation to services."""
from datetime import datetime, timezone
import json
import pandas as pd
import streamlit as st
from mindmate.services.core import Store, EMOTIONS, DataError
from mindmate.services.activities import ACTIVITIES


def remove(store, table, entry_id, prefix):
    confirmed = st.checkbox(t("Confirm permanent deletion"), key=prefix + "confirm")
    if st.button(t("Delete entry"), key=prefix + "delete", disabled=not confirmed):
        store.delete(table, entry_id)
        st.session_state.clear()
        st.session_state["notice"] = "Entry deleted. This session was cleared; saved reports and external copies may still contain related information."
        st.rerun()


def mood_view(store):
    st.header(t("Mood tracker"))
    st.write(t("Pause for a moment. How has your day felt to you?"))
    st.caption(t("One check-in per UTC day. Mood: 1 Very low, 2 Low, 3 Neutral, 4 Good, 5 Very good. Stress: 0 None to 10 Extremely high. All dates and times use UTC."))
    rows = store.list("mood_entries")
    choices = {r["id"]: r for r in rows}
    pending = st.session_state.pop("mood_select_pending", None)
    if pending in choices:
        st.session_state["mood_selector"] = pending
    selected = st.selectbox(t("Check-in to edit"), [None] + list(choices), key="mood_selector", format_func=lambda i: "New check-in" if i is None else f"Check-in #{i}")
    row = choices.get(selected, {})
    st.caption(t("Choose New check-in to add a day, or select a saved check-in to edit it. Save before leaving this page."))
    if row:
        st.caption(f"Editing check-in #{selected} | {row['entry_date']} UTC")
    try:
        emotions = json.loads(row.get("emotion", "[]"))
        if not isinstance(emotions, list):
            emotions = []
    except (ValueError, TypeError):
        emotions = [row["emotion"]] if row.get("emotion") in EMOTIONS else []
    moment = datetime.fromisoformat(row["recorded_at"]) if row.get("recorded_at") else datetime.now(timezone.utc)
    with st.form(f"mood-{selected}"):
        date_col, time_col = st.columns(2)
        day = date_col.date_input(t("Check-in date (UTC)"), value=moment.date())
        clock = time_col.time_input(t("Check-in time (UTC)"), value=moment.time())
        st.subheader(t("How are you feeling?"))
        score = st.slider(t("Mood rating"), 1, 5, int(row.get("mood_score", 3)), help="1 Very low / 2 Low / 3 Neutral / 4 Good / 5 Very good. A personal rating, not a clinical assessment.")
        stress = st.slider(t("Stress level"), 0, 10, int(row.get("stress_level") or 0), help="0 No stress to 10 Extremely high stress.")
        feelings = st.multiselect(t("Emotions"), EMOTIONS, default=[e for e in emotions if e in EMOTIONS])
        triggers = st.text_input(t("Triggers (optional)"), row.get("triggers", ""), max_chars=500)
        reflection = st.text_area(t("Short reflection (optional)"), row.get("note", ""), max_chars=2000)
        save = st.form_submit_button("Save check-in" if selected is None else "Save changes", type="primary")
    from mindmate.ui.support import check_content
    route = check_content(triggers, reflection)
    if save:
        if route.show_support:
            st.session_state["support_pending"] = route
        saved_id = store.save_mood(day.isoformat(), score, stress, feelings, triggers, reflection,
                        datetime.combine(day, clock, timezone.utc).isoformat(), selected)
        if selected is None:
            st.session_state["mood_select_pending"] = saved_id
            st.session_state["notice"] = "Check-in saved. You are now viewing the saved entry; use New check-in to record another day."
            st.rerun()
        else:
            st.success(t("Check-in saved."))
    if selected is not None:
        st.caption(t("Deleting a check-in keeps linked journals and removes their association."))
        remove(store, "mood_entries", selected, "mood")


def journal_view(store, settings=None):
    st.header(t("Reflection journal"))
    st.write(t("A space to put your day into words, without needing to find the perfect ones."))
    st.caption(t("Stored locally without encryption. Content is not sent externally unless you explicitly consent to a reflection request. Journal bodies are excluded from application logs. Anyone with access to this device or app can read it."))
    rows = store.list("journal_entries")
    choices = {r["id"]: r for r in rows}
    pending = st.session_state.pop("journal_select_pending", None)
    if pending in choices:
        st.session_state["journal_selector"] = pending
    selected = st.selectbox(t("Journal entry"), [None] + list(choices), key="journal_selector", format_func=lambda i: "New journal entry" if i is None else f"Journal #{i}")
    row = choices.get(selected, {})
    st.caption(t("Choose a saved journal to read, edit or request optional reflection. Saving a new entry opens that saved journal. Save before navigating away."))
    moods = {r["id"]: r for r in store.list("mood_entries")}
    links = [None] + list(moods)
    with st.form(f"journal-{selected}"):
        date_col, title_col = st.columns([1, 2])
        day = date_col.date_input(t("Journal date (UTC)"), value=datetime.fromisoformat(row["entry_date"]).date() if row else datetime.now(timezone.utc).date())
        title = title_col.text_input(t("Title (optional)"), row.get("title", ""), key=f"journal_title_{selected}", max_chars=150)
        content = st.text_area(t("Your reflection"), row.get("content", ""), key=f"journal_content_{selected}", max_chars=20000, height=220)
        link = st.selectbox(t("Associated check-in (optional)"), links, key=f"journal_link_{selected}", index=links.index(row.get("mood_entry_id")) if row.get("mood_entry_id") in links else 0,
                            format_func=lambda i: "No association" if i is None else moods[i]["entry_date"])
        save = st.form_submit_button("Save journal" if selected is None else "Save changes", type="primary")
    from mindmate.ui.support import check_content
    route = check_content(title, content)
    if save:
        if route.show_support:
            st.session_state["support_pending"] = route
        saved_id = store.save_journal(day.isoformat(), title, content, link, selected)
        if selected is None:
            st.session_state["journal_select_pending"] = saved_id
            st.session_state["notice"] = "Journal saved. Your saved entry is open below, including optional reflection."
            st.rerun()
        else:
            st.success(t("Journal saved."))
    if selected is not None:
        fresh_saved = next((r for r in store.list("journal_entries") if r["id"] == selected), None)
        if fresh_saved:
            with st.expander(t("Read saved entry")):
                st.text(fresh_saved["content"])
        st.divider()
        st.caption(t("Delete only if you want to permanently remove this journal. Saved reports and external copies are separate."))
        remove(store, "journal_entries", selected, "journal")
        if settings is not None:
            from mindmate.ui.reflection import reflection_view
            fresh = next((r for r in store.list("journal_entries") if r["id"] == selected), None)
            if fresh:
                reflection_view(settings, store, fresh)
    if not rows:
        st.info(t("Your journal is empty. Write a first reflection above."))


def dashboard_view(store):
    st.header(t("Your wellbeing dashboard"))
    st.write(t("Notice patterns in what you recorded, with space for the days you did not."))
    rows = store.list("mood_entries")
    today = datetime.now(timezone.utc).date()
    earliest = min((datetime.fromisoformat(r["entry_date"]).date() for r in rows), default=today)
    latest = max((datetime.fromisoformat(r["entry_date"]).date() for r in rows), default=today)
    left, right = st.columns(2)
    start = left.date_input(t("From (UTC)"), value=earliest)
    end = right.date_input(t("To (UTC)"), value=max(today, latest))
    from mindmate.analytics.trends import analyze
    from mindmate.ui.trends import render_evidence
    evidence = analyze(rows, store.list("wellness_activities"), start, end, today=today)
    render_evidence(evidence)


def activities_view(store):
    st.header(t("Small wellness moments"))
    st.write(t("Choose an optional pause. There is no right way to do this, and you can stop at any time."))
    st.caption(t("Optional general wellbeing activities. These do not diagnose or treat any condition. Skip or stop any exercise that feels uncomfortable."))
    activity = st.selectbox(t("Choose an activity"), list(ACTIVITIES))
    st.write(ACTIVITIES[activity])
    with st.form("activity"):
        day = st.date_input(t("Completion date (UTC)"), value=datetime.now(timezone.utc).date())
        duration = st.number_input(t("Minutes spent"), min_value=1, max_value=180, value=3, step=1)
        helpfulness = st.selectbox(t("Perceived helpfulness (optional)"), [None, 1, 2, 3, 4, 5], format_func=lambda x: "Not rated" if x is None else str(x))
        st.caption(t("Helpfulness: 1 Not helpful to 5 Very helpful. Your own perception, not a clinical outcome."))
        done = st.form_submit_button(t("Record completed activity"), type="primary")
    if done:
        store.complete_activity(day.isoformat(), activity, duration, helpfulness)
        st.session_state["notice"] = "Completed activity recorded."
        st.rerun()
    rows = store.list("wellness_activities")
    if rows:
        st.dataframe(pd.DataFrame(rows)[["id", "activity_date", "activity_type", "duration_minutes", "helpfulness"]], hide_index=True, use_container_width=True)
        selected = st.selectbox(t("Activity record to remove"), [r["id"] for r in rows])
        remove(store, "wellness_activities", selected, "activity")
    else:
        st.info(t("No completed activities yet."))


def render_core(settings, page):
    if "notice" in st.session_state:
        st.success(st.session_state.pop("notice"))
    from mindmate.ui.accounts import user_store
    store = user_store(settings)
    try:
        if page in {'Timeline','Lifestyle','Weekly plan','Data portability','Reminders'}:
            from mindmate.ui.expansion import render_expansion
            render_expansion(store,settings,page)
            return
        from mindmate.ui.reports import reports_view
        from mindmate.ui.support import support_view
        from mindmate.ui.privacy import privacy_view
        {"Get support": lambda store: support_view(), "Privacy & data": lambda store: privacy_view(settings), "Weekly reports": lambda store: reports_view(store, settings), "Mood tracker": mood_view, "Journal": lambda store: journal_view(store, settings), "Dashboard": dashboard_view, "Wellness activities": activities_view}[page](store)
    except (ValueError, DataError) as error:
        st.error(str(error))
