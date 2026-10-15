# EnergyPulse local operations and recovery

Run from the repository root with Python 3.12 and `v2/requirements.lock`; see README for installation and command order. Generated files are in `v2/energy_pulse/data/generated/` and ignored by Git. The API binds to `127.0.0.1` only. Check `/health`, `/api/runs`, and SQLite `pipeline_runs` after each stage.

**Ingest failure:** a file is committed atomically; the failed run records an error and the file can be rerun. Identical event IDs with the same payload are no-ops. A changed payload with an existing ID is quarantined; do not edit Bronze in place. Correct the producer source, assign a new event ID with an authorized correction policy, then rerun ingest/build.

**Build failure:** the build transaction rolls back Silver/Gold/incident changes and records `FAILED`. Rerun `build` with the same manifest. Raw rows with `processed=0` remain eligible. A fault-injection test raises after Gold processing and verifies rollback followed by a successful retry.

**Late or out-of-calendar data:** observations older than the 48-hour watermark remain in Bronze with `processed=1` and enter `quarantine` as `LATE_REVIEW`; an otherwise valid event outside expected slots is `OUTSIDE_CALENDAR`. Neither silently affects Silver, Gold or incidents. Inspect the source event and confirm the calendar policy. If needed, run `build` with an extended manifest first. Then run `python -m energy_pulse.cli backfill --db <db> --event-id <id> --reason "reviewed synthetic correction"`. This records the reason in `reviewed_backfills`, inserts the Silver row, rebuilds its Gold hour and recomputes incidents atomically. Repeating the same backfill is rejected. In a real installation the review step would need authentication and an operator identity; this local demo accepts only a CLI invocation.

**Incident uncertainty:** a gap following a threshold breach is not a normal reading. The incident remains open until a later GOOD reading actually clears the rule; `gap_count` records the unobserved slots. `CLOSED` transition provenance points to that recovery event. The dashboard must not imply that missing readings prove recovery.

**Quality:** `NO_DATA` means zero GOOD readings for an expected hour; `PARTIAL` means fewer GOOD readings than expected; `COMPLETE` means all expected slots have GOOD readings. If an asset is inactive or cadence changes, update the expected-slot policy and reprocess the affected period before interpreting coverage.

**Safe reset of synthetic demo:** use a fresh output directory and rerun seed/ingest/build. Do not delete a database containing evidence being reviewed. No real equipment or customer data may be loaded.
