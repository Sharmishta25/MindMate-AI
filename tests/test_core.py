"""All content below is synthetic test data, never real journal content."""
import sqlite3
import pytest
from mindmate.database import initialize_database, connect, SCHEMA
from mindmate.services.core import Store, DataError
from mindmate.analytics.moods import summarize


@pytest.fixture
def store(tmp_path):
    path = tmp_path / "core.sqlite3"
    initialize_database(path)
    return Store(path)


def mood(store, date="2026-10-26", score=3):
    return store.save_mood(date, score, 4, ["Calm"], "Synthetic trigger", "Synthetic reflection", date + "T12:30:00+00:00")


def test_full_crud_and_restart_persistence(store):
    mid = mood(store)
    jid = store.save_journal("2026-10-26", "Synthetic title", "Synthetic content", mid)
    store.save_journal("2026-10-27", "Revised", "Synthetic revision", mid, jid)
    store.save_mood("2026-10-26", 5, 2, ["Happy"], recorded_at="2026-10-26T13:00:00Z", entry_id=mid)
    aid = store.complete_activity("2026-10-26", "Grounding pause", 3, 5)
    initialize_database(store.path)
    reopened = Store(store.path)
    assert reopened.list("mood_entries")[0]["mood_score"] == 5
    assert reopened.list("journal_entries")[0]["content"] == "Synthetic revision"
    assert reopened.list("wellness_activities")[0]["helpfulness"] == 5
    reopened.delete("mood_entries", mid)
    assert reopened.list("journal_entries")[0]["mood_entry_id"] is None
    reopened.delete("journal_entries", jid)
    reopened.delete("wellness_activities", aid)
    assert not reopened.list("journal_entries")
    with pytest.raises(ValueError):
        reopened.delete("wellness_activities", aid)


def test_duplicate_and_missing_link_preserve_data(store):
    mood(store)
    with pytest.raises(DataError):
        mood(store, score=1)
    assert store.list("mood_entries")[0]["mood_score"] == 3
    with pytest.raises(DataError):
        store.save_journal("2026-10-26", "Synthetic", "Synthetic content", 999)
    assert not store.list("journal_entries")


@pytest.mark.parametrize("change", [
    {"entry_date": "2026-02-30"}, {"score": 0}, {"score": True}, {"stress": 11},
    {"emotions": ["Unknown"]}, {"triggers": "x" * 501}, {"reflection": "x" * 2001},
    {"recorded_at": "2026-10-26T10:00:00"}, {"recorded_at": "2026-10-27T10:00:00Z"},
])
def test_mood_validation(store, change):
    args = dict(entry_date="2026-10-26", score=3, stress=1, emotions=[], recorded_at="2026-10-26T10:00:00Z")
    with pytest.raises(ValueError):
        store.save_mood(**(args | change))
    assert not store.list("mood_entries")


@pytest.mark.parametrize("content", ["", "   ", "x" * 20001, None])
def test_journal_validation(store, content):
    with pytest.raises(ValueError):
        store.save_journal("2026-10-26", "Synthetic", content)


def test_long_text_and_sql_are_literal(store):
    content = "x" * 20000
    jid = store.save_journal("2026-10-26", "'); DROP TABLE mood_entries;--", content)
    assert store.list("journal_entries")[0]["content"] == content
    assert store.list("mood_entries") == []
    with pytest.raises(ValueError):
        store.delete("journal_entries; DROP TABLE mood_entries", jid)


@pytest.mark.parametrize("activity,duration,rating", [("Unknown", 3, None), ("Grounding pause", 0, 2), ("Grounding pause", 3, 6)])
def test_activity_validation(store, activity, duration, rating):
    with pytest.raises(ValueError):
        store.complete_activity("2026-10-26", activity, duration, rating)


def test_metrics_filters_and_week_boundaries(store):
    mood(store, "2026-10-25", 1)  # Sunday
    mood(store, "2026-10-26", 3)  # Monday
    mood(store, "2026-10-28", 5)
    stats = summarize(store.list("mood_entries"), "2026-10-25", "2026-10-28")
    assert stats["count"] == 3 and stats["average"] == 3 and stats["recent"] == 5
    assert stats["weekly"]["mean_mood"].tolist() == [1, 4]
    assert len(stats["daily"]) == 3
    single = summarize(store.list("mood_entries"), "2026-10-26", "2026-10-26")
    assert single["count"] == 1 and single["average"] == 3
    assert summarize([], "2026-10-01", "2026-10-02")["recent"] is None
    assert summarize(store.list("mood_entries"), "2025-01-01", "2025-01-02")["count"] == 0
    with pytest.raises(ValueError):
        summarize([], "2026-10-28", "2026-10-25")


def test_v1_migration_preserves_records(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    with connect(path) as db:
        db.executescript(SCHEMA)
        db.execute("INSERT INTO mood_entries(entry_date,mood_score,emotion) VALUES ('2026-10-26',2,'Calm')")
        db.execute("INSERT INTO journal_entries(entry_date,content) VALUES ('2026-10-26','Synthetic legacy')")
        db.execute("PRAGMA user_version=1")
    initialize_database(path)
    initialize_database(path)
    store = Store(path)
    assert store.list("journal_entries")[0]["content"] == "Synthetic legacy"
    assert store.list("mood_entries")[0]["recorded_at"] == "2026-10-26T00:00:00+00:00"


def test_database_failure_is_sanitized(tmp_path):
    store = Store(tmp_path / "missing" / "db.sqlite3")
    with pytest.raises(DataError, match="Database unavailable"):
        store.list("journal_entries")
