"""Synthetic report generation/refresh, restart view and narrative UI."""
from datetime import datetime, timezone, timedelta
from streamlit.testing.v1 import AppTest
from mindmate.config import PROJECT_ROOT
from mindmate.database import initialize_database
from mindmate.services.core import Store
from mindmate.services.reports import Reports, week_bounds


def test_report_workflow(tmp_path, monkeypatch):
    path = tmp_path / "ui-reports.sqlite3"
    initialize_database(path)
    previous = datetime.now(timezone.utc).date() - timedelta(days=7)
    start, end = week_bounds(previous)
    store = Store(path)
    store.save_mood(start, 4, 2, ["Calm"], "Synthetic stressor", recorded_at=start + "T12:00:00Z")
    monkeypatch.setenv("MINDMATE_DB_PATH", str(path))
    monkeypatch.setenv("MINDMATE_LLM_ENABLED", "false")
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()
    app.sidebar.radio[0].set_value("Weekly reports").run()
    app.button(key="report_generate").click().run()
    assert not app.exception
    assert app.metric[0].value == "1"
    assert len(Reports(path).list()) == 1
    app.button(key="report_generate").click().run()
    assert not app.exception and len(Reports(path).list()) == 1
    app.button(key="report_ai_request").click().run()
    assert not app.exception
    assert app.session_state["report_ai_result"]["source"].startswith("Rule-based")
    assert len(app.get("download_button")) == 1
    restarted = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()
    restarted.sidebar.radio[0].set_value("Weekly reports").run()
    assert not restarted.exception and restarted.metric[0].value == "1"
    assert restarted.selectbox(key="report_selected").value == Reports(path).list()[0]["id"]
    confirm = next(c for c in restarted.checkbox if c.key.startswith("report_delete_confirm_"))
    confirm.check().run()
    restarted.button(key="report_delete").click().run()
    assert not restarted.exception and not Reports(path).list()


def test_report_narrative_consent_gate(tmp_path, monkeypatch):
    from unittest.mock import Mock
    path = tmp_path / "consent-report.sqlite3"
    initialize_database(path)
    previous = datetime.now(timezone.utc).date() - timedelta(days=7)
    start, _ = week_bounds(previous)
    Reports(path).generate(start)
    monkeypatch.setenv("MINDMATE_DB_PATH", str(path))
    monkeypatch.setenv("MINDMATE_LLM_ENABLED", "true")
    monkeypatch.setenv("MINDMATE_LLM_API_KEY", "synthetic")
    monkeypatch.setenv("MINDMATE_LLM_MODEL", "synthetic")
    generate = Mock(return_value={"focus": ["coverage"]})
    monkeypatch.setattr("mindmate.ai.provider.AnthropicProvider.generate_report", generate)
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()
    app.sidebar.radio[0].set_value("Weekly reports").run()
    consent = next(c for c in app.checkbox if c.key.startswith("report_ai_consent_"))
    consent.check().run()
    app.button(key="report_ai_request").click().run()
    assert not app.exception and generate.call_count == 1
    assert app.session_state["report_ai_result"]["source"].startswith("LLM-selected")
    assert not next(c for c in app.checkbox if c.key.startswith("report_ai_consent_")).value
    app.button(key="report_ai_request").click().run()
    assert not app.exception and generate.call_count == 1
    assert app.session_state["report_ai_result"]["source"].startswith("Rule-based")
