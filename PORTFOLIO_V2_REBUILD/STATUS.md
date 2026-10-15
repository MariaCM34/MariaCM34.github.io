# Portfolio V2 engineering status

**Date:** 2026-10-15. **Branch:** `portfolio-v2`. **Public release:** V1 remains on `main`; V2 has not been merged or deployed to GitHub Pages. This file records tested implementation state, not a claim of production use.

## Independent release audit update

- A clean checkout of source commit `f26aed45d0ea8fb019dbe292ac442426a62c54a6` ran all three generators/loaders/reconcilers twice. The curated static export was regenerated with that source commit and reproduced exactly as structured data except for export time. An earlier snapshot from `aac6680` had the same observed results but OS-dependent hashes/run IDs; `.gitattributes`, LF JSONL/case writers, and regression checks corrected that provenance defect.
- Independent source arithmetic reconciled Energy 106 unique JSONL IDs to Bronze/Silver, a 3/4 missing-slot hour and the 84.3 °C incident; Analytics 4,000 unique orders, 8,000 unique lines and four monthly currency totals (April USD 6,145,024 minor units); Migration 17 distinct cases and the A-001 10.00-versus-11.00 discrepancy executed on SQLite and DuckDB.
- A mobile visual audit found 399 px document width at a 390 px viewport in Governed Analytics when a result was visible. The grid was bounded, the result table became keyboard-scrollable, and the browser regression now checks the visible result. Eight final local screenshots cover desktop/mobile Energy, Analytics, Migration and showcase; all have no document-level horizontal overflow. Showcase links now describe code/local setup accurately.
- Final clean-checkout local result: **44 V2 Python tests passed**, **23 V1 Node tests passed**, **four desktop/mobile browser flows passed**, `pip check` found no broken requirements. One Starlette/httpx deprecation warning remains. Credential-pattern and curated-export path-marker scans found no matches; generated database/report files are ignored.
- The release decisions and exact open gates are in [`../V2_RELEASE_READINESS.md`](../V2_RELEASE_READINESS.md). All three are **CONDITIONAL PASS** for the documented local reference scope; public V2 Pages verification remains unavailable by instruction. Local `portfolio-v2` is ahead of the remote at this audit checkpoint; final evidence/report commit, push and CI are next. Remote `main` must remain V1.

## Preservation and recovery

- Verified local and remote `main` at `adcbfa7175acd65eba4cc322c17ae6ac4f382c7a`; tagged it locally as `v1-preserved-adcbfa7`. The development branch was created from this SHA without rewriting history.
- Located the original EnergyPulse slice `044b7e94ae8c69eb1148dd4db460286469adc96e`, recovered interrupted agent outputs without resetting them, independently reviewed their valid work, then integrated all three packages in `aac668016c25f9dfe46e01de18dd50f0162c4e7b`.
- The user-supplied V2 specification package and overnight instruction file remain untracked and preserved. Existing V1 worktrees were not changed. A clean detached checkout at `.worktrees/v2-verify` was used for reproduction.
- The `portfolio-v2` development branch was pushed to the personal remote. This changed neither remote `main` nor the public Pages site. No external repository or paid service was used.

## Product state and evidence

| Product | Executable flow | Verified local outcome | Remaining limits |
| --- | --- | --- | --- |
| EnergyPulse | Deterministic JSONL producer → validated SQLite Bronze/Silver/Gold → incident lifecycle → read-only FastAPI → browser dashboard | 106 of 108 expected events emitted and ingested; 106 Silver, 27 Gold, one incident with source-event lineage. Late backfill, rollback/retry, schema migrations, gap-aware chart and negative rules tested. | Synthetic 12-slot fixture; no real sensors, HA, distributed stream, or production safety role. |
| Governed Analytics | Synthetic source records → DuckDB facts and version-linked Parquet → allowlisted parameterized SQL → independent reconciliation → API/dashboard | 12,723 source rows. Multi-line orders, partial refunds, currency separation, published-run consistency and refusal audit tested. | No FX conversion or arbitrary natural-language SQL; local single-node reference. |
| Migration Assurance | SQLGlot reviewed AST translation → actual SQLite and DuckDB execution → typed result comparison → persisted JSON/HTML reports and viewer | 17 cases: 11 PASS, two intentional FAIL, four REVIEW; zero unexpected decisions. Invalid syntax and false ordered-PASS regression tested. | Only documented SQL subset and fixtures; PASS is not blanket production equivalence. |

Each package has contracts, architecture diagram, data dictionary, ADR/runbook, test evidence, and a guided local demonstration under `v2/`. All businesses and records are fictional/synthetic.

## Tests and independent review

- Local combined Python suite: **44 passed, zero failed**, one Starlette/httpx deprecation warning. Per-module statement coverage gates of 85% passed: Energy contracts 90.9%, pipeline 93.3%; Analytics pipeline 88.2%, semantic 95.0%; Migration engine 85.8%.
- V1 regression: `node --test`, **23 passed**. Three Playwright desktop/mobile flows passed against running local applications. A clean detached checkout reproduced the same source-to-result flows and tests.
- Independent cross-review found and prompted fixes for EnergyPulse false coverage and out-of-calendar lineage, Analytics Parquet/warehouse publication and SQLite audit handles, and Migration Assurance's false ordered-comparison PASS. Each has a regression test.
- Remote [GitHub Actions run 38751666431](https://github.com/MariaCM34/MariaCM34.github.io/actions/runs/38751666431) **completed successfully** at `aac6680`, repeating V1/V2 tests, coverage gates, and the three live browser flows.
- Filename-only secret-pattern scan of V2 source and workflow found no matches. Generated databases, Parquet, reports, dependencies, and coverage are Git-ignored. Public evidence must still be reviewed before any Pages promotion.

## Static showcase and publication boundary

`v2/showcase/` exports a small curated `evidence.json` from the three executed local systems and renders it with a responsive bilingual static page. It labels the export frozen/synthetic and distinguishes it from the runnable local APIs. A local Playwright flow passed on 1280×800 and 390×844, exercising the sensor gap, governed metric/currency selection, a failed typed diff, keyboard language switching, and missing-export state. The committed snapshot has 106 Bronze rows, 12,723 governed source rows, and 17 executed migration decisions. A repeat export matched the committed payload exactly after excluding only its source-commit and export-time metadata. A content scan found no local absolute paths or credential markers in `evidence.json`.

Commit `a72b337356682f18728b54f69c5c4f2833e608aa` added the showcase and expanded CI to regenerate it. [GitHub Actions run 38753659110](https://github.com/MariaCM34/MariaCM34.github.io/actions/runs/38753659110) **completed successfully**, including the three application browser flows and the static showcase browser flow. Commit `a2ed03fb2e104e2f741ed6dc3169a9bfbea581e0` hardened the exporter to check the EnergyPulse source hash against the manifest and successful ingestion, plus exact reviewed migration case IDs/statuses. [GitHub Actions run 38754152711](https://github.com/MariaCM34/MariaCM34.github.io/actions/runs/38754152711) **completed successfully** for that commit.

## Next actions

1. Commit only curated final evidence, screenshots and audit documentation; push `portfolio-v2`, then require the final CI run to pass and verify both remote branch refs.
2. Keep public Pages unchanged until a separately reviewed V2 release decision; remote `main` must remain `adcbfa7`.
3. Continue product QA against the three runbooks; the frozen page must never be presented as a live hosted application.

Gate 0/1 audit and architecture decisions are in [`docs/06_ARCHITECTURE_GATE_1.md`](docs/06_ARCHITECTURE_GATE_1.md). Reproduction starts at [`../v2/README.md`](../v2/README.md).
