-- One accepted source event per asset, metric, and 15-minute slot.
-- If legacy data already violates this invariant, migration fails visibly;
-- no evidence is deleted or silently selected as the winner.
CREATE UNIQUE INDEX ux_raw_asset_metric_slot
  ON raw_events(asset_id, metric, observed_at_utc);

INSERT INTO schema_migrations(version) VALUES (3);
