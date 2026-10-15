"""Independent deterministic JSONL producer. No database access."""

from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .contracts import ASSETS, CADENCE_MINUTES, UNITS


BASE = {"temperature": 64.0, "vibration": 2.6, "pressure": 58.0}


def produce(path: Path, *, seed: int = 42, slots: int = 96, start: datetime | None = None) -> dict:
    """Write one metric event per asset/slot; deterministic gaps and a threshold breach."""
    if slots < 1 or slots > 96 * 30:
        raise ValueError("slots_out_of_range")
    start = start or datetime(2026, 10, 15, 0, 0, tzinfo=timezone.utc)
    if start.tzinfo is None or start.utcoffset() != timedelta(0):
        raise ValueError("start_must_be_utc")
    rng = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for slot in range(slots):
            observed = start + timedelta(minutes=CADENCE_MINUTES * slot)
            for asset_id, asset in ASSETS.items():
                for metric, unit in UNITS.items():
                    if asset_id == "CHILL-C301" and metric == "pressure" and slot in (3, 4):
                        continue  # Deliberately missing expected slots.
                    value = round(BASE[metric] + rng.uniform(-1.0, 1.0), 2)
                    if asset_id == "PUMP-A102" and metric == "temperature" and slot in (5, 6):
                        value = 84.3 if slot == 5 else 83.1
                    event = {
                        "event_id": f"EVT-{asset_id}-{observed:%Y%m%dT%H%MZ}-{metric.upper()}",
                        "source_id": "SYNTHETIC-PRODUCER-01",
                        "asset_id": asset_id,
                        "site_id": asset["site_id"],
                        "observed_at_utc": observed.isoformat().replace("+00:00", "Z"),
                        "metric": metric,
                        "value": value,
                        "unit": unit,
                        "quality": "GOOD",
                        "schema_version": 1,
                    }
                    output.write(json.dumps(event, separators=(",", ":"), sort_keys=True) + "\n")
                    count += 1
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {"seed": seed, "start_utc": start.isoformat().replace("+00:00", "Z"), "slots": slots,
                "expected_events": slots * len(ASSETS) * len(UNITS), "emitted_events": count,
                "sha256": digest, "synthetic": True, "contract_version": 1}
    path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
