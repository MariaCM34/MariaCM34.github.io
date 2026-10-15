# EnergyPulse architecture and data flow

The source is a seeded Python producer with no database access. It writes JSONL plus a manifest containing seed, expected/emitted counts, UTC start and source SHA-256. The ingestor validates the versioned event contract and writes immutable accepted payloads to `raw_events`; invalid records and conflicting IDs go to `quarantine`. A separate build command normalizes new raw events into `measurements`, constructs expected 15-minute asset/metric slots, executes SQLite SQL from `sql/rebuild_gold.sql` for affected UTC hours, and computes deterministic threshold episodes. FastAPI uses read-only SQLite connections. The dashboard only calls the API.

```mermaid
flowchart LR
  J[events.jsonl] --> I[ingest]
  I --> B[(Bronze raw_events)]
  I --> Q[(quarantine)]
  B --> N[build]
  N --> S[(Silver measurements)]
  N --> E[(expected_slots)]
  S --> H[SQL hourly aggregate]
  E --> H
  H --> G[(Gold asset_hourly)]
  S --> R[versioned rules]
  R --> C[(incidents and transitions)]
  B --> A[read-only API]
  S --> A
  G --> A
  C --> A
  A --> U[accessible browser view]
```

One source event is one asset/metric/15-minute observation. Gold grain is `(asset_id, metric, UTC hour)` and incident grain is one contiguous threshold-breach episode under one rule version. Stable incident IDs derive from asset, metric, rule version and episode start. Event time determines Gold hour, not ingestion time. A build recomputes only hours receiving new expected slots or new accepted Silver measurements; incident episodes are recomputed from persisted Silver when measurements change. The 48-hour lateness watermark is relative to the greatest previously normalized event time, not wall-clock time. Older events remain in Bronze and receive a `LATE_REVIEW` quarantine record; an explicit backfill path is pending.

`GET /api/incidents/{id}/lineage` returns the incident, first source raw event/hash, normalized measurement, Gold hour and transition records. The API does not mutate data. `GET /api/quality` makes expected-versus-received counts visible even when zero GOOD readings exist.

**Trade-offs:** SQLite WAL supports one local writer with concurrent readers but not distributed writes. Recomputing all incident episodes is simple and deterministic at this demonstration scale; a much larger fleet would partition that work. The threshold is illustrative, not calibrated to real equipment. The current local UI presents data from the API; no public hosted API exists.
