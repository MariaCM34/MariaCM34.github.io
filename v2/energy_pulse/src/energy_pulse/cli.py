"""Separate reproducible producer, ingestor, builder, and read-only server commands."""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .pipeline import backfill, build, ingest, migrate
from .producer import produce


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EnergyPulse synthetic telemetry reference system")
    sub = parser.add_subparsers(dest="command", required=True)
    seed = sub.add_parser("seed")
    seed.add_argument("--out", type=Path, required=True)
    seed.add_argument("--seed", type=int, default=42)
    seed.add_argument("--slots", type=int, default=96)
    init = sub.add_parser("migrate")
    init.add_argument("--db", type=Path, required=True)
    load = sub.add_parser("ingest")
    load.add_argument("--db", type=Path, required=True)
    load.add_argument("--source", type=Path, required=True)
    model = sub.add_parser("build")
    model.add_argument("--db", type=Path, required=True)
    model.add_argument("--manifest", type=Path, required=True)
    review = sub.add_parser("backfill")
    review.add_argument("--db", type=Path, required=True)
    review.add_argument("--event-id", required=True)
    review.add_argument("--reason", required=True)
    demo = sub.add_parser("demo")
    demo.add_argument("--out-dir", type=Path, default=Path("data/generated"))
    demo.add_argument("--seed", type=int, default=42)
    demo.add_argument("--slots", type=int, default=96)
    serve = sub.add_parser("serve")
    serve.add_argument("--db", type=Path, required=True)
    serve.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.command == "seed":
        result = produce(args.out, seed=args.seed, slots=args.slots)
    elif args.command == "migrate":
        migrate(args.db)
        result = {"database": str(args.db), "migration": 3}
    elif args.command == "ingest":
        result = ingest(args.db, args.source)
    elif args.command == "build":
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = build(args.db, start=datetime.fromisoformat(manifest["start_utc"].replace("Z", "+00:00")), slots=manifest["slots"])
    elif args.command == "backfill":
        result = backfill(args.db, event_id=args.event_id, reason=args.reason)
    elif args.command == "demo":
        args.out_dir.mkdir(parents=True, exist_ok=True)
        source = args.out_dir / "events.jsonl"
        db = args.out_dir / "energy.sqlite"
        calls = [
            ["seed", "--out", str(source), "--seed", str(args.seed), "--slots", str(args.slots)],
            ["ingest", "--db", str(db), "--source", str(source)],
            ["build", "--db", str(db), "--manifest", str(source.with_suffix(".manifest.json"))],
        ]
        for call in calls:
            subprocess.run([sys.executable, "-m", "energy_pulse.cli", *call], check=True)
        result = {"database": str(db), "source": str(source), "local_url": "http://127.0.0.1:8765/",
                  "serve_command": f"python -m energy_pulse.cli serve --db {db}"}
    else:
        import uvicorn
        from .api import create_app
        uvicorn.run(create_app(args.db), host="127.0.0.1", port=args.port)
        return 0
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
