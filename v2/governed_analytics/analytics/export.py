"""Create a transparent, immutable-feeling public snapshot from executed SQL."""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb

from .pipeline import DATA
from .semantic import CATALOG, VERSION, QueryRequest, compile_query


def export(database: Path = DATA / "warehouse.duckdb", target: Path = DATA / "export" / "analytics-evidence.json") -> dict:
    if not database.exists():
        raise FileNotFoundError("Build the warehouse before exporting")
    con = duckdb.connect(str(database), read_only=True)
    try:
        run = con.execute("SELECT run_id, model_version, source_sha256, source_count, rejected_count, processed_at FROM run_manifest").fetchone()
        evidence = {"label": "SYNTHETIC DEMO SNAPSHOT — not a live API", "exported_at_utc": datetime.now(timezone.utc).isoformat(),
                    "run_id": run[0], "model_version": run[1], "semantic_version": VERSION, "source_sha256": run[2],
                    "source_count": run[3], "rejected_count": run[4], "processed_at_utc": run[5],
                    "window": "2026-04-01 inclusive to 2026-06-01 exclusive UTC", "queries": []}
        for metric in CATALOG:
            for currency in ("USD", "COP"):
                req = QueryRequest(metric=metric, start=date(2026, 4, 1), end=date(2026, 6, 1), currency=currency)
                sql, params = compile_query(req)
                cursor = con.execute(sql, params)
                columns = [d[0] for d in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                evidence["queries"].append({"metric": metric, "definition": CATALOG[metric], "currency": currency,
                                            "sql_executed": sql, "bound_parameters": params, "rows": rows,
                                            "row_count": len(rows)})
    finally:
        con.close()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return {"path": str(target), "query_count": len(evidence["queries"]), "source_count": evidence["source_count"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=DATA / "warehouse.duckdb")
    parser.add_argument("--out", type=Path, default=DATA / "export" / "analytics-evidence.json")
    args = parser.parse_args()
    print(json.dumps(export(args.database, args.out)))
