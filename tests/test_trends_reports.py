"""Deterministic synthetic analytics and persistence fixtures; no personal data."""
from datetime import date, timedelta
import json
import sqlite3
from unittest.mock import Mock
import pytest
from mindmate.analytics.trends import analyze
from mindmate.database import connect, initialize_database, SCHEMA
from mindmate.services.core import Store, DataError
from mindmate.services.reports import Reports, week_bounds, export_markdown
from mindmate.ai.report_narrative import narrative
from mindmate.ai.report_prompts import payload
from mindmate.ai.provider import ProviderError
from mindmate.config import load_settings

TODAY = date(2026, 10, 27)


def synthetic_rows():
    rows = []
    for i, score in enumerate([2] * 7 + [1, 2, 3, 4, 5, 4, 2]):
        d = (date(2026, 10, 12) + timedelta(days=i)).isoformat()
        rows.append({"id": i + 1, "entry_date": d, "mood_score": score,
                     "emotion": json.dumps(["Calm", "Calm"] if i % 2 == 0 else ["Sad"]),
                     "triggers": "Work, work; Noise" if i >= 7 else ""})
    return rows


@pytest.fixture
def stored(tmp_path):
    path = tmp_path / "reports.sqlite3"
    initialize_database(path)
    store = Store(path)
    for r in synthetic_rows():
        store.save_mood(r["entry_date"], r["mood_score"], 2, list(set(json.loads(r["emotion"]))), r["triggers"], recorded_at=r["entry_date"] + "T12:00:00Z")
    store.complete_activity("2026-10-20", "Grounding pause", 3, 5)
    store.complete_activity("2026-10-21", "Grounding pause", 3, 3)
    store.complete_activity("2026-10-21", "Reflective journaling", 5)
    return path


def test_known_statistics_and_counts():
    e = analyze(synthetic_rows(), [], "2026-10-19", "2026-10-25", today=TODAY)
    assert (e["count"], e["average"], e["median"], e["recent"]) == (7, 3, 3, 2)
    assert e["missing_days"] == 0 and e["coverage"] == 1
    assert e["comparison"]["supported"] and e["comparison"]["average_change"] == 1
    assert e["comparison"]["previous_average"] == 2
    assert e["emotions"] == [{"label": "Sad", "count": 4}, {"label": "Calm", "count": 3}]
    assert e["triggers"] == [{"label": "noise", "count": 7}, {"label": "work", "count": 7}]
    assert not e["weekly"][0]["incomplete"]
    assert e["daily_trend_supported"] and not e["weekly_trend_supported"]
    all_data = analyze(synthetic_rows(), [], "2026-10-12", "2026-10-25", today=TODAY)
    assert all_data["weekly_trend_supported"]


def test_even_median_and_missing_gaps():
    e = analyze(synthetic_rows(), [], "2026-10-19", "2026-10-20", today=TODAY)
    assert e["average"] == 1.5 and e["median"] == 1.5 and e["small_sample"]
    assert not e["comparison"]["supported"]
    e = analyze(synthetic_rows()[::2], [], "2026-10-19", "2026-10-25", today=TODAY)
    assert e["missing_days"] == 4 and e["weekly"][0]["incomplete"]
    assert e["weekly"][0]["small_sample"] and "small sample" in e["weekly"][0]["label"]
    assert e["daily"][0]["mean_mood"] is None
    assert e["daily"][1]["mean_mood"] == 2


def test_empty_and_single_entry():
    e = analyze([], [], "2026-10-19", "2026-10-25", today=TODAY)
    assert e["average"] is None and e["median"] is None and e["count"] == 0
    assert e["missing_days"] == 7 and not e["comparison"]["supported"]
    one = analyze(synthetic_rows()[-1:], [], "2026-10-19", "2026-10-25", today=TODAY)
    assert one["median"] == 2 and not one["daily_trend_supported"]


def test_incomplete_week_and_future_records_excluded():
    e = analyze(synthetic_rows(), [], "2026-10-19", "2026-10-25", today=date(2026, 10, 21))
    assert e["count"] == 3 and e["future_days"] == 4 and e["missing_elapsed_days"] == 0
    assert not e["period_ended"] and e["weekly"][0]["incomplete"]
    assert not e["comparison"]["supported"]


def test_comparison_threshold_and_partial_ranges():
    rows = synthetic_rows()
    five_each = rows[:5] + rows[7:12]
    e = analyze(five_each, [], "2026-10-19", "2026-10-25", today=TODAY)
    assert e["comparison"]["supported"]
    e = analyze(rows[:4] + rows[7:], [], "2026-10-19", "2026-10-25", today=TODAY)
    assert not e["comparison"]["supported"]
    e = analyze(rows, [], "2026-10-20", "2026-10-25", today=TODAY)
    assert not e["comparison"]["supported"] and e["weekly"][0]["incomplete"]


@pytest.mark.parametrize("anchor,expected", [("2026-10-25", ("2026-10-19", "2026-10-25")), ("2025-01-01", ("2024-12-30", "2025-01-05")), ("2024-02-29", ("2024-02-26", "2024-03-03"))])
def test_week_boundaries(anchor, expected):
    assert week_bounds(anchor) == expected


@pytest.mark.parametrize("start,end", [("2026-10-25", "2026-10-19"), ("2026-02-30", "2026-03-01"), ("2000-01-01", "2026-01-01")])
def test_invalid_periods(start, end):
    with pytest.raises(ValueError):
        analyze([], [], start, end, today=TODAY)


def test_report_snapshot_refresh_export_and_delete(stored):
    reports = Reports(stored)
    rid = reports.generate("2026-10-19", today=TODAY)
    report = reports.get(rid)
    e = report["evidence"]
    assert e["average"] == 3 and e["activity_count"] == 3
    assert e["helpful_activities"] == [{"label": "Grounding pause", "count": 1, "average_helpfulness": 5}]
    md = export_markdown(report)
    assert "Completed check-ins: 7" in md and "median mood: 3.00" in md
    assert "2026-10-19" in md and "```text" in md
    assert "No background scheduling" in md
    Store(stored).delete("mood_entries", 8)
    assert Reports(stored).get(rid)["evidence"]["count"] == 7  # Snapshot survives source edits/reopen.
    assert reports.generate("2026-10-19", today=TODAY) == rid
    assert len(reports.list()) == 1 and reports.get(rid)["evidence"]["count"] == 6
    reports.delete(rid)
    assert not reports.list()


def test_empty_report_and_missing_report(tmp_path):
    path = tmp_path / "empty.sqlite3"
    initialize_database(path)
    reports = Reports(path)
    rid = reports.generate("2026-10-19", today=TODAY)
    assert reports.get(rid)["evidence"]["count"] == 0
    assert "No data" in export_markdown(reports.get(rid))
    with pytest.raises(DataError):
        reports.get(999)


def test_invalid_generation_and_export(stored):
    reports = Reports(stored)
    with pytest.raises(ValueError):
        reports.generate("2026-10-20", today=TODAY)
    with pytest.raises(ValueError):
        reports.generate("2026-11-02", today=TODAY)
    with pytest.raises(DataError):
        export_markdown({"version": 999})
    rid = reports.generate("2026-10-19", today=TODAY)
    with connect(stored) as db:
        db.execute("UPDATE report_metadata SET snapshot_json=? WHERE id=?", ('{"version":1}', rid))
    with pytest.raises(DataError):
        reports.get(rid)


def test_export_escapes_user_labels(stored):
    with connect(stored) as db:
        db.execute("UPDATE mood_entries SET triggers=? WHERE entry_date=?", ("<script>alert(1)</script> [click](https://example.com)", "2026-10-19"))
    reports = Reports(stored)
    text = export_markdown(reports.get(reports.generate("2026-10-19", today=TODAY)))
    assert "<script>" not in text and "[click](" not in text


def test_storage_error_does_not_leak(stored, tmp_path):
    with pytest.raises(DataError, match="Unable to generate"):
        Reports(tmp_path / "missing" / "reports.sqlite3").generate("2026-10-19", today=TODAY)


def test_duplicate_legacy_metadata_is_preserved(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    with connect(path) as db:
        db.executescript(SCHEMA)
        for _ in range(2):
            db.execute("INSERT INTO report_metadata(period_start,period_end) VALUES ('2026-10-19','2026-10-25')")
        db.execute("PRAGMA user_version=1")
    initialize_database(path)
    initialize_database(path)
    rid = Reports(path).generate("2026-10-19", today=TODAY)
    assert Reports(path).generate("2026-10-19", today=TODAY) == rid
    with connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM report_metadata").fetchone()[0] == 3
        assert db.execute("PRAGMA user_version").fetchone()[0] == 4


def test_narrative_uses_only_validated_engine_numbers(stored):
    reports = Reports(stored)
    e = reports.get(reports.generate("2026-10-19", today=TODAY))["evidence"]
    settings = load_settings({"MINDMATE_LLM_ENABLED": "true", "MINDMATE_LLM_API_KEY": "synthetic", "MINDMATE_LLM_MODEL": "synthetic"})
    provider = Mock()
    provider.generate_report.return_value = {"focus": ["mood", "coverage"]}
    result = narrative(e, settings, consent=True, provider=provider)
    assert result["source"].startswith("LLM-selected") and "3.00" in result["text"]
    for output in [{"focus": ["mood"], "average": 99}, {"focus": ["diagnosis"]}, {"focus": []}, {"focus": ["mood", "mood"]}]:
        provider.generate_report.return_value = output
        fallback = narrative(e, settings, consent=True, provider=provider)
        assert fallback["reason"] == "invalid_output" and "99" not in fallback["text"]
    provider.generate_report.side_effect = ProviderError("timeout")
    assert narrative(e, settings, consent=True, provider=provider)["reason"] == "timeout"
    provider.reset_mock()
    assert narrative(e, settings, provider=provider)["source"].startswith("Rule-based")
    provider.generate_report.assert_not_called()
    assert narrative(e, load_settings({}), consent=True)["reason"] == "missing_configuration"
    serialized = json.dumps(payload(e))
    assert "work" not in serialized and "noise" not in serialized and "Grounding" not in serialized


def test_narrative_rejects_unavailable_section():
    e = analyze([], [], "2026-10-19", "2026-10-25", today=TODAY)
    settings = load_settings({"MINDMATE_LLM_ENABLED": "true", "MINDMATE_LLM_API_KEY": "synthetic", "MINDMATE_LLM_MODEL": "synthetic"})
    provider = Mock()
    provider.generate_report.return_value = {"focus": ["mood"]}
    result = narrative(e, settings, consent=True, provider=provider)
    assert result["reason"] == "invalid_output" and result["focus"] == ["coverage"]


def test_failed_refresh_rolls_back_existing_snapshot(stored):
    reports = Reports(stored)
    rid = reports.generate("2026-10-19", today=TODAY)
    before = reports.get(rid)
    Store(stored).delete("mood_entries", 8)
    with connect(stored) as db:
        db.execute("CREATE TRIGGER synthetic_block_update BEFORE UPDATE ON report_metadata BEGIN SELECT RAISE(ABORT,'Synthetic test failure'); END")
    with pytest.raises(DataError):
        reports.generate("2026-10-19", today=TODAY)
    assert reports.get(rid) == before


def test_v2_upgrade_preserves_metadata_and_moods(tmp_path):
    path = tmp_path / "v2.sqlite3"
    initialize_database(path)
    store = Store(path)
    mid = store.save_mood("2026-10-19", 4, 2, ["Calm"], recorded_at="2026-10-19T12:00:00Z")
    with connect(path) as db:
        db.execute("DROP INDEX idx_report_snapshot_period")
        db.execute("ALTER TABLE report_metadata DROP COLUMN snapshot_json")
        db.execute("ALTER TABLE report_metadata DROP COLUMN updated_at")
        db.execute("INSERT INTO report_metadata(period_start,period_end) VALUES ('2026-10-19','2026-10-25')")
        db.execute("PRAGMA user_version=2")
    initialize_database(path)
    assert Store(path).list("mood_entries")[0]["id"] == mid
    with connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM report_metadata").fetchone()[0] == 1
    assert Reports(path).generate("2026-10-19", today=TODAY)


def test_concurrent_generation_does_not_duplicate(stored):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as executor:
        ids = list(executor.map(lambda _: Reports(stored).generate("2026-10-19", today=TODAY), range(2)))
    assert ids[0] == ids[1] and len(Reports(stored).list()) == 1


def test_report_provider_uses_aggregate_only(monkeypatch):
    from mindmate.ai.provider import AnthropicProvider
    from mindmate.ai.report_prompts import SCHEMA, SYSTEM
    e = analyze(synthetic_rows(), [], "2026-10-19", "2026-10-25", today=TODAY)
    settings = load_settings({"MINDMATE_LLM_ENABLED": "true", "MINDMATE_LLM_API_KEY": "synthetic", "MINDMATE_LLM_MODEL": "synthetic"})
    request = Mock(return_value={"focus": ["coverage"]})
    monkeypatch.setattr(AnthropicProvider, "_request", request)
    assert AnthropicProvider(settings).generate_report(e) == {"focus": ["coverage"]}
    system, user, schema = request.call_args.args
    assert system == SYSTEM and schema == SCHEMA
    assert json.loads(user) == payload(e)


def test_calendar_boundary_is_rejected_cleanly():
    with pytest.raises(ValueError):
        analyze([], [], "0001-01-01", "0001-01-07", today=TODAY)
    with pytest.raises(ValueError):
        week_bounds("9999-12-31")
