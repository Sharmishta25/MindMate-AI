"""Validated local CRUD. Never logs user content or raw database exceptions."""
from datetime import date, datetime, timezone
import json
import sqlite3
from mindmate.database import connect

EMOTIONS = ("Calm", "Happy", "Hopeful", "Sad", "Anxious", "Frustrated", "Tired", "Overwhelmed", "Grateful")
TABLES = {"mood_entries", "journal_entries", "wellness_activities"}


class DataError(Exception):
    pass


def text(value, label, maximum, required=False):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text")
    if "\x00" in value:
        raise ValueError(f"{label} cannot contain null characters")
    try:
        value.encode("utf-8")
    except UnicodeError:
        raise ValueError(f"{label} must contain valid Unicode text") from None
    value = value.strip()
    if required and not value:
        raise ValueError(f"{label} cannot be empty")
    if len(value) > maximum:
        raise ValueError(f"{label} must be at most {maximum} characters")
    return value


def integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be a whole number from {low} to {high}")
    return value


def day(value):
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("Use a valid ISO date (YYYY-MM-DD)") from None
    if parsed.isoformat() != value:
        raise ValueError("Use a valid ISO date (YYYY-MM-DD)")
    return value


def identifier(value):
    return integer(value, 1, 2**63 - 1, "Entry ID")


class Store:
    def __init__(self, path):
        self.path = path

    def _execute(self, sql, params=(), *, fetch=False, existing=False):
        try:
            with connect(self.path) as db:
                cursor = db.execute(sql, params)
                if fetch:
                    return [dict(row) for row in cursor.fetchall()]
                if existing and cursor.rowcount != 1:
                    raise ValueError("Entry no longer exists. Refresh the page.")
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise DataError("Unable to save: one check-in per day is allowed; any linked entry must still exist.") from None
        except sqlite3.Error:
            raise DataError("Database unavailable. No change was saved. Retry or check file access.") from None

    def list(self, table):
        if not isinstance(table, str) or table not in TABLES:
            raise ValueError("Unknown record type")
        return self._execute(f"SELECT * FROM {table} ORDER BY id DESC", fetch=True)

    def delete(self, table, entry_id):
        if not isinstance(table, str) or table not in TABLES:
            raise ValueError("Unknown record type")
        self._execute(f"DELETE FROM {table} WHERE id=?", (identifier(entry_id),), existing=True)

    def save_mood(self, entry_date, score, stress, emotions, triggers="", reflection="", recorded_at=None, entry_id=None):
        day(entry_date)
        integer(score, 1, 5, "Mood")
        integer(stress, 0, 10, "Stress")
        if not isinstance(emotions, (list, tuple)) or any(e not in EMOTIONS for e in emotions):
            raise ValueError("Choose emotions from the supplied list")
        triggers = text(triggers, "Triggers", 500)
        reflection = text(reflection, "Reflection", 2000)
        try:
            moment = datetime.fromisoformat(recorded_at) if recorded_at else datetime.now(timezone.utc)
            if moment.tzinfo is None or moment.utcoffset() is None:
                raise ValueError()
            moment = moment.astimezone(timezone.utc)
            if moment.date().isoformat() != entry_date:
                raise ValueError()
        except (TypeError, ValueError, OverflowError):
            raise ValueError("Check-in timestamp must include a timezone and match the selected UTC date") from None
        values = (entry_date, score, stress, json.dumps(list(dict.fromkeys(emotions))), triggers, reflection, moment.isoformat())
        if entry_id is None:
            return self._execute("INSERT INTO mood_entries(entry_date,mood_score,stress_level,emotion,triggers,note,recorded_at) VALUES (?,?,?,?,?,?,?)", values)
        self._execute("UPDATE mood_entries SET entry_date=?,mood_score=?,stress_level=?,emotion=?,triggers=?,note=?,recorded_at=? WHERE id=?", values + (identifier(entry_id),), existing=True)
        return entry_id

    def save_journal(self, entry_date, title, content, mood_entry_id=None, entry_id=None):
        values = (day(entry_date), text(title, "Title", 150), text(content, "Journal", 20000, True),
                  identifier(mood_entry_id) if mood_entry_id is not None else None)
        if entry_id is None:
            return self._execute("INSERT INTO journal_entries(entry_date,title,content,mood_entry_id) VALUES (?,?,?,?)", values)
        self._execute("UPDATE journal_entries SET entry_date=?,title=?,content=?,mood_entry_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", values + (identifier(entry_id),), existing=True)
        return entry_id

    def complete_activity(self, activity_date, activity_type, duration, helpfulness=None):
        from mindmate.services.activities import ACTIVITIES
        if not isinstance(activity_type, str) or activity_type not in ACTIVITIES:
            raise ValueError("Choose an activity from the collection")
        integer(duration, 1, 180, "Duration")
        if helpfulness is not None:
            integer(helpfulness, 1, 5, "Helpfulness")
        return self._execute("INSERT INTO wellness_activities(activity_date,activity_type,duration_minutes,completed,helpfulness) VALUES (?,?,?,1,?)",
                             (day(activity_date), activity_type, duration, helpfulness))
