# Operations runbook

## Reproduce

Use Python 3.12 and the repository's `v2/requirements.lock`. From the repository root in PowerShell:

```powershell
$env:PYTHONPATH='v2/governed_analytics'
& v2/.venv/Scripts/python.exe -m analytics.pipeline all
& v2/.venv/Scripts/python.exe -m pytest v2/governed_analytics/tests -q
& v2/.venv/Scripts/python.exe -m uvicorn analytics.api:app --host 127.0.0.1 --port 8766
```

Open `http://127.0.0.1:8766/`, run a metric for `2026-04-01`–`2026-06-01`, and compare the returned SQL/params/row counts with the `data/` artifacts. `GET /api/status`, `GET /api/catalog`, `POST /api/query` and `GET /api/audit/{query_id}` are local endpoints. The OpenAPI schema is at `/docs`. A build from the default seed should yield 4,000 orders, 8,000 lines, 711 return events and 12 product records, total 12,723; actual build counts are in `data/build_manifest.json`.

## Recovery and fault injection

- To replay without changing source data, run `python -m analytics.pipeline build`. The same source/model/rejection content produces the same run ID and counts. The warehouse is built as `warehouse.duckdb.building`; its four Parquet files are staged under `parquet/.<run_id>-*/`, then published as `parquet/<run_id>/` before the DB swap. The DB's `run_manifest.run_id` identifies the matching Parquet generation. If the swap fails, the prior DB and its old Parquet generation remain valid; an unreferenced new generation may remain and can be removed after confirming it is not the manifest run ID. Do not serve the DB while replacing it on Windows; stop the local API first.
- To change the deterministic seed, run `python -m analytics.pipeline seed --orders 4000`, then `build`. This overwrites only package-local generated `data/` files. Generated data is ignored by Git.
- To inject a validation failure, append a duplicate `order_id` or negative `unit_minor` line to the generated JSONL, then rebuild. Check `data/rejections.jsonl` and `data/build_manifest.json`. Invalid rows do not enter facts; valid rows still load. Restore by reseeding.
- To inspect a known refund, open DuckDB read-only and run the lineage query in `DATA_DICTIONARY.md`. To inspect a refusal, use its query ID in `/api/audit/{id}` or the local `data/audit.sqlite` file.
- To export static evidence from the **actual** built snapshot, run `python -m analytics.export`; it writes eight currency-specific metric results to ignored `data/export/analytics-evidence.json` with exact SQL, bound parameters, UTC processing/export times and source hash. It is a snapshot, not an interactive hosted API.

## Boundaries

The build is single-writer/offline and the local API is read-only. No concurrent ingestion, CDC, real order feeds, authentication, production monitoring, SLA or public API hosting exists. The audit store is separate so query logging does not mutate the warehouse. `run_id` is a deterministic content identifier, not a cryptographic signature. SHA-256 detects content changes but does not authenticate a data owner.
