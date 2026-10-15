# EnergyPulse data dictionary

| Dataset | Grain / key | Main fields | Quality and provenance |
| --- | --- | --- | --- |
| `events.jsonl` | One asset/metric/15-minute event; `event_id` | source/site/asset IDs, UTC observation, metric, numeric value, compatible unit, quality, schema v1 | Synthetic; manifest seed and SHA-256 |
| `raw_events` (Bronze) | One accepted `event_id` | original canonical JSON, SHA-256, ingestion time/run ID, processed flag | Identical retries no-op; conflicting payload quarantined |
| `quarantine` | One rejected input attempt | raw line, event ID if extractable, reason, run ID/time | `CONTRACT_INVALID`, `UNIT_MISMATCH`, `UNKNOWN_ASSET`, `ID_CONFLICT`, `NATURAL_KEY_CONFLICT`, `LATE_REVIEW` |
| `measurements` (Silver) | One valid normalized `event_id` | asset/site, metric, value, unit, source quality, UTC time, build run ID | Foreign key to Bronze; only GOOD values count toward Gold coverage |
| `expected_slots` | `(asset_id, metric, observed_at_utc)` | active asset cadence calendar | Reveals missing data independently of received rows |
| `asset_hourly` (Gold) | `(asset_id, metric, hour_utc)` | expected/received counts; mean/max/min; `NO_DATA`/`PARTIAL`/`COMPLETE`; build run ID | SQL aggregate over expected slots left-joined to GOOD Silver readings |
| `incidents` | Stable episode ID | open/closed times, rule version, threshold/operator, first/last source event, build run ID | A contiguous breach episode, not one alert per reading |
| `incident_transitions` | `(incident_id, state, transition_at_utc)` | state, event ID, rule version | Deterministically recomputed history for the current synthetic evidence set |
| `pipeline_runs` | `run_id` | stage, source hash, counts, status, duration timestamps, error | Structured operational evidence |

Allowed units: temperature `C`, vibration `mm/s`, pressure `bar`. All observation timestamps are UTC at exact 15-minute boundaries. SQL `NULL` in an absent Gold aggregate means no observed GOOD value; zero is not substituted. This synthetic contract is mirrored by `v2/contracts/energy_event_v1.schema.json` and Pydantic runtime validation.
