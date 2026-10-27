"""SQLite schema version 4. No journal content is logged or seeded."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS mood_entries (
    id INTEGER PRIMARY KEY,
    entry_date TEXT NOT NULL UNIQUE,
    mood_score INTEGER NOT NULL CHECK (mood_score BETWEEN 1 AND 5),
    emotion TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY,
    entry_date TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL CHECK (length(trim(content)) > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS wellness_activities (
    id INTEGER PRIMARY KEY,
    activity_date TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    duration_minutes INTEGER CHECK (duration_minutes > 0),
    completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS report_metadata (
    id INTEGER PRIMARY KEY,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL CHECK (period_end >= period_start),
    report_type TEXT NOT NULL DEFAULT 'weekly' CHECK (report_type = 'weekly'),
    generation_mode TEXT NOT NULL DEFAULT 'local' CHECK (generation_mode IN ('local', 'llm')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_activity_date ON wellness_activities(activity_date);
"""


@contextmanager
def connect(database_path: Path):
    connection = sqlite3.connect(str(database_path), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA secure_delete = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database(database_path: Path) -> None:
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(database_path) as connection:
        if connection.execute("PRAGMA user_version").fetchone()[0] > 4:
            raise ValueError("Database schema is newer than this application supports")
        connection.executescript(SCHEMA)
        connection.execute("BEGIN IMMEDIATE")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version > 4:
            raise ValueError("Database schema is newer than this application supports")
        if version < 2:
            connection.execute("ALTER TABLE mood_entries ADD COLUMN stress_level INTEGER CHECK (stress_level BETWEEN 0 AND 10)")
            connection.execute("ALTER TABLE mood_entries ADD COLUMN triggers TEXT NOT NULL DEFAULT ''")
            connection.execute("ALTER TABLE mood_entries ADD COLUMN recorded_at TEXT")
            connection.execute("UPDATE mood_entries SET recorded_at = entry_date || 'T00:00:00+00:00'")
            connection.execute("ALTER TABLE journal_entries ADD COLUMN mood_entry_id INTEGER REFERENCES mood_entries(id) ON DELETE SET NULL")
            connection.execute("ALTER TABLE wellness_activities ADD COLUMN helpfulness INTEGER CHECK (helpfulness BETWEEN 1 AND 5)")
        if version < 3:
            connection.execute("ALTER TABLE report_metadata ADD COLUMN snapshot_json TEXT")
            connection.execute("ALTER TABLE report_metadata ADD COLUMN updated_at TEXT")
            # Legacy metadata rows remain intact. Only new full snapshots are unique.
            connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_report_snapshot_period ON report_metadata(period_start,period_end,report_type) WHERE snapshot_json IS NOT NULL")
        if version < 4:
            for statement in ACCOUNT_SCHEMA:
                connection.execute(statement)
        connection.execute("PRAGMA user_version = 4")


ACCOUNT_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, recovery_hash TEXT NOT NULL, failures INTEGER NOT NULL DEFAULT 0, locked_until REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, expires_at REAL NOT NULL)",
    "CREATE TABLE IF NOT EXISTS vault_records (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, kind TEXT NOT NULL, event_date TEXT NOT NULL, ciphertext TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_vault_daily ON vault_records(user_id,kind,event_date) WHERE kind IN ('mood','lifestyle','report','preferences','schedule')",
    "CREATE INDEX IF NOT EXISTS idx_vault_owner ON vault_records(user_id,kind,event_date)",
    "CREATE TABLE IF NOT EXISTS deliveries (user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, occurrence TEXT NOT NULL, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, updated_at REAL NOT NULL, PRIMARY KEY(user_id,occurrence))",
)
