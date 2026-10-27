from mindmate.i18n import t
"""Always-available support and conditional guidance, with no outbound actions."""
import streamlit as st
from mindmate.safety.support import support_route, LIMITATION, URGENT_GUIDANCE, SUPPORT_GUIDANCE
from mindmate.safety.resources import VERIFIED_ON, INDIA_EMERGENCY, INDIA_SUPPORT, INDIA_WEBSITE, OTHER_REGION


def resource_links():
    region = st.session_state.get("support_region", "Other / not specified")
    if region == "India":
        st.markdown(INDIA_EMERGENCY)
        st.markdown(INDIA_SUPPORT)
        st.markdown(INDIA_WEBSITE)
        st.caption(f"Resource details reviewed {VERIFIED_ON}; availability can change. India resources only apply when you are in India. No call or contact is placed by this app.")
    else:
        st.write(OTHER_REGION)


def show_support(route, *, automatic=True):
    if not route.show_support:
        return
    st.subheader(t("Support is available"))
    if automatic:
        st.caption(t("Some wording matched a local support rule. This may be a quotation, historical experience, or a misunderstanding; it is not an assessment of your current safety."))
    if route.urgent:
        st.warning(URGENT_GUIDANCE)
    else:
        st.info(SUPPORT_GUIDANCE)
    resource_links()
    st.caption(LIMITATION)
    st.caption(t("This app is not monitored. It does not contact family, professionals, emergency services or anyone else. You choose whether to contact support."))


def check_content(*passages):
    route = support_route(*passages)
    show_support(route)
    return route


def support_view():
    st.header(t("Get support"))
    st.write(t("You can use this page whenever you want support, regardless of what any automated check shows. No description of your situation is required."))
    immediate = st.checkbox(t("I need urgent help now"), key="support_immediate")
    show_support(support_route(manual=True, immediate=immediate), automatic=False)
