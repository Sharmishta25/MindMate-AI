"""Synthetic journal, provider mocks, per-request consent and dismissals."""
from unittest.mock import Mock
from streamlit.testing.v1 import AppTest
from mindmate.config import PROJECT_ROOT
from mindmate.database import initialize_database
from mindmate.services.core import Store


def test_reflection_consent_fallback_dismiss_and_llm(tmp_path, monkeypatch):
    path = tmp_path / "reflection.sqlite3"
    initialize_database(path)
    entry = Store(path).save_journal("2026-10-27", "Synthetic", "I feel tired after work.")
    monkeypatch.setenv("MINDMATE_DB_PATH", str(path))
    monkeypatch.setenv("MINDMATE_LLM_ENABLED", "true")
    monkeypatch.setenv("MINDMATE_LLM_API_KEY", "synthetic-key")
    monkeypatch.setenv("MINDMATE_LLM_MODEL", "synthetic-model")
    generate = Mock(return_value={"themes": [{"theme": "work", "evidence": [{"entry": 0, "quote": "I feel tired after work"}]}],
                                 "emotions": [{"emotion": "tired", "evidence": {"entry": 0, "quote": "I feel tired"}}],
                                 "questions": ["needs"], "suggestions": [{"activity": "writing", "theme": "work"}]})
    monkeypatch.setattr("mindmate.ai.provider.AnthropicProvider.generate", generate)
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()
    app.sidebar.radio[0].set_value("Journal").run()
    app.selectbox[0].set_value(entry).run()
    app.multiselect(key="reflection_preferences").set_value(["writing"]).run()
    app.button(key="reflection_request").click().run()
    assert not app.exception
    generate.assert_not_called()
    assert any("Rule-based fallback" in x.value for x in app.info)
    app.button(key="reflection_dismiss_writing").click().run()
    assert not app.exception
    assert not any(b.key == "reflection_dismiss_writing" for b in app.button)
    consent = next(c for c in app.checkbox if c.key.startswith("reflection_consent_"))
    consent.check().run()
    app.button(key="reflection_request").click().run()
    assert not app.exception
    generate.assert_called_once_with(["I feel tired after work."], ["writing"])
    assert any("Source: LLM" in x.value for x in app.info)
    assert not next(c for c in app.checkbox if c.key.startswith("reflection_consent_")).value
    app.button(key="reflection_request").click().run()
    assert generate.call_count == 1
    assert any("Rule-based fallback" in x.value for x in app.info)
    app.text_area(key="reflection_excerpt").set_value("A changed synthetic excerpt.").run()
    assert not any("Source:" in x.value for x in app.info)
    assert not next(c for c in app.checkbox if c.key.startswith("reflection_consent_")).value
