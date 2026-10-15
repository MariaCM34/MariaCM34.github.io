"""Export a small, public-safe static snapshot from three executed local systems."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "v2" / "energy_pulse" / "src"))
from energy_pulse.contracts import RULES  # noqa: E402 — read the versioned executable rule registry


def energy_snapshot(database: Path) -> dict:
    if not database.is_file():
        raise FileNotFoundError(f"EnergyPulse database does not exist: {database}")
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    try:
        schema = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        if schema < 3:
            raise ValueError("EnergyPulse schema must be at least v3")
        counts = {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                  for table in ("raw_events", "measurements", "asset_hourly", "incidents", "quarantine")}
        def fetch(sql: str, params: tuple = ()) -> list[dict]:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]
        readings = fetch("""SELECT event_id,asset_id,observed_at_utc,metric,value,unit,source_quality
            FROM measurements WHERE (asset_id='PUMP-A102' AND metric='temperature')
               OR (asset_id='CHILL-C301' AND metric='pressure') ORDER BY asset_id,observed_at_utc""")
        quality = fetch("""SELECT asset_id,metric,hour_utc,expected_samples,received_samples,quality_status
            FROM asset_hourly WHERE (asset_id='PUMP-A102' AND metric='temperature')
               OR (asset_id='CHILL-C301' AND metric='pressure') ORDER BY asset_id,hour_utc""")
        incidents = fetch("""SELECT incident_id,asset_id,metric,opened_at_utc,closed_at_utc,status,
            rule_version,threshold,operator,first_event_id,last_event_id,gap_count
            FROM incidents ORDER BY opened_at_utc""")
        for incident in incidents:
            raw = conn.execute("SELECT payload_sha256 FROM raw_events WHERE event_id=?",
                               (incident["first_event_id"],)).fetchone()
            incident["source_sha256"] = raw[0] if raw else None
        manifest = json.loads(database.with_name("events.manifest.json").read_text(encoding="utf-8"))
        if not manifest.get("synthetic"):
            raise ValueError("EnergyPulse source must be marked synthetic")
        return {"schema_version": schema, "source_sha256": manifest["sha256"], "rules": RULES,
                "expected_events": manifest["expected_events"], "emitted_events": manifest["emitted_events"],
                "counts": counts, "readings": readings, "quality": quality, "incidents": incidents}
    finally:
        conn.close()


def analytics_snapshot(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "SYNTHETIC" not in data.get("label", ""):
        raise ValueError("Analytics export must be marked synthetic")
    return {"run_id": data["run_id"], "semantic_version": data["semantic_version"],
            "source_sha256": data["source_sha256"], "source_count": data["source_count"],
            "rejected_count": data["rejected_count"], "window": data["window"],
            "queries": [{key: query[key] for key in ("metric", "currency", "definition", "sql_executed", "bound_parameters", "rows", "row_count")}
                        for query in data["queries"]]}


def migration_snapshot(directory: Path) -> dict:
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in directory.glob("*-report.json")]
    if len(reports) != 17 or len({r["case_id"] for r in reports}) != 17:
        raise ValueError("Migration export requires one report for each of 17 reviewed cases")
    reports.sort(key=lambda r: r["case_id"])
    counts = dict(Counter(r["status"] for r in reports))
    cases = [{key: report.get(key) for key in ("case_id", "status", "stage", "source_sql", "target_sql",
              "row_counts", "differences", "error", "engines", "input_hashes", "result_hashes")}
             for report in reports]
    return {"counts": counts, "cases": cases, "rules_version": reports[0]["rules_version"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--energy-db", type=Path, required=True)
    parser.add_argument("--analytics-export", type=Path, required=True)
    parser.add_argument("--migration-reports", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("evidence.json"))
    args = parser.parse_args()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                            capture_output=True, text=True).stdout.strip()
    bundle = {"label": "SYNTHETIC, FROZEN EXPORT — local systems are executable separately",
              "exported_at_utc": datetime.now(timezone.utc).isoformat(), "source_commit": commit,
              "energy": energy_snapshot(args.energy_db),
              "analytics": analytics_snapshot(args.analytics_export),
              "migration": migration_snapshot(args.migration_reports)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "commit": commit,
                      "energy_bronze": bundle["energy"]["counts"]["raw_events"],
                      "analytics_sources": bundle["analytics"]["source_count"],
                      "migration_cases": len(bundle["migration"]["cases"])}))


if __name__ == "__main__":
    main()
