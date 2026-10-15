# Portfolio V2 engineering status

**Date:** 2026-10-15. **Branch:** `portfolio-v2`. **Public release:** V1 remains on `main`; V2 has not been merged or deployed to GitHub Pages. This file records tested implementation state, not a claim of production use.

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

## Static showcase in progress

`v2/showcase/` exports a small curated `evidence.json` from the three executed local systems and renders it with a responsive bilingual static page. It labels the export frozen/synthetic and distinguishes it from the runnable local APIs. A local Playwright flow passed on 1280×800 and 390×844, exercising the sensor gap, governed metric/currency selection, a failed typed diff, keyboard language switching, and missing-export state. The showcase is **uncommitted and not yet in remote CI** at the time of this entry.

## Next actions

1. Review the static export for accidental local paths, secrets, and misleading claims; complete its runbook.
2. Commit only curated showcase/workflow/status files, push `portfolio-v2`, and require the expanded CI to pass including regeneration and browser test of the static export.
3. Keep `main` and public Pages unchanged until V2 has an explicit release decision. Recheck remote refs and report the precise verified URLs and SHA.

Gate 0/1 audit and architecture decisions are in [`docs/06_ARCHITECTURE_GATE_1.md`](docs/06_ARCHITECTURE_GATE_1.md). Reproduction starts at [`../v2/README.md`](../v2/README.md).
