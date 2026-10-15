PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO schema_migrations(version) VALUES (1);

CREATE TABLE IF NOT EXISTS pipeline_runs (
  run_id TEXT PRIMARY KEY,
  stage TEXT NOT NULL CHECK(stage IN ('INGEST','BUILD')),
  started_at_utc TEXT NOT NULL,
  finished_at_utc TEXT,
  source_sha256 TEXT,
  accepted INTEGER NOT NULL DEFAULT 0,
  duplicate INTEGER NOT NULL DEFAULT 0,
  quarantined INTEGER NOT NULL DEFAULT 0,
  output_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK(status IN ('RUNNING','SUCCESS','FAILED')),
  error TEXT
);

CREATE TABLE IF NOT EXISTS raw_events (
  event_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  site_id TEXT NOT NULL,
  observed_at_utc TEXT NOT NULL,
  metric TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL,
  ingested_at_utc TEXT NOT NULL,
  ingest_run_id TEXT NOT NULL REFERENCES pipeline_runs(run_id),
  processed INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_raw_unprocessed ON raw_events(processed, observed_at_utc);
CREATE UNIQUE INDEX IF NOT EXISTS ux_raw_natural_key
  ON raw_events(source_id, asset_id, metric, observed_at_utc);

CREATE TABLE IF NOT EXISTS quarantine (
  quarantine_id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT,
  raw_line TEXT NOT NULL,
  reason_code TEXT NOT NULL,
  ingested_at_utc TEXT NOT NULL,
  ingest_run_id TEXT NOT NULL REFERENCES pipeline_runs(run_id)
);

CREATE TABLE IF NOT EXISTS measurements (
  event_id TEXT PRIMARY KEY REFERENCES raw_events(event_id),
  asset_id TEXT NOT NULL,
  site_id TEXT NOT NULL,
  observed_at_utc TEXT NOT NULL,
  metric TEXT NOT NULL,
  value REAL NOT NULL,
  unit TEXT NOT NULL,
  source_quality TEXT NOT NULL,
  build_run_id TEXT NOT NULL REFERENCES pipeline_runs(run_id)
);
CREATE INDEX IF NOT EXISTS ix_measurements_asset_time ON measurements(asset_id, metric, observed_at_utc);

CREATE TABLE IF NOT EXISTS expected_slots (
  asset_id TEXT NOT NULL,
  metric TEXT NOT NULL,
  observed_at_utc TEXT NOT NULL,
  PRIMARY KEY(asset_id, metric, observed_at_utc)
);

CREATE TABLE IF NOT EXISTS asset_hourly (
  asset_id TEXT NOT NULL,
  metric TEXT NOT NULL,
  hour_utc TEXT NOT NULL,
  expected_samples INTEGER NOT NULL,
  received_samples INTEGER NOT NULL,
  avg_value REAL,
  max_value REAL,
  min_value REAL,
  quality_status TEXT NOT NULL CHECK(quality_status IN ('NO_DATA','PARTIAL','COMPLETE')),
  build_run_id TEXT NOT NULL REFERENCES pipeline_runs(run_id),
  PRIMARY KEY(asset_id, metric, hour_utc)
);

CREATE TABLE IF NOT EXISTS incidents (
  incident_id TEXT PRIMARY KEY,
  asset_id TEXT NOT NULL,
  metric TEXT NOT NULL,
  opened_at_utc TEXT NOT NULL,
  closed_at_utc TEXT,
  status TEXT NOT NULL CHECK(status IN ('OPEN','CLOSED')),
  rule_version TEXT NOT NULL,
  threshold REAL NOT NULL,
  operator TEXT NOT NULL,
  first_event_id TEXT NOT NULL REFERENCES measurements(event_id),
  last_event_id TEXT NOT NULL REFERENCES measurements(event_id),
  build_run_id TEXT NOT NULL REFERENCES pipeline_runs(run_id)
);

CREATE TABLE IF NOT EXISTS incident_transitions (
  incident_id TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('OPEN','CLOSED')),
  transition_at_utc TEXT NOT NULL,
  event_id TEXT NOT NULL,
  rule_version TEXT NOT NULL,
  PRIMARY KEY(incident_id, state, transition_at_utc)
);
