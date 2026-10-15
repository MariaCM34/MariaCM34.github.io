# Test evidence — local reference implementation

**Observed environment:** Windows; Python 3.12.14; SQLite 3.53.1; DuckDB 1.5.6; SQLGlot 30.23.0; pytest 9.1.1. The shared `v2/requirements.lock` supplies the pinned V2 environment. All data is synthetic. Evidence was run on 2026-10-15 UTC in a working V2 branch; reports generated before the package's integration commit indicate a dirty package and must be regenerated after commit for a clean release snapshot.

From repository root:

```powershell
$env:PYTHONPATH='v2/migration_assurance/src'
v2/.venv/Scripts/python.exe -m pytest -q v2/migration_assurance/tests
v2/.venv/Scripts/python.exe -m migration_assurance.cli suite --out v2/migration_assurance/artifacts/release
```

**Current integrated result:** `20 passed` for this package within a 44-test combined V2 run; suite assessed 17 cases with zero unexpected decisions: 11 PASS from distinct queries actually executed on both engines, 2 expected FAIL from altered/missing target records, and 4 expected REVIEW refusals. The mismatch report contains `A-001.amount: expected 10.00; actual 11.00`; source and target fixture digests differ. Tests verify independent persisted executed-row files and hashes, changed duplicate counts, NULL-vs-zero, missing key, type/order mismatch, malformed contract, replay stability, HTML escaping, and refusal of DELETE, multiple statements, unordered LIMIT, unapproved table, JOIN/CTE and unknown functions. A cross-review found that an `ORDER BY` string literal could falsely meet an ordered-comparison requirement; the check now inspects the SQLGlot AST. A second regression rejects invalid ISO dates in fixtures even when a query does not project the date.

HTTP smoke test: Python's `ThreadingHTTPServer` served the generated `index.html` via `127.0.0.1`; `urllib.request.urlopen` returned **HTTP 200, 7,648 bytes**. The subsequent Playwright browser test passed on desktop 1280×800 and mobile 390×844: it filtered 17 cases to 2 FAIL cases, followed the deliberate mismatch report, verified the A-001 field difference and engine labels, and found no horizontal overflow.

The generated artifacts under `artifacts/` are ignored by Git. They include versioned case copies and fixtures, JSON reports, both engines' executed rows, individual HTML reports and an index with decision filtering. `git check-ignore` confirmed the generated index is ignored. For a releasable Pages evidence export, regenerate on the exact integrated commit, run browser E2E at desktop/mobile, verify no private paths/data, and record the final commit and CI URL.

Coverage of `migration_assurance.engine` is **85.8%** statement coverage using pinned pytest-cov/coverage. Independent cross-review was performed and its P1 ordering finding corrected; CI at an integrated commit and public V2 deployment remain pending. This is a **reference implementation**, not production-ready or deployed V2.
