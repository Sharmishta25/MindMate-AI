"""User-initiated logical deletion of this application's records only."""
import sqlite3
from mindmate.database import connect
from mindmate.services.core import DataError

RESET_PHRASE = "DELETE ALL MY DATA"


def reset_all_data(path, confirmation):
    if confirmation != RESET_PHRASE:
        raise ValueError("Type DELETE ALL MY DATA exactly to confirm the reset")
    try:
        with connect(path) as db:
            db.execute("BEGIN IMMEDIATE")
            # Includes legacy metadata and snapshots; schema/configuration remain intact.
            for table in ("journal_entries", "mood_entries", "wellness_activities", "report_metadata"):
                db.execute(f"DELETE FROM {table}")
    except sqlite3.Error:
        raise DataError("Unable to reset records. The transaction was rolled back; check database access.") from None
