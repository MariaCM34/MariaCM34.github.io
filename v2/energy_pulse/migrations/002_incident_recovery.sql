ALTER TABLE incidents ADD COLUMN gap_count INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS reviewed_backfills (
  event_id TEXT PRIMARY KEY REFERENCES raw_events(event_id),
  reason TEXT NOT NULL,
  reviewed_at_utc TEXT NOT NULL,
  build_run_id TEXT NOT NULL REFERENCES pipeline_runs(run_id)
);

INSERT INTO schema_migrations(version) VALUES (2);
