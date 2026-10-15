"""SQLite Bronze/Silver/Gold processing with explicit run and failure records."""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import ValidationError

from .contracts import ASSETS, CADENCE_MINUTES, LATENESS_HOURS, RULES, UNITS, TelemetryEvent, is_breach


ROOT = Path(__file__).resolve().parents[2]
LOG = logging.getLogger("energy_pulse")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def migrate(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.executescript((ROOT / "migrations" / "001_init.sql").read_text(encoding="utf-8"))


def _start_run(conn: sqlite3.Connection, stage: str, source_sha: str | None = None) -> str:
    run_id = f"{stage.lower()}-{uuid.uuid4().hex[:16]}"
    conn.execute(
        "INSERT INTO pipeline_runs(run_id,stage,started_at_utc,source_sha256,status) VALUES(?,?,?,?,?)",
        (run_id, stage, utc_now(), source_sha, "RUNNING"),
    )
    conn.commit()
    return run_id


def _finish_run(conn: sqlite3.Connection, run_id: str, status: str, **counts: int | str) -> None:
    allowed = {"accepted", "duplicate", "quarantined", "output_count", "error"}
    if set(counts) - allowed:
        raise ValueError("invalid_run_field")
    fields = ["finished_at_utc=?", "status=?"] + [f"{key}=?" for key in counts]
    values = [utc_now(), status, *counts.values(), run_id]
    conn.execute(f"UPDATE pipeline_runs SET {', '.join(fields)} WHERE run_id=?", values)
    conn.commit()


def _reason(exc: Exception) -> str:
    details = str(exc)
    for token, code in [
        ("metric_unit_mismatch", "UNIT_MISMATCH"),
        ("unknown_asset", "UNKNOWN_ASSET"),
        ("value_not_finite", "NONFINITE_VALUE"),
        ("observed_at_must_be_utc", "NON_UTC_TIME"),
        ("observed_at_off_cadence", "OFF_CADENCE"),
    ]:
        if token in details:
            return code
    return "CONTRACT_INVALID"


def _quarantine(conn: sqlite3.Connection, run_id: str, raw_line: str, event_id: str | None, reason: str) -> None:
    conn.execute(
        "INSERT INTO quarantine(event_id,raw_line,reason_code,ingested_at_utc,ingest_run_id) VALUES(?,?,?,?,?)",
        (event_id, raw_line, reason, utc_now(), run_id),
    )


def ingest(db_path: Path, source: Path) -> dict:
    """Commit an input file atomically. Re-running the same file is safe."""
    if not source.is_file():
        raise FileNotFoundError(source)
    migrate(db_path)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    with connect(db_path) as conn:
        run_id = _start_run(conn, "INGEST", source_sha)
        accepted = duplicate = quarantined = 0
        try:
            conn.execute("BEGIN")
            for raw_line in source.read_text(encoding="utf-8").splitlines():
                if not raw_line.strip():
                    continue
                event_id = None
                try:
                    data = json.loads(raw_line, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))
                    if isinstance(data, dict):
                        event_id = str(data.get("event_id", "")) or None
                    event = TelemetryEvent.model_validate_json(raw_line)
                except (ValueError, TypeError, ValidationError) as exc:
                    _quarantine(conn, run_id, raw_line, event_id, _reason(exc))
                    quarantined += 1
                    continue
                canonical = json.dumps(event.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
                payload_sha = hashlib.sha256(canonical.encode()).hexdigest()
                prior = conn.execute("SELECT payload_sha256 FROM raw_events WHERE event_id=?", (event.event_id,)).fetchone()
                if prior:
                    if prior["payload_sha256"] == payload_sha:
                        duplicate += 1
                    else:
                        _quarantine(conn, run_id, raw_line, event.event_id, "ID_CONFLICT")
                        quarantined += 1
                    continue
                try:
                    conn.execute(
                        """INSERT INTO raw_events(event_id,source_id,asset_id,site_id,observed_at_utc,metric,
                           payload_json,payload_sha256,ingested_at_utc,ingest_run_id)
                           VALUES(?,?,?,?,?,?,?,?,?,?)""",
                        (event.event_id, event.source_id, event.asset_id, event.site_id,
                         event.observed_at_utc.isoformat().replace("+00:00", "Z"), event.metric,
                         canonical, payload_sha, utc_now(), run_id),
                    )
                    accepted += 1
                except sqlite3.IntegrityError:
                    _quarantine(conn, run_id, raw_line, event.event_id, "NATURAL_KEY_CONFLICT")
                    quarantined += 1
            conn.commit()
            _finish_run(conn, run_id, "SUCCESS", accepted=accepted, duplicate=duplicate, quarantined=quarantined)
        except Exception as exc:
            conn.rollback()
            _finish_run(conn, run_id, "FAILED", error=type(exc).__name__)
            raise
    result = {"run_id": run_id, "source_sha256": source_sha, "accepted": accepted,
              "duplicate": duplicate, "quarantined": quarantined}
    LOG.info(json.dumps({"stage": "ingest", **result}))
    return result


def _incident_rows(conn: sqlite3.Connection, run_id: str) -> int:
    """Recompute deterministic episodes from persisted good measurements."""
    conn.execute("DELETE FROM incident_transitions")
    conn.execute("DELETE FROM incidents")
    count = 0
    step = timedelta(minutes=CADENCE_MINUTES)
    for asset_id in ASSETS:
        for metric in UNITS:
            rows = conn.execute(
                """SELECT event_id,observed_at_utc,value FROM measurements
                   WHERE asset_id=? AND metric=? AND source_quality='GOOD'
                   ORDER BY observed_at_utc,event_id""", (asset_id, metric)
            ).fetchall()
            episode = None

            def save(current: dict, closed_at: str | None) -> None:
                nonlocal count
                rule = RULES[metric]
                incident_id = "INC-" + hashlib.sha256(
                    f"{asset_id}|{metric}|{rule['version']}|{current['opened']}".encode()
                ).hexdigest()[:16].upper()
                conn.execute(
                    """INSERT INTO incidents VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (incident_id, asset_id, metric, current["opened"], closed_at,
                     "CLOSED" if closed_at else "OPEN", rule["version"], rule["threshold"],
                     rule["operator"], current["first_event"], current["last_event"], run_id),
                )
                conn.execute("INSERT INTO incident_transitions VALUES(?,?,?,?,?)",
                             (incident_id, "OPEN", current["opened"], current["first_event"], rule["version"]))
                if closed_at:
                    conn.execute("INSERT INTO incident_transitions VALUES(?,?,?,?,?)",
                                 (incident_id, "CLOSED", closed_at, current["last_event"], rule["version"]))
                count += 1

            for row in rows:
                observed = datetime.fromisoformat(row["observed_at_utc"].replace("Z", "+00:00"))
                breach = is_breach(metric, row["value"])
                if episode and observed - episode["last_time"] != step:
                    save(episode, (episode["last_time"] + step).isoformat().replace("+00:00", "Z"))
                    episode = None
                if breach:
                    if episode is None:
                        episode = {"opened": row["observed_at_utc"], "first_event": row["event_id"]}
                    episode["last_event"] = row["event_id"]
                    episode["last_time"] = observed
                elif episode:
                    save(episode, row["observed_at_utc"])
                    episode = None
            if episode:
                save(episode, None)
    return count


def build(db_path: Path, *, start: datetime, slots: int) -> dict:
    """Materialize expected slots and process only new raw rows; rebuild affected Gold hours."""
    if slots < 1 or slots > 96 * 30 or start.tzinfo is None or start.utcoffset() != timedelta(0):
        raise ValueError("invalid_window")
    migrate(db_path)
    with connect(db_path) as conn:
        run_id = _start_run(conn, "BUILD")
        normalized = late_review = affected_count = incident_count = 0
        try:
            conn.execute("BEGIN")
            conn.execute("CREATE TEMP TABLE affected_hours(hour_utc TEXT PRIMARY KEY)")
            for slot in range(slots):
                observed = (start + timedelta(minutes=CADENCE_MINUTES * slot)).isoformat().replace("+00:00", "Z")
                hour = observed[:13] + ":00:00Z"
                for asset_id in ASSETS:
                    for metric in UNITS:
                        before = conn.total_changes
                        conn.execute("INSERT OR IGNORE INTO expected_slots VALUES(?,?,?)", (asset_id, metric, observed))
                        if conn.total_changes > before:
                            conn.execute("INSERT OR IGNORE INTO affected_hours VALUES(?)", (hour,))
            prior_max = conn.execute("SELECT MAX(observed_at_utc) FROM measurements").fetchone()[0]
            watermark = (datetime.fromisoformat(prior_max.replace("Z", "+00:00")) - timedelta(hours=LATENESS_HOURS)) if prior_max else None
            rows = conn.execute("SELECT * FROM raw_events WHERE processed=0 ORDER BY observed_at_utc,event_id").fetchall()
            for row in rows:
                event = TelemetryEvent.model_validate_json(row["payload_json"])
                if watermark and event.observed_at_utc < watermark:
                    _quarantine(conn, row["ingest_run_id"], row["payload_json"], event.event_id, "LATE_REVIEW")
                    late_review += 1
                else:
                    conn.execute(
                        """INSERT OR IGNORE INTO measurements VALUES(?,?,?,?,?,?,?,?,?)""",
                        (event.event_id, event.asset_id, event.site_id, row["observed_at_utc"],
                         event.metric, event.value, event.unit, event.quality, run_id),
                    )
                    conn.execute("INSERT OR IGNORE INTO affected_hours VALUES(?)", (row["observed_at_utc"][:13] + ":00:00Z",))
                    normalized += 1
                conn.execute("UPDATE raw_events SET processed=1 WHERE event_id=?", (event.event_id,))
            affected_count = conn.execute("SELECT COUNT(*) FROM affected_hours").fetchone()[0]
            if affected_count:
                conn.execute("DELETE FROM asset_hourly WHERE hour_utc IN (SELECT hour_utc FROM affected_hours)")
                conn.execute((ROOT / "sql" / "rebuild_gold.sql").read_text(encoding="utf-8"), {"run_id": run_id})
            if normalized:
                incident_count = _incident_rows(conn, run_id)
            else:
                incident_count = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
            conn.commit()
            _finish_run(conn, run_id, "SUCCESS", accepted=normalized, quarantined=late_review,
                        output_count=conn.execute("SELECT COUNT(*) FROM asset_hourly").fetchone()[0])
        except Exception as exc:
            conn.rollback()
            _finish_run(conn, run_id, "FAILED", error=type(exc).__name__)
            raise
    result = {"run_id": run_id, "normalized": normalized, "late_review": late_review,
              "affected_hours": affected_count, "incidents": incident_count}
    LOG.info(json.dumps({"stage": "build", **result}))
    return result
