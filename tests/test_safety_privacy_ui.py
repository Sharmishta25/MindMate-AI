"""Synthetic content only; exercise support before AI and explicit privacy reset."""
from unittest.mock import Mock
from streamlit.testing.v1 import AppTest
from mindmate.config import PROJECT_ROOT
from mindmate.database import initialize_database
from mindmate.services.core import Store
from mindmate.services.reports import Reports


def app_for(path, monkeypatch):
    monkeypatch.setenv("MINDMATE_DB_PATH", str(path))
    monkeypatch.setenv("MINDMATE_LLM_ENABLED", "false")
    return AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()


def test_support_after_journal_save_and_long_entry_before_ai(tmp_path, monkeypatch):
    path = tmp_path / "support-ui.sqlite3"
    app = app_for(path, monkeypatch)
    app.sidebar.radio[0].set_value("Journal").run()
    app.text_area[0].set_value("Synthetic statement: I cannot stay safe.")
    app.button[0].click().run()
    assert not app.exception
    assert any("local emergency services" in x.value for x in app.warning)
    assert any("not an assessment" in x.value for x in app.caption)
    app.button(key="support_hide_notice").click().run()
    assert not app.exception
    mid = Store(path).list("journal_entries")[0]["id"]
    Store(path).save_journal("2026-10-27", "Synthetic", "x" * 2500 + " I may hurt myself.", entry_id=mid)
    app.sidebar.radio[0].set_value("Journal").run()
    app.selectbox(key="journal_selector").set_value(mid).run()
    assert not app.exception
    assert not any(b.key == "reflection_request" for b in app.button)
    assert any("Routine AI interpretation is paused" in x.value for x in app.caption)


def test_manual_support_without_content_and_region_selection(tmp_path, monkeypatch):
    app = app_for(tmp_path / "manual.sqlite3", monkeypatch)
    app.sidebar.radio[0].set_value("Get support").run()
    assert not app.exception
    assert any("not been verified" in x.value for x in app.markdown)
    app.sidebar.selectbox(key="support_region").set_value("India").run()
    app.checkbox(key="support_immediate").check().run()
    assert not app.exception
    assert any("tel:112" in x.value for x in app.markdown)
    assert any("tel:+9114416" in x.value for x in app.markdown)
    assert any("local emergency services" in x.value for x in app.warning)


def test_user_reset_clears_records_and_private_session_state(tmp_path, monkeypatch):
    path = tmp_path / "reset-ui.sqlite3"
    initialize_database(path)
    Store(path).save_journal("2026-10-19", "Synthetic", "Synthetic journal.")
    app = app_for(path, monkeypatch)
    app.session_state["reflection_result"] = "Synthetic cached result"
    app.sidebar.radio[0].set_value("Privacy & data").run()
    assert not app.exception
    app.text_input[0].set_value("DELETE ALL MY DATA")
    app.button[1].click().run()
    assert len(Store(path).list("journal_entries")) == 1
    assert any("Acknowledge" in x.value for x in app.error)
    app.checkbox[0].check()
    app.button[1].click().run()
    assert not app.exception
    assert Store(path).list("journal_entries") == []
    assert "reflection_result" not in app.session_state
    assert any("All application records" in x.value for x in app.success)


def test_untrusted_entry_is_plain_text_and_unexpected_error_is_sanitized(tmp_path, monkeypatch, caplog):
    path = tmp_path / "render-ui.sqlite3"
    initialize_database(path)
    malicious = '<img src="https://example.invalid/track" onerror="alert(1)">'
    mid = Store(path).save_journal("2026-10-19", "Synthetic", malicious)
    app = app_for(path, monkeypatch)
    app.sidebar.radio[0].set_value("Journal").run()
    app.selectbox(key="journal_selector").set_value(mid).run()
    assert any(malicious == x.value for x in app.text)
    assert not any(malicious in x.value for x in app.markdown)
    monkeypatch.setattr("mindmate.ui.core.Store.list", Mock(side_effect=RuntimeError("Synthetic sensitive content synthetic-key")))
    app.sidebar.radio[0].set_value("Mood tracker").run()
    assert not app.exception
    assert any("page could not be completed" in x.value for x in app.error)
    assert "Synthetic sensitive content" not in caplog.text


def test_full_additional_context_is_checked_before_ai(tmp_path, monkeypatch):
    path = tmp_path / "context-support.sqlite3"
    initialize_database(path)
    store = Store(path)
    primary = store.save_journal("2026-10-19", "Synthetic", "I feel tired after work.")
    context = store.save_journal("2026-10-20", "Synthetic context", "x" * 2500 + " I cannot stay safe.")
    app = app_for(path, monkeypatch)
    app.sidebar.radio[0].set_value("Journal").run()
    app.selectbox(key="journal_selector").set_value(primary).run()
    assert any(b.key == "reflection_request" for b in app.button)
    app.multiselect(key="reflection_context").set_value([context]).run()
    assert not app.exception
    assert not any(b.key == "reflection_request" for b in app.button)
    assert any("local emergency services" in x.value for x in app.warning)
