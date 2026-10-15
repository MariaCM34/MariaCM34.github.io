"""Read-only API over persisted SQLite pipeline output."""

from __future__ import annotations

import sqlite3
import re
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from .contracts import ASSETS, RULES, UNITS


WEB = Path(__file__).resolve().parents[2] / "web"
UTC_FILTER = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def validate_filter(value: str | None) -> datetime | None:
    if value is None:
        return None
    if not UTC_FILTER.fullmatch(value):
        raise HTTPException(status_code=422, detail="timestamp_must_be_utc_second_precision")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="invalid_timestamp") from exc


@contextmanager
def read_db(path: Path) -> Iterator[sqlite3.Connection]:
    if not path.is_file():
        raise HTTPException(status_code=503, detail="database_not_ready")
    conn = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    try:
        yield conn
    finally:
        conn.close()


def rows(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def create_app(db_path: Path) -> FastAPI:
    app = FastAPI(title="EnergyPulse synthetic telemetry API", version="0.1.0")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB / "index.html")

    @app.get("/app.js")
    def script() -> FileResponse:
        return FileResponse(WEB / "app.js", media_type="text/javascript")

    @app.get("/style.css")
    def style() -> FileResponse:
        return FileResponse(WEB / "style.css", media_type="text/css")

    @app.get("/health")
    def health() -> dict:
        with read_db(db_path) as conn:
            version = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        return {"status": "ok", "schema_version": version, "synthetic": True}

    @app.get("/api/assets")
    def assets() -> dict:
        return {"items": [{"asset_id": key, **value} for key, value in ASSETS.items()], "synthetic": True}

    @app.get("/api/rules")
    def rules() -> dict:
        return {"items": RULES, "synthetic": True}

    @app.get("/api/runs")
    def runs(limit: int = Query(20, ge=1, le=100)) -> dict:
        with read_db(db_path) as conn:
            items = rows(conn, "SELECT * FROM pipeline_runs ORDER BY started_at_utc DESC,run_id DESC LIMIT ?", (limit,))
        return {"items": items, "synthetic": True}

    @app.get("/api/measurements")
    def measurements(
        asset_id: str,
        metric: str,
        start: str | None = None,
        end: str | None = None,
        limit: int = Query(500, ge=1, le=1000),
    ) -> dict:
        if asset_id not in ASSETS or metric not in UNITS:
            raise HTTPException(status_code=422, detail="unsupported_asset_or_metric")
        start_time, end_time = validate_filter(start), validate_filter(end)
        if start_time and end_time and (start_time >= end_time or end_time - start_time > timedelta(days=31)):
            raise HTTPException(status_code=422, detail="invalid_time_range")
        with read_db(db_path) as conn:
            items = rows(conn, """SELECT event_id,asset_id,site_id,observed_at_utc,metric,value,unit,source_quality
                 FROM measurements WHERE asset_id=? AND metric=? AND (? IS NULL OR observed_at_utc>=?)
                 AND (? IS NULL OR observed_at_utc<?) ORDER BY observed_at_utc LIMIT ?""",
                 (asset_id, metric, start, start, end, end, limit))
        return {"items": items, "asset_id": asset_id, "metric": metric, "unit": UNITS[metric],
                "grain": "one source event per asset/metric/15-minute slot", "timezone": "UTC", "synthetic": True}

    @app.get("/api/quality")
    def quality(asset_id: str | None = None, metric: str | None = None, limit: int = Query(500, ge=1, le=1000)) -> dict:
        if asset_id is not None and asset_id not in ASSETS:
            raise HTTPException(status_code=422, detail="unsupported_asset")
        if metric is not None and metric not in UNITS:
            raise HTTPException(status_code=422, detail="unsupported_metric")
        with read_db(db_path) as conn:
            items = rows(conn, """SELECT * FROM asset_hourly WHERE (? IS NULL OR asset_id=?)
                AND (? IS NULL OR metric=?) ORDER BY hour_utc,asset_id,metric LIMIT ?""",
                (asset_id, asset_id, metric, metric, limit))
        return {"items": items, "grain": "asset/metric/UTC hour", "synthetic": True}

    @app.get("/api/incidents")
    def incidents(asset_id: str | None = None, limit: int = Query(100, ge=1, le=500)) -> dict:
        if asset_id is not None and asset_id not in ASSETS:
            raise HTTPException(status_code=422, detail="unsupported_asset")
        with read_db(db_path) as conn:
            items = rows(conn, """SELECT * FROM incidents WHERE (? IS NULL OR asset_id=?)
                ORDER BY opened_at_utc DESC,incident_id LIMIT ?""", (asset_id, asset_id, limit))
        return {"items": items, "synthetic": True}

    @app.get("/api/incidents/{incident_id}/lineage")
    def lineage(incident_id: str) -> dict:
        with read_db(db_path) as conn:
            incident = conn.execute("SELECT * FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()
            if incident is None:
                raise HTTPException(status_code=404, detail="incident_not_found")
            event_id = incident["first_event_id"]
            raw = conn.execute("SELECT event_id,payload_json,payload_sha256,ingested_at_utc,ingest_run_id FROM raw_events WHERE event_id=?", (event_id,)).fetchone()
            silver = conn.execute("SELECT * FROM measurements WHERE event_id=?", (event_id,)).fetchone()
            gold = conn.execute("""SELECT * FROM asset_hourly WHERE asset_id=? AND metric=? AND hour_utc=?""",
                (incident["asset_id"], incident["metric"], incident["opened_at_utc"][:13] + ":00:00Z")).fetchone()
            transitions = rows(conn, "SELECT * FROM incident_transitions WHERE incident_id=? ORDER BY transition_at_utc", (incident_id,))
        return {"incident": dict(incident), "raw": dict(raw), "measurement": dict(silver),
                "gold": dict(gold) if gold else None, "transitions": transitions, "synthetic": True}

    return app
