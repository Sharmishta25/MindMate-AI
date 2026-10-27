from mindmate.i18n import t
"""Explicit storage disclosure and user-controlled reset/session clearing."""
import streamlit as st
from mindmate.services.privacy import reset_all_data, RESET_PHRASE


def privacy_view(settings):
    st.header(t("Privacy and data controls"))
    st.info(t("Authenticated record payloads use Fernet encryption. Account identifiers, record type/date metadata and legacy tables are not encrypted. Exports and other open sessions have separate limitations."))
    st.write(t("MindMate AI supports local authenticated profiles for general wellbeing. Profile payloads are encrypted; SQLite itself and metadata are not. Explicit legacy compatibility mode has no login and retains plaintext records. Protect this device and the server environment."))
    st.write(t("Configured local storage location:"))
    st.code(str(settings.database_path), language=None)
    st.write(t("Mood entries, journals, activities and weekly snapshots persist across restarts. AI excerpts/results can also remain in this browser's server session memory until cleared or the session ends. No journal content is transmitted merely by saving it."))
    st.write(t("External reflection requires per-request consent. Reviewed excerpts may contain identifying details; redact them before sending. Report AI sends only previewed aggregate statistics. Provider processing/retention follows your account terms. Local deletion cannot retract a request or remove provider copies."))
    st.write(t("Delete individual journals, moods, activity records and reports in their respective tools. Deleting a source entry does not delete previously saved report snapshots or downloaded copies. In profile mode, reset deletes only your encrypted records, preferences, schedules and delivery history; your account remains. Legacy mode resets the original four tables."))
    st.warning(t("Deletion is logical database deletion, not guaranteed forensic erasure. SQLite pages/sidecars, OS caches, backups, exports, downloads, provider records and other open app sessions may retain copies. Close other sessions before resetting. This app does not locate or delete backups/downloads, change API keys, or contact anyone."))
    if st.button(t("Clear this app session"), key="privacy_clear_session"):
        st.session_state.clear()
        st.session_state["notice"] = "This app session was cleared. Saved database records were kept."
        st.rerun()
    with st.form("privacy_reset"):
        acknowledge = st.checkbox(t("I understand this deletes all records in my current profile (or all legacy records in compatibility mode)."))
        phrase = st.text_input(t("Type DELETE ALL MY DATA to confirm"), max_chars=30)
        submitted = st.form_submit_button(t("Reset all saved data"))
    if submitted:
        if not acknowledge:
            st.error(t("Acknowledge the deletion before resetting."))
        else:
            if settings.legacy_local:
                reset_all_data(settings.database_path, phrase)
            else:
                from mindmate.ui.accounts import user_store
                user_store(settings).reset(phrase)
            st.session_state.clear()
            st.session_state["notice"] = ("All application records and reports in legacy storage were deleted." if settings.legacy_local else "All records and reports in your profile were deleted; your account remains.") + " This session was cleared; external copies may remain."
            st.rerun()

    if not settings.legacy_local:
        st.subheader(t("Encryption key rotation"))
        st.caption(t("Operator prerequisite: put the new key first and keep old keys in MINDMATE_ENCRYPTION_KEYS, then restart the app and worker. This rotates only your profile records. Keep old backup keys securely."))
        rotate=st.checkbox(t("I have securely backed up the key ring and my records."))
        if st.button(t("Rotate my encrypted records"),disabled=not rotate):
            from mindmate.ui.accounts import user_store
            user_store(settings).rotate()
            st.success(t("Your profile records were re-encrypted with the first configured key."))
