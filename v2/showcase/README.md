# V2 static evidence showcase

This is a GitHub Pages-compatible **frozen export**, not a hosted API. The three local applications execute and persist synthetic data independently. `export.py` reads their resulting SQLite database, governed SQL export, and per-case migration reports; `evidence.json` is the reviewed public snapshot. The page fetches that file and draws charts/tables from its records. It never claims a live connection or production telemetry.

The committed evidence records the source implementation commit in `source_commit`. Its export time is informational, not a freshness guarantee. Re-exporting requires all three local systems to have run successfully. The exporter checks the EnergyPulse JSONL hash against its synthetic manifest and persisted successful ingestion, and rejects a missing/mismatched database, an analytics export without the synthetic label, or incomplete, duplicated, or unexpected migration decisions.

## Reproduce

Start with the dependency and application setup in [`../README.md`](../README.md). In a clean checkout, set `PYTHONPATH` to `v2/energy_pulse/src`, `v2/governed_analytics`, and `v2/migration_assurance/src` using your shell's path separator, then run from the repository root:

```text
python -m energy_pulse.cli demo --out-dir v2/energy_pulse/data/generated/showcase --slots 12
python -m analytics.pipeline all
python -m analytics.export
python -m migration_assurance.cli suite --out v2/migration_assurance/artifacts/showcase
python v2/showcase/export.py --energy-db v2/energy_pulse/data/generated/showcase/energy.sqlite --analytics-export v2/governed_analytics/data/export/analytics-evidence.json --migration-reports v2/migration_assurance/artifacts/showcase
python -m http.server 8768 --bind 127.0.0.1 --directory v2/showcase
```

Open `http://127.0.0.1:8768/`. Use a fresh migration output directory for each suite run, since the exporter requires exactly one report per reviewed case and deliberately refuses ambiguous duplicates. The generated source databases, Parquet files, and detailed reports stay ignored; only the reviewed small `evidence.json` is published in the development branch. Run `node v2/showcase/browser.mjs` with Playwright installed, or use the repository's pinned `v2/package-lock.json` (`npm ci` from `v2/`).

The browser test covers desktop and mobile layouts, a sensor gap, currency/metric changes, a failed migration diff, keyboard language switching, and the missing-export state. The CI workflow reruns the source systems, regenerates the export, and repeats this browser flow. Source-level contracts, diagrams, ADRs, runbooks, and limitations live in each product directory.

## Security and interpretation

All entities and records are fictional and synthetic. The export contains only curated fields; no source row payloads, credentials, raw audit logs, or generated database files. A `PASS` migration decision applies to the executed fixture and engine versions only. The analytics selector chooses among eight executed, governed queries; it does not execute arbitrary SQL in the browser. EnergyPulse's static plot is an exported observation, while the local API/dashboard remains the executable system. No public backend or real equipment connection exists.
