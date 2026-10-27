from streamlit.testing.v1 import AppTest
from mindmate.config import PROJECT_ROOT
from mindmate.services.core import Store


def test_user_workflows(tmp_path, monkeypatch):
    path = tmp_path / "ui.sqlite3"
    monkeypatch.setenv("MINDMATE_DB_PATH", str(path))
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()
    app.sidebar.radio[0].set_value("Mood tracker").run()
    app.button[0].click().run()
    assert not app.exception
    assert len(Store(path).list("mood_entries")) == 1
    app.sidebar.radio[0].set_value("Journal").run()
    app.text_area[0].set_value("Synthetic UI reflection")
    app.button[0].click().run()
    assert not app.exception
    assert Store(path).list("journal_entries")[0]["content"] == "Synthetic UI reflection"
    app.sidebar.radio[0].set_value("Dashboard").run()
    assert not app.exception
    assert app.metric[0].value == "1"
    app.sidebar.radio[0].set_value("Wellness activities").run()
    app.button[0].click().run()
    assert not app.exception
    assert len(Store(path).list("wellness_activities")) == 1
    restarted = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()
    restarted.sidebar.radio[0].set_value("Journal").run()
    journal_id = Store(path).list("journal_entries")[0]["id"]
    restarted.selectbox[0].set_value(journal_id).run()
    assert restarted.text_area[0].value == "Synthetic UI reflection"
    restarted.text_area[0].set_value("Synthetic edited UI reflection")
    restarted.button[0].click().run()
    assert Store(path).list("journal_entries")[0]["content"] == "Synthetic edited UI reflection"
    restarted.checkbox[0].check().run()
    restarted.button[1].click().run()
    assert not Store(path).list("journal_entries")
    assert not restarted.exception
    restarted.sidebar.radio[0].set_value("Mood tracker").run()
    mid = Store(path).list("mood_entries")[0]["id"]
    restarted.selectbox[0].set_value(mid).run()
    restarted.slider[0].set_value(5)
    restarted.button[0].click().run()
    assert Store(path).list("mood_entries")[0]["mood_score"] == 5
    restarted.checkbox[0].check().run()
    restarted.button[1].click().run()
    assert not Store(path).list("mood_entries")
    assert not restarted.exception
