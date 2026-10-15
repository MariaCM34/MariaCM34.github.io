import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from energy_pulse.pipeline import build, ingest
from energy_pulse.producer import produce


START = datetime(2026, 10, 15, tzinfo=timezone.utc)


def db_rows(db: Path, query: str):
    with sqlite3.connect(db) as conn:
        return conn.execute(query).fetchall()


def write_events(path: Path, events: list[dict]):
    path.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events), encoding="utf-8")


def fixture(tmp_path: Path, slots: int = 12):
    source = tmp_path / "events.jsonl"
    manifest = produce(source, slots=slots)
    db = tmp_path / "energy.sqlite"
    return source, manifest, db


def test_separate_process_source_to_gold_and_lineage(tmp_path):
    source, manifest, db = fixture(tmp_path)
    for args in [
        ["ingest", "--db", str(db), "--source", str(source)],
        ["build", "--db", str(db), "--manifest", str(source.with_suffix(".manifest.json"))],
    ]:
        subprocess.run([sys.executable, "-m", "energy_pulse.cli", *args], check=True, capture_output=True, text=True)
    assert manifest["emitted_events"] == 106  # Independent count: 3 assets × 3 metrics × 12 slots − 2 missing.
    assert db_rows(db, "SELECT COUNT(*) FROM raw_events")[0][0] == 106
    assert db_rows(db, "SELECT COUNT(*) FROM measurements")[0][0] == 106
    assert db_rows(db, "SELECT COUNT(*) FROM asset_hourly")[0][0] == 27  # 3 hours × 3 × 3.
    assert db_rows(db, "SELECT received_samples,expected_samples,quality_status FROM asset_hourly WHERE asset_id='CHILL-C301' AND metric='pressure' AND hour_utc='2026-10-15T00:00:00Z'")[0] == (3, 4, "PARTIAL")
    with sqlite3.connect(db) as conn:
        event_id = conn.execute("SELECT first_event_id FROM incidents").fetchone()[0]
        assert conn.execute("SELECT value FROM measurements WHERE event_id=?", (event_id,)).fetchone()[0] == 84.3
        assert conn.execute("SELECT payload_sha256 FROM raw_events WHERE event_id=?", (event_id,)).fetchone()[0]
        assert conn.execute("SELECT status FROM incidents").fetchone()[0] == "CLOSED"


def test_replay_is_idempotent_and_conflict_is_quarantined(tmp_path):
    source, _, db = fixture(tmp_path)
    first = ingest(db, source)
    build(db, start=START, slots=12)
    ids_before = db_rows(db, "SELECT incident_id FROM incidents ORDER BY incident_id")
    second = ingest(db, source)
    rebuilt = build(db, start=START, slots=12)
    assert first["accepted"] == 106
    assert second["accepted"] == 0 and second["duplicate"] == 106
    assert rebuilt["normalized"] == 0 and rebuilt["affected_hours"] == 0
    assert db_rows(db, "SELECT COUNT(*) FROM measurements")[0][0] == 106
    assert db_rows(db, "SELECT incident_id FROM incidents ORDER BY incident_id") == ids_before
    altered = json.loads(source.read_text(encoding="utf-8").splitlines()[0])
    altered["value"] += 10
    conflict = tmp_path / "conflict.jsonl"
    write_events(conflict, [altered])
    result = ingest(db, conflict)
    assert result["quarantined"] == 1
    assert db_rows(db, "SELECT reason_code FROM quarantine")[-1][0] == "ID_CONFLICT"
    assert db_rows(db, "SELECT COUNT(*) FROM raw_events")[0][0] == 106


def test_invalid_event_contract_reaches_quarantine_without_gold(tmp_path):
    source, _, db = fixture(tmp_path)
    base = json.loads(source.read_text(encoding="utf-8").splitlines()[0])
    bad_unit = {**base, "event_id": "EVT-BAD-UNIT", "unit": "bar"}
    unknown_asset = {**base, "event_id": "EVT-BAD-ASSET", "asset_id": "UNKNOWN-A"}
    malformed = {**base, "event_id": "EVT-BAD-VALUE", "value": float("nan")}
    invalid = tmp_path / "invalid.jsonl"
    write_events(invalid, [bad_unit, unknown_asset, malformed])
    result = ingest(db, invalid)
    build(db, start=START, slots=1)
    assert result["accepted"] == 0 and result["quarantined"] == 3
    assert set(code for (code,) in db_rows(db, "SELECT reason_code FROM quarantine")) == {"UNIT_MISMATCH", "UNKNOWN_ASSET", "CONTRACT_INVALID"}
    assert db_rows(db, "SELECT COUNT(*) FROM measurements")[0][0] == 0
    assert db_rows(db, "SELECT COUNT(*) FROM asset_hourly WHERE quality_status='NO_DATA'")[0][0] == 9
    assert db_rows(db, "SELECT avg_value FROM asset_hourly LIMIT 1")[0][0] is None


def test_within_watermark_late_event_repairs_only_affected_hour(tmp_path):
    source, _, db = fixture(tmp_path)
    ingest(db, source)
    build(db, start=START, slots=12)
    late = json.loads(source.read_text(encoding="utf-8").splitlines()[0])
    late.update(event_id="EVT-CHILL-C301-20261015T0045Z-PRESSURE", asset_id="CHILL-C301",
                site_id="SYNTHETIC-SITE-02", metric="pressure", value=57.5, unit="bar",
                observed_at_utc="2026-10-15T00:45:00Z")
    late_path = tmp_path / "late.jsonl"
    write_events(late_path, [late])
    assert ingest(db, late_path)["accepted"] == 1
    result = build(db, start=START, slots=12)
    assert result["normalized"] == 1 and result["affected_hours"] == 1
    assert db_rows(db, "SELECT received_samples,quality_status FROM asset_hourly WHERE asset_id='CHILL-C301' AND metric='pressure' AND hour_utc='2026-10-15T00:00:00Z'")[0] == (4, "COMPLETE")


def test_older_than_watermark_requires_review(tmp_path):
    source, _, db = fixture(tmp_path, slots=96 * 3)
    ingest(db, source)
    build(db, start=START, slots=96 * 3)
    late = json.loads(source.read_text(encoding="utf-8").splitlines()[0])
    late.update(event_id="EVT-CHILL-C301-20261015T0045Z-PRESSURE", asset_id="CHILL-C301",
                site_id="SYNTHETIC-SITE-02", metric="pressure", value=57.5, unit="bar",
                observed_at_utc="2026-10-15T00:45:00Z")
    late_path = tmp_path / "too_late.jsonl"
    write_events(late_path, [late])
    ingest(db, late_path)
    result = build(db, start=START, slots=96 * 3)
    assert result["late_review"] == 1 and result["normalized"] == 0
    assert db_rows(db, "SELECT reason_code FROM quarantine ORDER BY quarantine_id DESC LIMIT 1")[0][0] == "LATE_REVIEW"
    assert db_rows(db, "SELECT received_samples FROM asset_hourly WHERE asset_id='CHILL-C301' AND metric='pressure' AND hour_utc='2026-10-15T00:00:00Z'")[0][0] == 3
