# EnergyPulse test evidence — working checkpoint

Environment: Windows, Python 3.12.14 from the Codex workspace runtime, pinned V2 virtual environment; SQLite through Python standard library; FastAPI 0.143.1, Pydantic 2.14.1, pytest 9.1.1. Exact dependency versions are in `v2/requirements.lock`.

Commands executed from repository root:

```text
v2/.venv/Scripts/python.exe -m energy_pulse.cli demo --out-dir v2/energy_pulse/data/generated/slice1 --slots 12
v2/.venv/Scripts/python.exe -m pytest v2/energy_pulse/tests -q
node --check v2/energy_pulse/web/app.js
```

Observed 12-slot run: producer **106 emitted / 108 expected** with source SHA-256 `cfbe54cc0b3de09672ae216363aef05c65534a7412a9acefdff534c6ce6d7c2f`; ingest **106 accepted, 0 quarantined**; build **106 normalized, 27 Gold rows, 1 incident**. The initial implementation attempt rejected all rows because strict Pydantic dictionary validation treated the JSON timestamp as a string; after changing to JSON-mode validation, a fresh run produced the above results. The rejected first local database is ignored and not evidence of a successful run.

`pytest`: **6 passed, 0 failed, 1 dependency deprecation warning**. Cases cover separate-process source-to-Gold lineage, replay/idempotency and conflict quarantine, invalid event and explicit `NO_DATA`, in-policy late repair of only one hour, out-of-policy `LATE_REVIEW`, and API read/negative filters. Browser inspection of the local API dashboard showed the persisted Pump temperature incident's Bronze/Silver/Gold/rule chain; switching to Chiller pressure showed **10/12 · 83%** coverage and two `PARTIAL` hourly cells. HTTP checks for `/`, JS, CSS, `/health`, assets, quality and incidents returned **7/7 200**.

This is not independent reviewer sign-off or fresh-clone CI. More recovery, accessibility, benchmark and release checks are pending.
