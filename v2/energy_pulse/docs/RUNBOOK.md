# EnergyPulse local operations and recovery

Run from the repository root with Python 3.12 and `v2/requirements.lock`; see README for installation and command order. Generated files are in `v2/energy_pulse/data/generated/` and ignored by Git. The API binds to `127.0.0.1` only. Check `/health`, `/api/runs`, and SQLite `pipeline_runs` after each stage.

**Ingest failure:** a file is committed atomically; the failed run records an error and the file can be rerun. Identical event IDs with the same payload are no-ops. A changed payload with an existing ID is quarantined; do not edit Bronze in place. Correct the producer source, assign a new event ID with an authorized correction policy, then rerun ingest/build.

**Build failure:** the build transaction rolls back Silver/Gold/incident changes and records `FAILED`. Rerun `build` with the same manifest. Raw rows with `processed=0` remain eligible. Check `quarantine.reason_code` for rejected records. `LATE_REVIEW` records require an explicit backfill process before they can enter Silver; this is not yet automated and is a release limitation.

**Quality:** `NO_DATA` means zero GOOD readings for an expected hour; `PARTIAL` means fewer GOOD readings than expected; `COMPLETE` means all expected slots have GOOD readings. If an asset is inactive or cadence changes, update the expected-slot policy and reprocess the affected period before interpreting coverage.

**Safe reset of synthetic demo:** use a fresh output directory and rerun seed/ingest/build. Do not delete a database containing evidence being reviewed. No real equipment or customer data may be loaded.
