"""Local weekly snapshots and safe Markdown export; no automatic delivery."""
from datetime import date, datetime, timezone, timedelta
import json
import re
import sqlite3
from mindmate.database import connect
from mindmate.services.core import DataError, day, identifier
from mindmate.analytics.trends import analyze

QUESTIONS = ["What stands out to you in the days you recorded?", "What small, optional wellbeing activity would you like to make space for next week?"]


def week_bounds(anchor):
    selected = date.fromisoformat(day(str(anchor)))
    try:
        start = selected - timedelta(days=selected.weekday())
        return start.isoformat(), (start + timedelta(days=6)).isoformat()
    except OverflowError:
        raise ValueError("Selected week is outside the supported calendar range") from None


class Reports:
    def __init__(self, path):
        self.path = path

    def generate(self, period_start, *, today=None):
        start, end = week_bounds(period_start)
        if str(period_start) != start:
            raise ValueError("Choose the Monday starting the reporting week")
        today = today or datetime.now(timezone.utc).date()
        if date.fromisoformat(start) > today:
            raise ValueError("Cannot generate a report for a future week")
        try:
            with connect(self.path) as db:
                db.execute("BEGIN IMMEDIATE")
                moods = [dict(r) for r in db.execute("SELECT id,entry_date,mood_score,emotion,triggers FROM mood_entries")]
                activities = [dict(r) for r in db.execute("SELECT activity_date,activity_type,completed,helpfulness FROM wellness_activities")]
                evidence = analyze(moods, activities, start, end, today=today)
                snapshot = {"version": 1, "evidence": evidence, "questions": QUESTIONS,
                            "next_steps": ["If useful, keep a brief check-in habit; missing days are okay.", "Consider revisiting an activity you personally rated helpful. Skip anything that does not suit you."]}
                encoded = json.dumps(snapshot, ensure_ascii=False, allow_nan=False)
                existing = db.execute("SELECT id FROM report_metadata WHERE period_start=? AND period_end=? AND report_type='weekly' AND snapshot_json IS NOT NULL", (start, end)).fetchone()
                if existing:
                    report_id = existing[0]
                    db.execute("UPDATE report_metadata SET snapshot_json=?,updated_at=CURRENT_TIMESTAMP,generation_mode='local' WHERE id=?", (encoded, report_id))
                else:
                    report_id = db.execute("INSERT INTO report_metadata(period_start,period_end,snapshot_json,updated_at) VALUES (?,?,?,CURRENT_TIMESTAMP)", (start, end, encoded)).lastrowid
                return report_id
        except sqlite3.Error:
            raise DataError("Unable to generate the report. Existing reports were not replaced. Check database access and retry.") from None

    def list(self):
        try:
            with connect(self.path) as db:
                return [dict(r) for r in db.execute("SELECT id,period_start,period_end,created_at,updated_at FROM report_metadata WHERE snapshot_json IS NOT NULL ORDER BY period_start DESC")]
        except sqlite3.Error:
            raise DataError("Unable to read saved reports. Check database access.") from None

    def get(self, report_id):
        try:
            with connect(self.path) as db:
                row = db.execute("SELECT snapshot_json FROM report_metadata WHERE id=?", (identifier(report_id),)).fetchone()
            if row is None or row[0] is None:
                raise DataError("Saved report is unavailable. Generate a report first.")
            snapshot = json.loads(row[0])
            # Exercise export before rendering so damaged snapshots fail with a safe message.
            export_markdown(snapshot)
            return snapshot
        except (sqlite3.Error, ValueError, TypeError, KeyError, AttributeError):
            raise DataError("Saved report could not be read. Regenerate it from your check-ins.") from None

    def delete(self, report_id):
        try:
            with connect(self.path) as db:
                cursor = db.execute("DELETE FROM report_metadata WHERE id=? AND snapshot_json IS NOT NULL", (identifier(report_id),))
                if cursor.rowcount != 1:
                    raise ValueError("Report no longer exists")
        except sqlite3.Error:
            raise DataError("Unable to delete the report. Check database access.") from None


def _escape(value):
    value = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", " ").replace("\r", " ")
    return re.sub(r"([\\`*_{}\[\]()#+.!|>-])", r"\\\1", value)


def formatted(value):
    return "No data" if value is None else f"{value:.2f}"


def export_markdown(snapshot, narrative=None):
    try:
        if snapshot["version"] != 1:
            raise ValueError()
        e = snapshot["evidence"]
        start, end = day(e["period_start"]), day(e["period_end"])
        lines = ["# MindMate AI weekly wellbeing report", f"Period: {start} to {end} (inclusive UTC)",
                 f"Snapshot as of: {day(e['as_of'])}. Regenerate to include later edits.",
                 "General wellbeing and self-reflection only. No diagnosis, treatment or health prediction.",
                 "## Recorded evidence", f"Completed check-ins: {e['count']}",
                 f"Recorded days: {e['recorded_days']} / {e['days']}; missing days: {e['missing_days']}; coverage: {e['coverage']:.1%}",
                 f"Unrecorded elapsed days: {e['missing_elapsed_days']}; future days: {e['future_days']}.",
                 f"Average mood: {formatted(e['average'])} / 5; median mood: {formatted(e['median'])} / 5.",
                 "Small sample (fewer than five check-ins)." if e["small_sample"] else "At least five check-ins; still descriptive self-reported data.",
                 "This reporting week has ended." if e["period_ended"] else "Ongoing/incomplete week; future days and unrecorded days remain unobserved.",
                 "## Daily mood chart", "Each # represents approximately 0.2 mood points; missing days are gaps. Exact means follow each bar.", "```text"]
        for row in e["daily"]:
            score = row["mean_mood"]
            lines.append(f"{day(row['date'])} | " + ("missing" if score is None else "#" * round(score * 5) + f" {score:.2f} (n={row['check_ins']})"))
        lines += ["```", "## Weekly descriptive values"]
        for row in e["weekly"]:
            lines.append(f"Week starting {day(row['date'])}: mean {formatted(row['average'])}, median {formatted(row['median'])}, n={row['count']}, recorded days={row['recorded_days']}/7. {row['label']}.")
        comparison = e["comparison"]
        lines += ["## Period comparison", comparison["explanation"]]
        if comparison["supported"]:
            lines.append(f"Previous period {comparison['previous_start']} to {comparison['previous_end']}: n={comparison['previous_count']}, coverage={comparison['previous_coverage']:.1%}, average={comparison['previous_average']:.2f}. Difference in average={comparison['average_change']:+.2f} mood points.")
        for title, key in [("User-selected emotions", "emotions"), ("User-reported stressor labels", "triggers")]:
            lines += ["## " + title, "Recurring means recorded on at least two check-ins; no cause or clinical meaning is inferred."]
            lines += [f"- {_escape(x['label'])}: {x['count']} check-ins" + (" (recurring in supplied records)" if x["count"] >= 2 else " (single occurrence)") for x in e[key]] or ["No labels recorded."]
        lines += ["## Activities you rated helpful", f"Completed activity records: {e['activity_count']}. Helpful = self-rated 4 or 5; unrated records are excluded."]
        lines += [f"- {_escape(x['label'])}: {x['count']} helpful records; average helpfulness among these records {x['average_helpfulness']:.2f}/5." for x in e["helpful_activities"]] or ["No activities rated helpful in this period."]
        if narrative:
            lines += ["## Optional evidence narrative", narrative]
        lines += ["## Optional reflection questions"] + ["- " + _escape(x) for x in snapshot["questions"]]
        lines += ["## Optional next steps"] + ["- " + _escape(x) for x in snapshot["next_steps"]]
        lines += ["## How to read this report", e["methods"], ("Local report snapshot. Optional in-app scheduling requires profile consent and a separate running worker; no external delivery." if snapshot.get("scheduling_available") else "Generated on demand. No background scheduling or delivery is implemented in legacy compatibility mode."), "Private local snapshot: exports can contain sensitive user-reported labels. Store and share with care."]
        return "\n\n".join(lines) + "\n"
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
        raise DataError("Unable to export this report. Regenerate it and try again.") from None
