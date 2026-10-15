# Portfolio V2 — independent release-readiness audit

**Audit date:** 2026-10-15. **Scope:** three synthetic, locally executable reference implementations and their frozen static showcase on `portfolio-v2`. This is a technical readiness decision for the documented reference scope, not a production certification. Public `main` remains V1 at `adcbfa7175acd65eba4cc322c17ae6ac4f382c7a`; V2 has not been merged or deployed to Pages.

## Decision

| Product | Decision | Evidence and release condition |
| --- | --- | --- |
| EnergyPulse | **CONDITIONAL PASS** | JSONL → persisted SQLite Bronze/Silver/Gold → incident lifecycle/API/chart/lineage passed clean-checkout and negative tests. Independently reconciled 106 unique events, the 3/4 missing-slot hour and the 84.3 °C incident source. Public release remains conditional on an actual Pages route check; the local unauthenticated API must stay loopback-only. No load/safety qualification is claimed. |
| Governed Analytics | **CONDITIONAL PASS** | 12,723 source rows → DuckDB/Parquet → governed SQL/API/chart; four monthly currency net totals matched independent source arithmetic. A confirmed 9 px mobile overflow and cross-checkout hash instability were fixed. Public release remains conditional on Pages verification and clear frozen-export positioning; arbitrary SQL/FX/hosted API are out of scope. |
| Migration Assurance | **CONDITIONAL PASS** | SQLGlot-reviewed subset → actual SQLite/DuckDB execution → typed reports/viewer; 17 unique cases gave 11 PASS, two deliberate FAIL, four REVIEW. A-001 was independently read as 10.00 in the source fixture and 11.00 in the target fixture and reproduced with both engines. Public release remains conditional on Pages verification. PASS never certifies an untested vendor migration or production cutover. |

There is no currently known blocking correctness defect within the declared local reference scope. **No project is approved as a deployed demo or production-ready system.** The final CI run at the audit correction commit and the V2 public URL remain the release gates; the latter is intentionally unavailable under the current instruction to preserve `main` and not publish V2.

## Adversarial findings and corrections

1. **[P1] Snapshot provenance was not portable.** The committed snapshot recorded source commit `aac6680`, but a clean Windows worktree changed source-code/model/fixture bytes from LF to CRLF. Analytics produced a different `run_id`; Migration fixture hashes changed even though results agreed. The old snapshot therefore could not be reproduced exactly from that commit in the tested checkout. Commit `248780f07c6744413dd7eb9d1f6878a1d5164360` pins LF checkout for V2 text and emits Analytics JSONL with LF on all OSes. Follow-up `f26aed45d0ea8fb019dbe292ac442426a62c54a6` gives generated Migration case JSON the same LF guarantee. A new snapshot was generated twice from a clean checkout of `f26aed4`; all exported fields matched except `exported_at_utc`. The old/new Analytics source hashes and run IDs changed (`38c7ff95…` / `8efb27e007e5dea3` → `5bd35572…` / `0d7bcd7fd9291b6c`), while the eight executed metric result sets, Energy evidence and Migration decisions remained equal. The new snapshot records `f26aed4` as its source implementation commit. Engine-version fields remain environment-specific and are intentionally shown rather than normalized away.
2. **[P2] Analytics result view overflowed on mobile.** A 390 px Chrome viewport had 399 px document scroll width when the SQL result was visible; the prior browser test checked only after hiding the result on an error. The grid/form min-width was bounded, the visible-result assertion added, and the result table made a keyboard-focusable horizontal-scroll region. The revised test and screenshot show zero page overflow.
3. **[P2] Showcase links overstated availability.** Three links labeled “Run the real application” opened repository folders. They now say “View code and local setup” in English and Spanish. No public API or Pages deployment is implied.
4. **[P3] Documentation lagged the integrated code.** The V2 overview and product evidence files still described CI, independent review, and static export as pending. They were aligned with observed commits and CI runs; the Analytics evidence file records the new reproducible run ID. Remaining performance, formal accessibility and public route evidence are explicitly open.

No speculative re-architecture was made. The reference stacks remain narrow: SQLite for telemetry state, DuckDB/Parquet for analytics, SQLGlot plus SQLite/DuckDB for bounded migration comparison, FastAPI only on loopback, and static GitHub Pages-compatible evidence. Python and browser dependencies are pinned in `v2/requirements.lock` and `v2/package-lock.json`; `pip check` reported **no broken requirements**. Generated databases, reports and local audit logs are ignored. Curated `evidence.json` contains no local absolute paths or credential markers in the audit scan. The showcase inserts exported text via `textContent`, not HTML interpolation.

## Independent data reconciliation

From persisted source files and databases, outside the application metric compiler:

- **EnergyPulse:** 106 JSONL event IDs are unique and equal the 106 Bronze IDs; Silver also has 106 rows. Chiller pressure at 00:00 UTC has 3 received / 4 expected and `PARTIAL`, not zero-filled. The incident's first event ID resolves to the source reading 84.3 °C and closes only after a recorded recovery event.
- **Governed Analytics:** 4,000 unique orders and 8,000 unique line IDs have valid order references. Source-level line arithmetic after discount, minus accepted returns in their UTC acceptance month, matches all four exported USD/COP monthly net values. April USD is **6,145,024 minor units**; currency values were never mixed. The warehouse and Parquet generation share run ID `0d7bcd7fd9291b6c` after the LF fix.
- **Migration Assurance:** 17 distinct case IDs match the reviewed registry; status counts are 11/2/4 PASS/FAIL/REVIEW with zero unexpected decisions. The deliberate mismatch fixture changes `A-001.amount` from `10.00` to `11.00`. Independent in-memory SQLite and DuckDB queries returned the corresponding values; the persisted report names the exact field and both row counts (5/5).

## Clean-checkout and test evidence

An isolated detached checkout `.worktrees/v2-audit-final` at `f26aed4` used the pinned local Python environment. The hosted [CI workflow](https://github.com/MariaCM34/MariaCM34.github.io/actions/workflows/v2-validation.yml) separately installs pinned dependencies in a fresh Linux runner. Reproduction commands, from a clean checkout with the documented `PYTHONPATH`, were:

```text
python -m energy_pulse.cli demo --out-dir v2/energy_pulse/data/generated/audit --slots 12
python -m analytics.pipeline all
python -m analytics.export
python -m migration_assurance.cli suite --out v2/migration_assurance/artifacts/audit
python v2/showcase/export.py --energy-db v2/energy_pulse/data/generated/audit/energy.sqlite --analytics-export v2/governed_analytics/data/export/analytics-evidence.json --migration-reports v2/migration_assurance/artifacts/audit --output v2/showcase/verification.json
python -m pytest v2/energy_pulse/tests v2/governed_analytics/tests v2/migration_assurance/tests -q
node --test
```

Observed locally: **44 Python tests passed**, one dependency deprecation warning; **23/23 V1 Node tests passed**; `pip check` found no broken requirements. Source-to-result runs produced Energy 106/108 expected, Analytics 12,723 accepted/0 rejected, Migration 17 assessed/0 unexpected. Four Playwright desktop 1280×800 and mobile 390×844 flows passed against local HTTP services, including failure/negative interactions. Screenshots were captured at desktop 1280×900 and mobile 390×844; all eight had no document-level horizontal overflow. The [last completed remote run before this audit](https://github.com/MariaCM34/MariaCM34.github.io/actions/runs/38754152711) passed at `a2ed03f`; final CI for the audit corrections must be inspected before promotion.

## Visual evidence

Captured with `node v2/audit_screenshots/capture.mjs` against actual local applications after data generation. These are screenshots of executed systems, not design mockups:

| Surface | Desktop | Mobile |
| --- | --- | --- |
| EnergyPulse incident and gap | [desktop](v2/audit_screenshots/energy-desktop.png) | [mobile](v2/audit_screenshots/energy-mobile.png) |
| Governed SQL result | [desktop](v2/audit_screenshots/analytics-desktop.png) | [mobile](v2/audit_screenshots/analytics-mobile.png) |
| Migration failed typed diff | [desktop](v2/audit_screenshots/migration-desktop.png) | [mobile](v2/audit_screenshots/migration-mobile.png) |
| Static evidence showcase | [desktop](v2/audit_screenshots/showcase-desktop.png) | [mobile](v2/audit_screenshots/showcase-mobile.png) |

## Open risks and recommendation

- Keep the local APIs bound to `127.0.0.1`; they have no public authentication, tenant isolation, or rate limit. Only the curated frozen export is suitable for static hosting.
- Energy thresholds are illustrative; no throughput, long-running recovery or calibrated industrial safety benchmark exists. Analytics has no FX/tax/shipping model or arbitrary SQL. Migration accepts only its reviewed SQL subset and tested fixture versions.
- Formal WCAG audit, cross-browser matrix beyond Chromium, dependency vulnerability advisory review, and public Pages verification remain undone. A successful unit/browser CI run is not evidence for those checks.
- Do not merge into `main` or publish V2 under the current instruction. After the final CI is green, the three packages may be presented as **local reference implementations with synthetic data**; promote the static showcase only through a separately reviewed release decision and then verify the public HTTPS route and links.
