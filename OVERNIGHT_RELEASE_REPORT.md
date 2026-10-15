# Overnight portfolio release report

**Status:** Published and verified anonymously on GitHub Pages. Checked 14 October 2026, 23:30 America/Bogota, before the 15 October 08:00 deadline.

## Working public URLs

| Page | URL | Verification |
| --- | --- | --- |
| Portfolio homepage | https://mariacm34.github.io/ | HTTPS 200; Spanish/English switch works |
| EnergyPulse flagship | https://mariacm34.github.io/projects/energypulse/ | HTTPS 200; synthetic readings and incident rule inspection work |
| Ask Your Data | https://mariacm34.github.io/projects/ask-your-data/ | HTTPS 200; suggested question computes chart/table; unsupported question clears prior evidence |
| Modernize Studio | https://mariacm34.github.io/projects/modernize-studio/ | HTTPS 200; reviewed template produces output; unsupported input is refused |

All six homepage links to the three GitHub source folders and their architecture/test READMEs returned HTTP 200 without signing in. Public project JavaScript and the synthetic JSON fixture also returned HTTP 200. GitHub Pages deploys `main` from the repository root; the [Pages deployment run](https://github.com/MariaCM34/MariaCM34.github.io/actions/runs/38681666249) completed successfully for release commit `ef7c00f94838423138de86a2fe988f0d65b24084`.

## Delivered

- **EnergyPulse:** fictional facility, 3 assets × 3 days × 24 hourly UTC readings, SVG trend and threshold, exact anomaly explanations, selected day/asset/signal, simulated replay, raw table, CSV, ES/EN. Fixture generation, rules and view are separate. No live telemetry.
- **Ask Your Data:** fictional retail fixture of 17 order lines, five allowlisted intents, six suggested questions, date filtering, computed chart/table and provenance, illustrative SQL clearly marked as not executed, ES/EN, validation and unsupported states.
- **Modernize Studio:** three exact reviewed T-SQL examples with documented Snowflake-compatible output, explicit changes and risks, synthetic validation comparison with a mismatch scenario, ES/EN, refusal for input outside the allowlist.
- **Homepage:** bilingual project cards with functional demo, source and architecture/test links, separate from anonymized professional case studies. Removed the unsupported “100+ DAGs” numerical claim before the first public push.

## Tests and release checks

- `node --test` on the integrated `main`: **23 passed, 0 failed** (5 portfolio/integration, 6 EnergyPulse, 7 Ask Your Data, 5 Modernize Studio). The [GitHub Actions portfolio check](https://github.com/MariaCM34/MariaCM34.github.io/actions/runs/38681666903) also completed successfully for the release commit.
- Local HTTP server: homepage plus eight project pages/assets returned **9/9 HTTP 200**. After Pages propagation, the homepage, three demo routes and three key assets returned **7/7 HTTPS 200**.
- Anonymous public browser: switched homepage to English; opened EnergyPulse and inspected `Temperatura > 78.0 °C`; ran an Ask Your Data question and saw monthly net sales; ran a Modernize Studio conversion. The Ask Your Data unsupported state was also checked locally after a successful result.
- At a 360 px viewport, all four published pages had document width 345 px within the viewport, with no horizontal overflow. Desktop and mobile visual checks were performed locally; the published Modernize Studio mobile layout was captured again after deployment.
- Tracked-file credential pattern scan before this report: **33 files, 0 flagged**. Project JavaScript makes no external service request; Ask Your Data fetches only its bundled relative JSON fixture. No client data, paid service or browser API key was added.

## Commits and deployment

- Local baseline: `94c4a27e3b8a13a0ef322aad0e70be3b7eec5bf3`; public-claim cleanup: `5833a0143077b18f9eb24ab682854d6d75e38458`.
- EnergyPulse feature: `af8e2894fc09e4d01f90ad45b56510da8bb9fdcb`.
- Ask Your Data feature and evidence-state fix: `65cbde7a8c3ffa2e40b874256ca9c07fddb931e8`, `6554259946a0c9cc27b910e1bf6b1c39c625972e`.
- Modernize Studio feature and language-state fix: `cf8a6c2c8fbfda2376850b355550a413e355f015`, `bb77bb8e594d26b6ee23eec88c1d37f34e9894f0`.
- Integrated release on `main`: `ef7c00f94838423138de86a2fe988f0d65b24084`. Ordinary push succeeded; no force push or history rewrite. This report is committed separately after release verification.

## Limits and follow-up

The demonstrations use small deterministic fixtures and illustrative rules. EnergyPulse does not monitor real equipment; Ask Your Data does not run SQL or an LLM; Modernize Studio is not a general SQL parser or migration engine. Each project README gives its precise test scope and reproduction commands.

The original homepage's qualitative professional and education statements were supplied in this workspace and were not independently checked against a CV master during this release. The user should review those statements and public LinkedIn details before using the portfolio for applications. No private phone, residential address, unverified certification badge, or client metric was added.
