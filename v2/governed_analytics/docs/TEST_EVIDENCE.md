# Test evidence

Build and test commands are listed in `README.md`. Evidence must be updated with the exact integration commit and CI run before a public V2 claim; this local builder file is not an independent reviewer sign-off.

| Check | Observed local result |
|---|---|
| Python runtime | 3.12.14 from shared `v2/.venv` |
| Seed | 4,000 orders + 8,000 lines + 711 returns + 12 products = 12,723 synthetic records |
| DuckDB build | 12,723 accepted, 0 rejected, 8,000 line facts; full optimized rebuild observed 1.03 seconds in one local PowerShell run (environment-specific) |
| Parquet | Four fact/dimension extracts produced and re-read in test |
| API | Read-only SQL execution returns exact statement, parameters, source hash, row counts and independent query ID |
| Independent oracle | Test reads source JSONL and independently recomputes monthly net/gross/category totals, not using model SQL or compiler |
| Negative cases | Duplicate order, missing product, negative amount, UTC midnight normalization, partial returns, unsupported metric, SQL injection value, extra SQL field; 422 refusals audited |
| `python -m pytest v2/governed_analytics/tests/test_reference.py -q` | **13 passed, 0 failed**, 1 Starlette/httpx deprecation warning, 4.43 s on the local Windows Python 3.12 environment. Includes forced DB-swap failure and Windows audit-handle deletion. |
| Local HTTP smoke test | `GET /` 200, `GET /api/status` 200 with 12,723 accepted rows, `POST /api/query` 200 with two monthly USD net rows; April 6,145,024 minor units; SQL contained bound placeholders |
| Browser E2E | Playwright 1.62.1 with locally installed Chrome passed desktop 1280×800 and mobile 390×844: loaded snapshot, executed net sales SQL, inspected returned table/chart and exact SQL, ran a category filter, then rejected an invalid date range and cleared the previous result. No horizontal overflow. |
| Evidence export | 8 executed metric/currency queries written to ignored `data/export/analytics-evidence.json`; current local build run ID `8efb27e007e5dea3` and matching Parquet generation. |

Critical-module statement coverage is **88.2%** for `analytics.pipeline` and **95.0%** for `analytics.semantic`. The independent coordinator review found and the builder fixed a possible Parquet/warehouse publication mismatch after a DB-swap failure, plus SQLite audit handle leaks; targeted tests now cover both. Remaining release evidence: CI at integration SHA and any public Pages route inspection. The local server UI is not evidence of a hosted live API.
