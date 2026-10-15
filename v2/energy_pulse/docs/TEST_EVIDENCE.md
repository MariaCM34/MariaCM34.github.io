# EnergyPulse test evidence — working checkpoint

Environment: Windows, Python 3.12.14 from the Codex workspace runtime, pinned V2 virtual environment; SQLite through Python standard library; FastAPI 0.143.1, Pydantic 2.14.1, pytest 9.1.1. Exact dependency versions are in `v2/requirements.lock`.

Commands executed from repository root:

```text
v2/.venv/Scripts/python.exe -m energy_pulse.cli demo --out-dir v2/energy_pulse/data/generated/slice1 --slots 12
v2/.venv/Scripts/python.exe -m pytest v2/energy_pulse/tests -q
node --check v2/energy_pulse/web/app.js
```

Observed 12-slot run: producer **106 emitted / 108 expected** with source SHA-256 `cfbe54cc0b3de09672ae216363aef05c65534a7412a9acefdff534c6ce6d7c2f`; ingest **106 accepted, 0 quarantined**; build **106 normalized, 27 Gold rows, 1 incident**. The initial implementation attempt rejected all rows because strict Pydantic dictionary validation treated the JSON timestamp as a string; after changing to JSON-mode validation, a fresh run produced the above results. The rejected first local database is ignored and not evidence of a successful run.

Current `pytest` after schema migrations 002/003: **11 passed, 0 failed, 1 dependency deprecation warning**. Added recovery-event and gap semantics, reviewed late and out-of-calendar backfill, duplicate-source slot protection, build rollback/retry fault injection, Windows file-handle cleanup, and strict UTC API negative filters. An independent reviewer first reproduced false `2/2 COMPLETE` coverage for one slot, an incident with no Gold row outside the calendar, and a Windows SQLite handle leak. All three were fixed and covered by tests. Critical-module statement coverage: `energy_pulse.contracts` **90.9%** and `energy_pulse.pipeline` **93.3%**. The integrated code is committed to remote `portfolio-v2` and passed clean-checkout [CI run 38754152711](https://github.com/MariaCM34/MariaCM34.github.io/actions/runs/38754152711).

`node v2/energy_pulse/tests/browser.mjs` against the seeded local API, using Playwright 1.62.1 and locally installed Chrome: **desktop 1280×800 and mobile 390×844 passed**. The test loads API data, selects an incident, checks Bronze/Silver lineage, changes to Chiller pressure, asserts 10/12 coverage and two partial hours, verifies the chart has two absent slots and disconnected line segments, toggles Spanish with keyboard, and rejects horizontal overflow. HTTP checks for `/`, JS, CSS, `/health`, assets, quality and incidents returned **7/7 200**.

Independent review and CI are complete for the tested reference scope. A formal accessibility audit, load benchmark, and public V2 release inspection remain open. The Pages-compatible frozen export is tracked under `v2/showcase/`; the local API is not hosted publicly.
