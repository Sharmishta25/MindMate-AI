"""Explainable descriptive evidence. No sentiment scoring or clinical inference."""
from collections import Counter, defaultdict
from datetime import date, datetime, timezone, timedelta
import json
import re
import statistics
from mindmate.services.core import day, EMOTIONS

METHODS = (
    "Average = sum of recorded mood scores / check-in count. Median = middle sorted score (mean of the middle pair for even counts). "
    "Coverage = distinct recorded dates / calendar days in the inclusive UTC range. Missing days are not scored as zero or imputed; future-dated records after the as-of UTC date are excluded. "
    "Daily/weekly means use only recorded check-ins; weeks start Monday. A small sample means fewer than five check-ins. "
    "Emotion counts are check-ins selecting that emotion, at most once per entry. Triggers are user-entered labels split on commas, semicolons or newlines, trimmed and case-folded, at most once per entry; no semantic grouping. "
    "Helpful activities are completed records rated 4 or 5 out of 5; unrated activities are excluded, not treated as unhelpful. "
    "Period comparison requires equal-length, non-overlapping consecutive periods of at least seven days, both ended before today UTC, with at least five check-ins and 70% date coverage in each. This is a display rule, not a statistical significance test. "
    "Associations and changes do not establish causation. No health condition is inferred from these records."
)


def _period(start, end):
    a, b = date.fromisoformat(day(str(start))), date.fromisoformat(day(str(end)))
    if a > b:
        raise ValueError("Start date must be on or before end date")
    return a, b


def _stats(rows):
    scores = [r["mood_score"] for r in rows]
    return {"count": len(scores), "average": statistics.mean(scores) if scores else None,
            "median": statistics.median(scores) if scores else None}


def _frequencies(counter):
    return [{"label": k, "count": v} for k, v in sorted(counter.items(), key=lambda x: (-x[1], x[0]))]


def analyze(rows, activities, start, end, *, today=None):
    a, b = _period(start, end)
    today = today or datetime.now(timezone.utc).date()
    selected = sorted([r for r in rows if a.isoformat() <= r["entry_date"] <= min(b, today).isoformat()], key=lambda r: (r["entry_date"], r["id"]))
    days = (b - a).days + 1
    if a.toordinal() <= days + 7 or b.toordinal() > date.max.toordinal() - 7:
        raise ValueError("Selected dates are too close to the calendar boundary")
    if days > 3660:
        raise ValueError("Select a period of at most 3,660 days")
    result = {"period_start": a.isoformat(), "period_end": b.isoformat(), "as_of": today.isoformat(), **_stats(selected)}
    observed = {r["entry_date"] for r in selected}
    future_days = max(0, (b - max(today, a - timedelta(days=1))).days)
    result.update(future_days=future_days, missing_elapsed_days=days - future_days - len(observed), days=days, recorded_days=len(observed), missing_days=days - len(observed), coverage=len(observed) / days,
                  small_sample=len(selected) < 5, recent=selected[-1]["mood_score"] if selected else None,
                  period_ended=b < today)
    buckets = defaultdict(list)
    for row in selected:
        buckets[row["entry_date"]].append(row["mood_score"])
    daily = []
    cursor = a
    while cursor <= b:
        scores = buckets[cursor.isoformat()]
        daily.append({"date": cursor.isoformat(), "mean_mood": statistics.mean(scores) if scores else None, "check_ins": len(scores)})
        cursor += timedelta(days=1)
    weekly = []
    week = a - timedelta(days=a.weekday())
    while week <= b:
        last = week + timedelta(days=6)
        members = [r for r in selected if week.isoformat() <= r["entry_date"] <= last.isoformat()]
        recorded = len({r["entry_date"] for r in members})
        complete = a <= week and b >= last and last < today and recorded == 7
        weekly.append({"date": week.isoformat(), "period_end": last.isoformat(), **_stats(members),
                       "recorded_days": recorded, "incomplete": not complete, "small_sample": len(members) < 5,
                       "label": ("Complete week" if complete else "Incomplete week (range boundary, missing days, or ongoing)") + ("; small sample (fewer than five check-ins)" if len(members) < 5 else "")})
        week += timedelta(days=7)
    emotions, triggers = Counter(), Counter()
    for row in selected:
        raw = row.get("emotion", "")
        try:
            values = json.loads(raw)
            if not isinstance(values, list):
                values = []
        except (ValueError, TypeError):
            values = [raw]
        emotions.update({e for e in values if isinstance(e, str) and e in EMOTIONS})
        triggers.update({v.strip().casefold() for v in re.split(r"[,;\n]", row.get("triggers", "") or "") if v.strip()})
    helpful = defaultdict(list)
    activity_count = 0
    for row in activities:
        if a.isoformat() <= row["activity_date"] <= min(b, today).isoformat() and row.get("completed") == 1:
            activity_count += 1
            if row.get("helpfulness") in (4, 5):
                helpful[row["activity_type"]].append(row["helpfulness"])
    result.update(daily=daily, weekly=weekly, emotions=_frequencies(emotions), triggers=_frequencies(triggers),
                  activity_count=activity_count, helpful_activities=[{"label": k, "count": len(v), "average_helpfulness": statistics.mean(v)} for k, v in sorted(helpful.items())],
                  daily_trend_supported=len(observed) >= 2,
                  weekly_trend_supported=sum(w["count"] >= 3 for w in weekly) >= 2)
    prev_end = a - timedelta(days=1)
    prev_start = a - timedelta(days=days)
    previous = [r for r in rows if prev_start.isoformat() <= r["entry_date"] <= prev_end.isoformat()]
    previous_stats = _stats(previous)
    previous_coverage = len({r["entry_date"] for r in previous}) / days
    eligible = days >= 7 and b < today and len(selected) >= 5 and len(previous) >= 5 and result["coverage"] >= .7 and previous_coverage >= .7
    result["comparison"] = {"supported": eligible, "previous_start": prev_start.isoformat(), "previous_end": prev_end.isoformat(),
                            "previous_count": previous_stats["count"], "previous_coverage": previous_coverage,
                            "previous_average": previous_stats["average"] if eligible else None,
                            "average_change": result["average"] - previous_stats["average"] if eligible else None,
                            "explanation": "Descriptive difference between averages; not evidence of significance or cause." if eligible else "Comparison withheld: requires ended periods of at least seven days, five check-ins and 70% coverage in both."}
    result["methods"] = METHODS
    return result
