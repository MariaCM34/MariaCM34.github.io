# ADR 001 — V2 execution boundary and first contracts

**Status:** accepted for implementation on `portfolio-v2`; 2026-10-15. These are reference-implementation decisions, not evidence of completed products.

## Context

GitHub Pages cannot run the ingestion, databases, or Python APIs. V1's browser prototypes must remain published until replacement evidence passes the quality gates. The supplied Gate 1 report proposes three isolated Python packages and a static public evidence layer.

## Decisions

1. **Hybrid release:** each engineering product runs locally from pinned Python dependencies and generates a bounded, sanitized, versioned HTML/JSON evidence export. Pages may later publish those artifacts with run ID, UTC timestamp, source commit, and explicit “snapshot” label. Hosted APIs need a separate security/cost review.
2. **Shared baseline:** Python 3.12 in CI and the local V2 virtual environment; package-local source and tests under `v2/`. A single `v2/requirements.lock` pins the current compatibility-spike environment; packages may split locks when their dependencies diverge. Windows PowerShell and CI commands are both required. Docker is optional because the local daemon is unavailable in this environment.
3. **Energy contract:** one event per metric and 15-minute slot for active assets; metrics `temperature/C`, `vibration/mm/s`, `pressure/bar`; UTC observations; deterministic synthetic producer. `event_id` is the idempotency key. Identical retry is a no-op; same ID with different canonical payload is quarantined. A 48-hour event-time lateness window permits affected-bucket recomputation; older arrivals require an explicit backfill. Missingness derives from expected slots, not from a zero value. Versioned rules produce stable incident episodes. The public API is read-only.
4. **Analytics contract:** order, line, return, and product are separate entities. Monetary values use integer minor units and each reported aggregate is currency-specific. Gross sales use completed lines before discount; net sales use completed lines after discount less **accepted** returns on return-acceptance date. Cancellation rate counts distinct cancelled eligible placed orders over distinct eligible placed orders in the placement-time window. Reporting buckets use UTC. No FX conversion or generative-AI claim in the first release. A deterministic semantic allowlist compiles parameterized SQL that is actually executed on a read-only DuckDB snapshot; audit logs use separate SQLite.
5. **Migration contract:** SQLite → DuckDB is the sole first executable dialect pair. Exactly one read-only `SELECT` from a declared supported AST subset per case. Source and target fixtures load into separate database files and execute in their respective engines. A declared key or duplicate-aware multiset governs result comparison; decimal tolerance and timezone normalization must be explicit. `PASS` means only that the tested fixtures and engines agreed under the declared comparator. Unsupported or ambiguous constructs yield `REVIEW`; observed divergence yields `FAIL`. SHA-256 report hashes provide integrity, not signer identity. T-SQL → Snowflake remains unevaluated compatibility research.
6. **Personal claims:** V1's professional biography remains unchanged during the build. Any new public technical claim must link exact executable evidence; existing biographical claims require owner review before V2 release text changes them.

## Consequences and rejected alternatives

- No public live API is implied by a Pages chart. Static exports must originate from a real executed pipeline and show when they were generated.
- SQLite/WAL favors a zero-secret single-writer Energy demo over a PostgreSQL service; actual lock and load behavior will be tested, not asserted as industrial scalability.
- DuckDB is used with an offline single-writer build and read-only serving to avoid unsupported multi-process writes. dbt is deferred until model volume or collaboration justifies it.
- Kafka, Spark, Kubernetes, an LLM, Snowflake, and paid hosting add cost or claims without supporting the first end-to-end slice, so none is on the critical path.
- Python 3.14 exists on this host but is not the supported baseline until the pinned dependency set and CI pass on it. Docker is not a release gate for a local-only implementation when Python-based fresh-clone setup is complete.

## Verification required before any public claim

Each package must demonstrate source → persisted storage → transformation → API/report → UI using actual commands and stable source IDs, with negative cases, independent expected values, structured run logs, fresh-clone setup, CI, and reviewer evidence. A V1 test result does not satisfy a V2 gate.
