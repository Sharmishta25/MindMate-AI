from streamlit.testing.v1 import AppTest


def test_landing_page_starts_without_ai_key(tmp_path, monkeypatch):
    from mindmate.config import PROJECT_ROOT
    monkeypatch.setenv("MINDMATE_DB_PATH", str(tmp_path / "app.sqlite3"))
    monkeypatch.setenv("MINDMATE_LLM_ENABLED", "false")
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run(timeout=20)
    assert not app.exception
    assert app.title[0].value == "Make space for how you feel."
    assert any("Local database initialized" in item.value for item in app.success)
