from mindmate.i18n import t
"""Application shell and functional landing page; metrics live in the dashboard."""
import streamlit as st
from mindmate.ai.provider import availability_message
from mindmate.safety.policy import WELLBEING_NOTICE, URGENT_HELP_NOTICE
from mindmate.ui.theme import apply_theme, navigate, PAGES


def render_landing(settings):
    st.set_page_config(page_title="MindMate AI | Your wellbeing companion", page_icon="M", layout="wide")
    apply_theme()
    if st.session_state.pop('account_clear',False):
        for key in ['account_password','account_recovery']:
            st.session_state.pop(key,None)
    from mindmate.ui.accounts import account_gate
    if not account_gate(settings):
        return
    if settings.demo_mode:
        st.warning(t("SYNTHETIC DEMO DATA | This separate demo database contains fictional entries for portfolio review. It is not a record of a real person."))
    st.sidebar.title(t("MindMate AI"))
    st.sidebar.caption(t("A little space for yourself"))
    from mindmate.i18n import language_picker
    language_picker(settings)
    page = st.sidebar.radio(t("Navigate"), PAGES, key="navigation", format_func=lambda value,language=st.session_state.get("ui_language","en"): t(value,language))
    st.sidebar.divider()
    st.sidebar.caption(t("YOUR SPACE, YOUR CHOICE"))
    st.sidebar.caption(t("Saved on this device. See Privacy & data for profile encryption and legacy storage limits. AI sharing requires consent."))
    st.sidebar.caption(availability_message(settings))
    st.sidebar.divider()
    st.sidebar.caption(t("Not monitored. Open Get support whenever you need it."))
    st.sidebar.selectbox(t("Support resources region"), ["Other / not specified", "India"], key="support_region")
    if st.session_state.get("support_pending"):
        from mindmate.ui.support import show_support
        show_support(st.session_state["support_pending"])
        if st.button(t("Hide this support notice"), key="support_hide_notice"):
            st.session_state.pop("support_pending", None)
            st.rerun()
    if "notice" in st.session_state:
        st.success(st.session_state.pop("notice"))
    if page != "Welcome":
        from mindmate.ui.core import render_core
        st.info(WELLBEING_NOTICE)
        render_core(settings, page)
        return
    st.markdown('<div class="mm-eyebrow">A DAILY PRACTICE IN SELF-REFLECTION</div>', unsafe_allow_html=True)
    left, right = st.columns([1.65, 1], gap="large")
    with left:
        st.title(t("Make space for how you feel."))
        st.markdown('<p class="mm-intro">Notice your days. Put feelings into words. Find small moments of care, at your own pace.</p>', unsafe_allow_html=True)
        st.write(t("Your local companion for mood check-ins, private journaling, and thoughtful weekly reflection."))
        a, b = st.columns(2)
        a.button(t("Start a check-in"), type="primary", on_click=navigate, args=("Mood tracker",), width="stretch")
        b.button(t("Open dashboard"), on_click=navigate, args=("Dashboard",), width="stretch")
        st.caption(t("No AI API key needed for your daily tools."))
    with right:
        st.markdown('''<div class="mm-note"><div class="mm-eyebrow">A GENTLER DAILY RHYTHM</div>
        <p><strong>01 &nbsp; Check in</strong><br>A mood, a few feelings, a moment to pause.</p>
        <p><strong>02 &nbsp; Reflect</strong><br>Write freely, with optional AI only when you choose.</p>
        <p><strong>03 &nbsp; Notice patterns</strong><br>Explore your recorded days without clinical labels.</p></div>''', unsafe_allow_html=True)
    st.info(WELLBEING_NOTICE)
    st.subheader(t("Choose a moment for yourself"))
    cards = [
        ("Mood tracker", "Check in with your day", "Record mood, stress and feelings. Revisit or edit your check-in whenever you need.", "Track my mood"),
        ("Journal", "Give your thoughts some space", "Write a reflection, connect it to a check-in, or request optional evidence-linked AI reflection.", "Open my journal"),
        ("Wellness activities", "Make room for a small pause", "Try an optional grounding, writing or breathing activity and note what felt helpful.", "Explore activities"),
        ("Weekly reports", "See the week in perspective", "Create a saved report from your own records, with clear explanations and a Markdown download.", "View weekly reports"),
    ]
    for offset in (0, 2):
        for col, (page_name, title, description, action) in zip(st.columns(2, gap="medium"), cards[offset:offset+2]):
            with col:
                with st.container(border=True):
                    st.subheader(title)
                    st.write(description)
                    st.button(action, key="welcome_" + page_name, on_click=navigate, args=(page_name,), width="stretch")
    with st.container(border=True):
        st.subheader(t("Privacy starts with clarity"))
        st.write(t("Profile payloads are encrypted in local SQLite; metadata and legacy records remain visible. You control whether reviewed excerpts leave this device for optional AI. See Privacy & data for key and deletion limitations."))
        st.button(t("Review privacy & data controls"), on_click=navigate, args=("Privacy & data",))
    with st.expander(t("When you need more support")):
        st.write(URGENT_HELP_NOTICE)
        st.button(t("Open Get support"), on_click=navigate, args=("Get support",))
    st.success(t("Local database initialized. Your daily tools are ready."))
    st.markdown('<div class="mm-footer">MindMate AI &nbsp; / &nbsp; General wellbeing and self-reflection &nbsp; / &nbsp; Built for thoughtful, local use</div>', unsafe_allow_html=True)
