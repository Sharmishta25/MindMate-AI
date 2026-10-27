"""Portfolio QA on synthetic local databases; no browser or live provider claims."""
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
import pytest
from streamlit.testing.v1 import AppTest
from mindmate.config import PROJECT_ROOT, load_settings
from mindmate.database import initialize_database
from mindmate.services.core import Store
from mindmate.services.reports import Reports, week_bounds, export_markdown
from mindmate.ai.provider import ProviderError
from mindmate.ui.theme import PAGES


def open_app(tmp_path, monkeypatch, *, ai=False):
    path = tmp_path / "qa.sqlite3"
    monkeypatch.setenv("MINDMATE_DB_PATH", str(path))
    monkeypatch.setenv("MINDMATE_LLM_ENABLED", "true" if ai else "false")
    monkeypatch.setenv("MINDMATE_LLM_API_KEY", "synthetic-key" if ai else "")
    monkeypatch.setenv("MINDMATE_LLM_MODEL", "synthetic-model" if ai else "")
    monkeypatch.setenv("MINDMATE_DEMO_MODE", "false")
    return AppTest.from_file(str(PROJECT_ROOT / "app.py")).run(), path


def healthy(app):
    assert not app.exception
    assert not any("page could not be completed" in item.value for item in app.error)


@pytest.mark.parametrize("button,page", [
    ("Start a check-in", "Mood tracker"), ("Open dashboard", "Dashboard"),
    ("Open my journal", "Journal"), ("Explore activities", "Wellness activities"),
    ("View weekly reports", "Weekly reports"), ("Review privacy & data controls", "Privacy & data"),
    ("Open Get support", "Get support"),
])
def test_landing_actions_navigate(tmp_path, monkeypatch, button, page):
    app, _ = open_app(tmp_path, monkeypatch)
    next(b for b in app.button if b.label == button).click().run()
    healthy(app)
    assert app.sidebar.radio[0].value == page


def test_every_navigation_empty_state(tmp_path, monkeypatch):
    app, _ = open_app(tmp_path, monkeypatch)
    for page in PAGES:
        app.sidebar.radio[0].set_value(page).run()
        healthy(app)
        if page == "Dashboard":
            assert app.metric[0].value == "0"
            assert any("No check-ins in this date range" in x.value for x in app.info)
        if page == "Weekly reports":
            assert any("No saved reports" in x.value for x in app.info)


def test_full_checkin_dashboard_activity_report_journey(tmp_path, monkeypatch):
    app, path = open_app(tmp_path, monkeypatch)
    previous = datetime.now(timezone.utc).date() - timedelta(days=7)
    start, _ = week_bounds(previous)
    moment = datetime.fromisoformat(start).date()
    app.sidebar.radio[0].set_value("Mood tracker").run()
    app.date_input[0].set_value(moment)
    app.slider[0].set_value(4)
    app.button[0].click().run()
    healthy(app)
    assert app.selectbox(key="mood_selector").value == Store(path).list("mood_entries")[0]["id"]
    app.slider[0].set_value(5)
    app.button[0].click().run()
    assert len(Store(path).list("mood_entries")) == 1
    assert Store(path).list("mood_entries")[0]["mood_score"] == 5
    app.sidebar.radio[0].set_value("Dashboard").run()
    assert app.metric[0].value == "1" and app.metric[2].value == "5.00"
    # Filter to an empty period, then deliberately reverse the range.
    app.date_input[0].set_value(moment - timedelta(days=14))
    app.date_input[1].set_value(moment - timedelta(days=7)).run()
    assert app.metric[0].value == "0"
    app.date_input[0].set_value(moment).run()
    assert any("Start date must be" in x.value for x in app.error)
    app.sidebar.radio[0].set_value("Wellness activities").run()
    app.date_input[0].set_value(moment)
    app.selectbox[1].set_value(5)
    app.button[0].click().run()
    healthy(app)
    app.sidebar.radio[0].set_value("Weekly reports").run()
    app.date_input[0].set_value(previous)
    app.button(key="report_generate").click().run()
    healthy(app)
    saved = Reports(path).get(Reports(path).list()[0]["id"])
    assert saved["evidence"]["average"] == 5
    assert saved["evidence"]["helpful_activities"][0]["count"] == 1
    assert "Completed check-ins: 1" in export_markdown(saved)
    assert len(app.get("download_button")) == 1


def test_new_journal_opens_saved_entry_and_does_not_duplicate(tmp_path, monkeypatch):
    app, path = open_app(tmp_path, monkeypatch)
    app.sidebar.radio[0].set_value("Journal").run()
    app.text_area[0].set_value("Synthetic first journal.")
    app.button[0].click().run()
    healthy(app)
    jid = Store(path).list("journal_entries")[0]["id"]
    assert app.selectbox(key="journal_selector").value == jid
    app.text_area(key=f"journal_content_{jid}").set_value("Synthetic edited journal.")
    app.button[0].click().run()
    healthy(app)
    assert len(Store(path).list("journal_entries")) == 1
    assert any(x.value == "Synthetic edited journal." for x in app.text)
    assert any(b.key == "reflection_request" for b in app.button)


@pytest.mark.parametrize("mode", ["missing", "timeout", "rate_limit", "malformed"])
def test_reflection_failure_states_in_ui(tmp_path, monkeypatch, mode):
    app, path = open_app(tmp_path, monkeypatch, ai=True)
    jid = Store(path).save_journal("2026-10-19", "Synthetic", "I feel tired after work.")
    generate = Mock()
    if mode == "missing":
        monkeypatch.setenv("MINDMATE_LLM_API_KEY", "")
    elif mode == "malformed":
        generate.return_value = {"diagnosis": "not allowed"}
    else:
        generate.side_effect = ProviderError(mode)
    monkeypatch.setattr("mindmate.ai.provider.AnthropicProvider.generate", generate)
    app.sidebar.radio[0].set_value("Journal").run()
    app.selectbox(key="journal_selector").set_value(jid).run()
    next(c for c in app.checkbox if c.key.startswith("reflection_consent_")).check().run()
    app.button(key="reflection_request").click().run()
    healthy(app)
    reason = {"missing":"missing_configuration", "malformed":"invalid_output"}.get(mode, mode)
    assert app.session_state["reflection_result"].reason == reason
    assert any("Rule-based fallback" in x.value for x in app.info)
    if mode == "missing":
        generate.assert_not_called()
    app.button(key="reflection_clear").click().run()
    healthy(app)
    assert not any("Source:" in x.value for x in app.info)


def test_activity_delete_and_clear_session_keep_correct_records(tmp_path, monkeypatch):
    app, path = open_app(tmp_path, monkeypatch)
    Store(path).save_journal("2026-10-19", "Synthetic", "Synthetic preserved journal.")
    aid = Store(path).complete_activity("2026-10-19", "Grounding pause", 3, 4)
    app.sidebar.radio[0].set_value("Wellness activities").run()
    assert app.button(key="activitydelete").disabled
    app.checkbox(key="activityconfirm").check().run()
    app.button(key="activitydelete").click().run()
    healthy(app)
    assert Store(path).list("wellness_activities") == []
    app.sidebar.radio[0].set_value("Privacy & data").run()
    app.button(key="privacy_clear_session").click().run()
    healthy(app)
    assert len(Store(path).list("journal_entries")) == 1
    assert app.sidebar.radio[0].value == "Welcome"


def test_demo_seed_is_explicit_and_non_overwriting(tmp_path, monkeypatch):
    from scripts import seed_demo
    path = tmp_path / "demo.sqlite3"
    monkeypatch.setattr(seed_demo, "DEMO_PATH", path)
    assert seed_demo.seed_demo()
    assert len(Store(path).list("mood_entries")) == 14
    assert all("SYNTHETIC" in row["content"] for row in Store(path).list("journal_entries"))
    assert not seed_demo.seed_demo()
    assert len(Store(path).list("mood_entries")) == 14
    monkeypatch.setenv("MINDMATE_DB_PATH", str(path))
    monkeypatch.setenv("MINDMATE_DEMO_MODE", "true")
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()
    assert any("SYNTHETIC DEMO DATA" in x.value for x in app.warning)
    assert load_settings({}).demo_mode is False
    with pytest.raises(ValueError):
        load_settings({"MINDMATE_DEMO_MODE":"yes"})
