"""Enforce the V2 spec's 85% statement coverage on each critical module."""

import json
from pathlib import Path


report = json.loads((Path(__file__).parent / "coverage.json").read_text(encoding="utf-8"))
critical = {
    "energy_pulse/contracts.py",
    "energy_pulse/pipeline.py",
    "governed_analytics/analytics/pipeline.py",
    "governed_analytics/analytics/semantic.py",
    "migration_assurance/engine.py",
}
found = set()
for path, result in report["files"].items():
    normalized = path.replace("\\", "/")
    matches = [name for name in critical if normalized.endswith(name)]
    if not matches:
        continue
    name = matches[0]
    found.add(name)
    percent = result["summary"]["percent_covered"]
    print(f"{name}: {percent:.1f}%")
    if percent < 85:
        raise SystemExit(f"Coverage gate failed: {name} below 85%")
if found != critical:
    raise SystemExit(f"Coverage gate missing modules: {sorted(critical - found)}")
