# Portfolio V2 — executable data engineering references

Three synthetic, local reference implementations share pinned Python 3.12 dependencies and one browser-test lockfile. They are designed to show actual source-to-consumption flows, not to imply that GitHub Pages runs a backend. Public `main` remains the V1 site until V2's release gates pass.

The [static evidence showcase](showcase/README.md) is a separate GitHub Pages-compatible **frozen export** generated from all three executed systems. Its interactive charts and filters select source-backed exported results; the full APIs, ingestion, query execution and reconciliation run locally.

| Product | Buyer problem | Executed path | Local UI |
| --- | --- | --- | --- |
| [EnergyPulse](energy_pulse/README.md) | Industrial analyst needs trustworthy readings, quality gaps and explainable incidents | JSONL → SQLite Bronze/Silver/Gold → FastAPI → SVG/table/lineage | `http://127.0.0.1:8876/` |
| [Governed Analytics](governed_analytics/README.md) | Ecommerce team needs consistent currency-separated sales and returns | JSONL → DuckDB facts/Parquet → governed parameterized SQL → FastAPI → chart/table | `http://127.0.0.1:8766/` |
| [Migration Assurance](migration_assurance/README.md) | Migration lead needs evidence that translated SQL returns equivalent data | reviewed SQLGlot AST → SQLite and DuckDB execution → typed diff → static HTML evidence | `http://127.0.0.1:8767/` |

These businesses, records, sites and orders are fictional. No employer or client data, credentials, live plant data, or paid service is used. The local APIs bind to loopback and have no authentication; do not expose them on a public interface. GitHub Pages can display a static export and project documentation, not these APIs or interactive SQL execution.

## Reproduce

Run from repository root. Use Python 3.12, Node 22 or 24, and free package registries. The lockfiles are [requirements.lock](requirements.lock) and [package-lock.json](package-lock.json). On Windows PowerShell:

```powershell
py -3.12 -m venv v2/.venv
v2/.venv/Scripts/python.exe -m pip install -r v2/requirements.lock
npm ci --prefix v2 --ignore-scripts --no-audit --no-fund
npx --prefix v2 playwright install chromium
$env:PYTHONPATH='v2/energy_pulse/src;v2/governed_analytics;v2/migration_assurance/src'
v2/.venv/Scripts/python.exe -m energy_pulse.cli demo --out-dir v2/energy_pulse/data/generated/demo --slots 12
v2/.venv/Scripts/python.exe -m analytics.pipeline all
v2/.venv/Scripts/python.exe -m migration_assurance.cli suite --out v2/migration_assurance/artifacts/demo
v2/.venv/Scripts/python.exe -m pytest v2/energy_pulse/tests v2/governed_analytics/tests v2/migration_assurance/tests -q
```

Start the three local servers in separate terminals using the commands in each package README. The Migration Assurance server is `python -m http.server 8767 --bind 127.0.0.1 --directory v2/migration_assurance/artifacts/demo`. With servers running, execute the three `tests/browser.mjs` scripts via Node. On macOS/Linux, use `v2/.venv/bin/python` and colon-separated `PYTHONPATH`. CI repeats seed/build/test/browser flows in `.github/workflows/v2-validation.yml`.

The combined result is **44 Python tests passed**, **23 V1 Node regressions passed**, and **four desktop/mobile browser flows passed** (three local applications plus the static showcase). Per-module statement coverage of five critical business modules is 85.8–95.0%. A clean detached checkout reproduced the source-to-result flows. [GitHub Actions validation](https://github.com/MariaCM34/MariaCM34.github.io/actions/workflows/v2-validation.yml) reruns the tests, builds all datasets, regenerates the frozen export and tests the four browser flows; see the package test-evidence documents and [`STATUS.md`](../PORTFOLIO_V2_REBUILD/STATUS.md) for exact run results.

## Architecture and limits

The initial [Gate 1 architecture](../PORTFOLIO_V2_REBUILD/docs/06_ARCHITECTURE_GATE_1.md) and [execution ADR](../PORTFOLIO_V2_REBUILD/docs/ADRS/001-execution-boundary-and-contracts.md) set the local-backend/static-Pages boundary. Each package contains a flow diagram, contracts or data dictionary, decision record, operations guide, tests and observed evidence. The choices favor SQLite/DuckDB, SQLGlot and narrow FastAPI services because they can be run and inspected on one laptop without cloud infrastructure or secrets.

These references do not include production authentication, multi-tenancy, concurrent ingestion, calibrated safety thresholds, currency conversion, vendor-specific migration certification, SLA, or a hosted public backend. A PASS is bounded by the tested synthetic fixtures and comparison rules. A browser chart is only evidence when its underlying executed rows are inspectable.
