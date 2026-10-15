# Differential testing and independent evidence

The suite has **11 distinct supported SELECT queries** executed on both engines: keyed projection, status filter, NULL filter, grouped count, grouped sum, COALESCE, HAVING, date range, arithmetic, ordered LIMIT, and duplicate-aware multiset. It also executes two negative data cases: changed A-001 amount and missing A-004 key. Four unsafe/ambiguous SQL cases are refused before execution. Tests additionally assert NULL-vs-zero, changed duplicate counts, type/order mismatch, malformed comparison contract, and stable replay hashes.

The case JSON, source fixture, and target fixture have separate SHA-256 hashes. Source and target row results have separate hashes and JSON files. A row count match alone is never treated as equivalence. The baseline data is intentionally simple and does not cover locale collation, timestamp conversion, overflow, large workloads, all SQLite affinity edges, or all DuckDB versions.

Independent oracle: the deliberate mismatch expected value comes directly from the immutable source fixture (`A-001 = 10.00`) and target fault fixture (`A-001 = 11.00`), not from the comparator's output. Tests require the field-level `A-001.amount` difference. The suite's expected decision list is explicit and checked; 11 PASS is not inferred by counting files.
