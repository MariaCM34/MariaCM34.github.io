"""Local read-only API for exact executed SQL and separate refusal audit."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from contextlib import closing
from pathlib import Path

import duckdb
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import ValidationError

from .pipeline import DATA, ROOT
from .semantic import CATALOG, VERSION, QueryRequest, compile_query


def create_app(database: Path | None = None, audit: Path | None = None) -> FastAPI:
    database = database or DATA / "warehouse.duckdb"
    audit = audit or DATA / "audit.sqlite"
    app = FastAPI(title="Governed Analytics — synthetic local reference", version=VERSION)

    def audit_event(query_id: str, status: str, reason: str, payload: dict) -> None:
        audit.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(audit)) as con:
            with con:
                con.execute("CREATE TABLE IF NOT EXISTS query_audit (query_id TEXT PRIMARY KEY, at_utc TEXT NOT NULL DEFAULT (datetime('now')), status TEXT NOT NULL, reason TEXT NOT NULL, request_json TEXT NOT NULL)")
                con.execute("INSERT INTO query_audit (query_id, status, reason, request_json) VALUES (?, ?, ?, ?)",
                            (query_id, status, reason, json.dumps(payload, sort_keys=True)))

    @app.get("/")
    def home():
        return FileResponse(ROOT / "web" / "index.html")

    @app.get("/api/catalog")
    def catalog():
        return {"version": VERSION, "metrics": CATALOG, "synthetic": True}

    @app.get("/api/status")
    def status():
        if not database.exists():
            raise HTTPException(503, "Run the seed/build pipeline first")
        con = duckdb.connect(str(database), read_only=True)
        try:
            row = con.execute("SELECT run_id, model_version, model_sha256, source_sha256, source_count, rejected_count, processed_at FROM run_manifest").fetchone()
            return dict(zip(("run_id", "model_version", "model_sha256", "source_sha256", "source_count", "rejected_count", "processed_at"), row))
        finally:
            con.close()

    @app.post("/api/query")
    async def query(request: Request):
        query_id = str(uuid.uuid4())
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                raise ValueError("request must be an object")
            req = QueryRequest.model_validate(payload)
        except (ValueError, ValidationError, json.JSONDecodeError) as exc:
            audit_event(query_id, "REFUSED", "unsupported or invalid semantic request", {"request_type": type(exc).__name__})
            raise HTTPException(422, {"query_id": query_id, "reason": "Unsupported metric or invalid filter. Previous result must be cleared."})
        if not database.exists():
            raise HTTPException(503, "Run the seed/build pipeline first")
        sql, params = compile_query(req)
        started = time.perf_counter()
        con = duckdb.connect(str(database), read_only=True)
        deadline = threading.Timer(2.0, con.interrupt)
        try:
            deadline.start()
            cursor = con.execute(sql, params)
            columns = [d[0] for d in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            snapshot_run, snapshot_hash = con.execute("SELECT run_id, source_sha256 FROM run_manifest").fetchone()
        except Exception:
            audit_event(query_id, "ERROR", "query execution failed", req.model_dump(mode="json"))
            raise HTTPException(500, "Query execution failed")
        finally:
            deadline.cancel()
            con.close()
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        audit_event(query_id, "EXECUTED", "", req.model_dump(mode="json"))
        return {"query_id": query_id, "metric_version": VERSION, "metric": req.metric,
                "definition": CATALOG[req.metric], "sql_executed": sql, "parameters": params,
                "rows": rows, "row_count": len(rows), "elapsed_ms": elapsed_ms,
                "source_snapshot_sha256": snapshot_hash, "synthetic": True,
                "snapshot_run_id": snapshot_run,
                "lineage": "JSONL → raw_* DuckDB → fct_order_lines/fct_returns/fct_orders → bound SELECT → API"}

    @app.get("/api/audit/{query_id}")
    def audit_query(query_id: str):
        if not audit.exists():
            raise HTTPException(404, "No audit record")
        with closing(sqlite3.connect(audit)) as con:
            row = con.execute("SELECT query_id, at_utc, status, reason, request_json FROM query_audit WHERE query_id = ?", (query_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "No audit record")
        return dict(zip(("query_id", "at_utc", "status", "reason", "request_json"), row))

    return app


app = create_app()
