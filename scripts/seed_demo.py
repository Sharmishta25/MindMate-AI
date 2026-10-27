"""Create explicitly synthetic data only in the fixed ignored demo database.

Run from the project root: .\\.venv\\Scripts\\python.exe -m scripts.seed_demo
Never clears or overwrites an existing populated demo database.
"""
from datetime import datetime, timezone, timedelta
from mindmate.config import PROJECT_ROOT
from mindmate.database import initialize_database, connect
from mindmate.services.core import Store

DEMO_PATH = PROJECT_ROOT / "tmp/demo/mindmate-demo.sqlite3"


def seed_demo():
    initialize_database(DEMO_PATH)
    with connect(DEMO_PATH) as db:
        populated = any(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in
                        ("mood_entries", "journal_entries", "wellness_activities", "report_metadata"))
    if populated:
        return False
    today = datetime.now(timezone.utc).date()
    this_monday = today - timedelta(days=today.weekday())
    start = this_monday - timedelta(days=14)
    store = Store(DEMO_PATH)
    scores = [3, 2, 4, 3, 4, 4, 3, 2, 3, 3, 4, 3, 5, 4]
    for offset, score in enumerate(scores):
        entry_date = (start + timedelta(days=offset)).isoformat()
        mood_id = store.save_mood(entry_date, score, max(0, 7-score), ["Calm"] if score >= 3 else ["Tired"],
                                 "Synthetic: deadline" if offset % 3 == 0 else "", "SYNTHETIC example check-in for a portfolio demonstration.",
                                 recorded_at=entry_date + "T18:00:00+00:00")
        if offset in (8, 12):
            store.save_journal(entry_date, "SYNTHETIC: a small pause", "SYNTHETIC ENTRY. I feel calm after a walk. I made time to rest after work today.", mood_id)
        if offset % 2 == 0:
            store.complete_activity(entry_date, "Grounding pause", 3, 4 if score >= 3 else None)
    return True


if __name__ == "__main__":
    print("Created synthetic demo data." if seed_demo() else "Existing demo records kept; no data was overwritten.")
    print("Demo database: tmp/demo/mindmate-demo.sqlite3")
