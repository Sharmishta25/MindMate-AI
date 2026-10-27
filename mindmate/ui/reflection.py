from mindmate.i18n import t
"""Per-request consent and ephemeral reflection results; no journal autosend."""
import hashlib
import json
import streamlit as st
from mindmate.ai.reflection import reflect, present
from mindmate.ai.prompts import SUGGESTIONS

REASONS = {
    "consent_not_given": "External transmission was not authorized.",
    "missing_configuration": "External AI is disabled or credentials/model are missing.",
    "input_boundary": "Input was kept local because it matched a conservative safety or instruction boundary.",
    "timeout": "The provider timed out. No automatic retry was made.",
    "rate_limit": "The provider rate limit was reached. No automatic retry was made.",
    "invalid_output": "The provider response did not pass validation.",
    "service_failure": "The provider request failed.",
}


def reflection_view(settings, store, row):
    st.subheader(t("Optional journal reflection"))
    st.caption(t("AI reflections can be mistaken. Topics are tentative, not assessments or professional treatment. Dashboard metrics are calculated separately in Python."))
    # Invalidate result and consent when saved content or selected journal changes.
    signature = hashlib.sha256((str(row["id"]) + row["content"]).encode()).hexdigest()
    if st.session_state.get("reflection_entry") != signature:
        for key in list(st.session_state):
            if key.startswith("reflection_"):
                del st.session_state[key]
        st.session_state["reflection_entry"] = signature
    excerpt = st.text_area(t("Review or shorten selected entry excerpt (only this text is analyzed)"), value=row["content"][:2000], max_chars=2000, key="reflection_excerpt")
    other = {r["id"]: r for r in store.list("journal_entries") if r["id"] != row["id"]}
    ids = st.multiselect(t("Optional additional saved entries for recurring themes (maximum two)"), list(other), max_selections=2,
                         format_func=lambda i: f"Journal #{i}", key="reflection_context")
    excerpts = [excerpt]
    for index, entry_id in enumerate(ids):
        excerpts.append(st.text_area(f"Review additional excerpt {index + 1}", other[entry_id]["content"][:2000], max_chars=2000, key=f"reflection_context_text_{entry_id}"))
    from mindmate.ui.support import check_content
    # Scan the complete selected saved entry, not just a truncated excerpt.
    context_passages = [value for entry_id in ids for value in (other[entry_id]["title"], other[entry_id]["content"])]
    route = check_content(row["title"], row["content"], *context_passages, *excerpts)
    if route.show_support:
        st.session_state.pop("reflection_result", None)
        st.caption(t("Routine AI interpretation is paused here so support guidance comes first. Your writing can still be saved, edited or deleted."))
        return
    preferences = st.multiselect(t("Activities you are open to (leave empty for no suggestions)"), list(SUGGESTIONS),
                                format_func=lambda p: SUGGESTIONS[p][0], key="reflection_preferences")
    fingerprint = hashlib.sha256(json.dumps([excerpts, preferences]).encode()).hexdigest()
    st.caption(t("External provider: Anthropic, api.anthropic.com. Only the reviewed excerpts, temporary source indexes and selected activity preferences are sent. No journal titles, dates, database IDs, mood scores or other history are sent. Review for identifying details. Provider processing/retention follows your Anthropic account terms; local deletion cannot retract a request."))
    consumed = st.session_state.pop("reflection_consumed", None)
    if consumed:
        st.session_state[consumed] = False
    consent = st.checkbox(t("For this request, I consent to sending these reviewed excerpts and preferences to Anthropic."), key=f"reflection_consent_{fingerprint}")
    st.caption(t("Leave consent unchecked for a local rule-based reflection. No journal text is sent externally without your checked consent and this request."))
    if st.button(t("Request reflection"), key="reflection_request", type="primary"):
        with st.spinner("Preparing reflection..."):
            try:
                st.session_state["reflection_result"] = reflect(excerpts, preferences, settings, consent=consent, language=st.session_state.get("ui_language","en"))
                st.session_state["reflection_fingerprint"] = fingerprint
                st.session_state["reflection_dismissed"] = []
                # Consume consent; another external request requires a fresh checkbox action.
                st.session_state["reflection_consumed"] = f"reflection_consent_{fingerprint}"
                st.rerun()
            except ValueError as error:
                st.error(str(error))
    result = st.session_state.get("reflection_result")
    if result is None or st.session_state.get("reflection_fingerprint") != fingerprint:
        return
    st.info(f"Source: {result.source} | Prompt: {result.prompt_version}")
    if result.reason == "support_pathway":
        from mindmate.ui.support import show_support
        from mindmate.safety.support import SupportRoute
        show_support(SupportRoute(True, result.support_urgent))
        return
    if result.source != "LLM":
        st.caption(REASONS[result.reason])
    view = present(result)
    st.write(view["summary"])
    st.write("Explicitly stated feelings: " + (", ".join(view["stated_emotions"]) or "None matched the supported explicit first-person vocabulary. This does not mean you have no feelings."))
    st.caption(t("Possible topics are tentative interpretations of words, not proof of your emotional state. Quoted, negated or hypothetical passages can be misunderstood."))
    if view["recurring"]:
        st.write("Possible recurring topics across at least two supplied entries: " + ", ".join(view["recurring"]))
    else:
        st.caption(t("Not enough supporting entries for a recurring topic."))
    for question in view["questions"]:
        st.write("Optional question: " + question)
    with st.expander(t("Evidence used (review for mistakes)")):
        for theme in result.data["themes"]:
            st.write("Tentative topic: " + theme["theme"].replace("_", " "))
            for item in theme["evidence"]:
                st.text(f"Excerpt {item['entry'] + 1}: {item['quote']}")
        for item in result.data["emotions"]:
            st.text(f"Stated {item['emotion']} in excerpt {item['evidence']['entry'] + 1}: {item['evidence']['quote']}")
    for suggestion in view["suggestions"]:
        if suggestion["id"] in st.session_state.get("reflection_dismissed", []):
            continue
        with st.container(border=True):
            st.write(suggestion["title"])
            st.write(suggestion["instruction"])
            st.caption(suggestion["why"])
            if st.button(t("Dismiss suggestion"), key="reflection_dismiss_" + suggestion["id"]):
                st.session_state["reflection_dismissed"].append(suggestion["id"])
                st.rerun()
    st.caption(t("Reflections and dismissals remain in this app session only; they are not saved to SQLite or application logs."))
    if st.button(t("Clear reflection"), key="reflection_clear"):
        st.session_state.pop("reflection_result", None)
        st.rerun()
