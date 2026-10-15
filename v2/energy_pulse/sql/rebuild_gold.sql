INSERT INTO asset_hourly (
  asset_id, metric, hour_utc, expected_samples, received_samples,
  avg_value, max_value, min_value, quality_status, build_run_id
)
SELECT e.asset_id, e.metric, substr(e.observed_at_utc, 1, 13) || ':00:00Z' AS hour_utc,
       COUNT(*) AS expected_samples,
       COUNT(m.event_id) AS received_samples,
       AVG(CASE WHEN m.source_quality = 'GOOD' THEN m.value END) AS avg_value,
       MAX(CASE WHEN m.source_quality = 'GOOD' THEN m.value END) AS max_value,
       MIN(CASE WHEN m.source_quality = 'GOOD' THEN m.value END) AS min_value,
       CASE WHEN COUNT(m.event_id) = 0 THEN 'NO_DATA'
            WHEN COUNT(m.event_id) < COUNT(*) THEN 'PARTIAL'
            ELSE 'COMPLETE' END AS quality_status,
       :run_id
FROM expected_slots e
LEFT JOIN measurements m
  ON m.asset_id = e.asset_id AND m.metric = e.metric
 AND m.observed_at_utc = e.observed_at_utc AND m.source_quality = 'GOOD'
WHERE substr(e.observed_at_utc, 1, 13) || ':00:00Z' IN
      (SELECT hour_utc FROM affected_hours)
GROUP BY e.asset_id, e.metric, substr(e.observed_at_utc, 1, 13)
ON CONFLICT(asset_id, metric, hour_utc) DO UPDATE SET
  expected_samples=excluded.expected_samples,
  received_samples=excluded.received_samples,
  avg_value=excluded.avg_value,
  max_value=excluded.max_value,
  min_value=excluded.min_value,
  quality_status=excluded.quality_status,
  build_run_id=excluded.build_run_id;
