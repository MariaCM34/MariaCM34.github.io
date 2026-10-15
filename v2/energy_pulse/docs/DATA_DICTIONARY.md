# EnergyPulse data dictionary

| Dataset | Grain / key | Main fields | Quality and provenance |
| --- | --- | --- | --- |
| `events.jsonl` | One asset/metric/15-minute event; `event_id` | source/site/asset IDs, UTC observation, metric, numeric value, compatible unit, quality, schema v1 | Synthetic; manifest seed and SHA-256 |
| `raw_events` (Bronze) | One accepted `event_id`; unique `(asset_id, metric, observed_at_utc)` across sources | original canonical JSON, SHA-256, ingestion time/run ID, processed flag | Identical retries no-op; conflicting payload or second source for the same slot quarantined |
| `quarantine` | One rejected input attempt | raw line, event ID if extractable, reason, run ID/time | Includes `NONFINITE_VALUE`, `UNIT_MISMATCH`, `UNKNOWN_ASSET`, `SITE_MISMATCH`, `ID_CONFLICT`, `NATURAL_KEY_CONFLICT`, `LATE_REVIEW`, `OUTSIDE_CALENDAR` |
| `measurements` (Silver) | One valid normalized `event_id` | asset/site, metric, value, unit, source quality, UTC time, build run ID | Foreign key to Bronze; only GOOD values count toward Gold coverage |
| `expected_slots` | `(asset_id, metric, observed_at_utc)` | active asset cadence calendar | Reveals missing data independently of received rows |
| `asset_hourly` (Gold) | `(asset_id, metric, hour_utc)` | expected/received counts; mean/max/min; `NO_DATA`/`PARTIAL`/`COMPLETE`; build run ID | SQL aggregate over expected slots left-joined to GOOD Silver readings |
| `incidents` | Stable episode ID | open/closed times, rule version, threshold/operator, first/last breach event, gap count, build run ID | One breach episode; gaps mark uncertainty and do not close it |
| `incident_transitions` | `(incident_id, state, transition_at_utc)` | state, source event ID, rule version | A `CLOSED` event ID refers to the first observed GOOD recovery reading |
| `reviewed_backfills` | One approved late `event_id` | review reason, UTC time, build run ID | Local CLI review evidence; production identity/access control is outside demo scope |
| `pipeline_runs` | `run_id` | stage, source hash, counts, status, duration timestamps, error | Structured operational evidence |

Allowed units: temperature `C`, vibration `mm/s`, pressure `bar`. All observation timestamps are UTC at exact 15-minute boundaries. SQL `NULL` in an absent Gold aggregate means no observed GOOD value; zero is not substituted. This synthetic contract is mirrored by `v2/contracts/energy_event_v1.schema.json` and Pydantic runtime validation.
