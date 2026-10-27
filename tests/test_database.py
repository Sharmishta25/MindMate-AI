import sqlite3
import pytest
from mindmate.database import connect, initialize_database


def test_initialization_is_idempotent_and_preserves_data(tmp_path):
    path = tmp_path / "nested" / "test.sqlite3"
    initialize_database(path)
    with connect(path) as db:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert tables == {"mood_entries", "journal_entries", "wellness_activities", "report_metadata", "users", "sessions", "vault_records", "deliveries"}
        assert db.execute("PRAGMA user_version").fetchone()[0] == 4
        db.execute("INSERT INTO mood_entries(entry_date,mood_score) VALUES (?,?)", ("2026-10-27", 3))
    initialize_database(path)
    with connect(path) as db:
        assert db.execute("SELECT mood_score FROM mood_entries").fetchone()[0] == 3
        assert db.execute("SELECT COUNT(*) FROM journal_entries").fetchone()[0] == 0


@pytest.mark.parametrize("sql", [
    "INSERT INTO mood_entries(entry_date,mood_score) VALUES ('2026-10-27',6)",
    "INSERT INTO journal_entries(entry_date,content) VALUES ('2026-10-27',' ')",
    "INSERT INTO wellness_activities(activity_date,activity_type,duration_minutes) VALUES ('2026-10-27','walk',0)",
    "INSERT INTO report_metadata(period_start,period_end) VALUES ('2026-10-28','2026-10-27')",
])
def test_constraints_reject_invalid_data(tmp_path, sql):
    path = tmp_path / "test.sqlite3"
    initialize_database(path)
    with pytest.raises(sqlite3.IntegrityError):
        with connect(path) as db:
            db.execute(sql)
