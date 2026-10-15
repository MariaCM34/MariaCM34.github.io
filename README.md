# MariaCM34 — Data Engineering Portfolio

A bilingual, static engineering portfolio for GitHub Pages. The homepage separates anonymized professional case studies from three public demonstrations using fictional businesses and synthetic, deterministic data. No demo needs an API key, paid service, or private backend.

| Demonstration | Try it | Architecture, tests, limitations |
| --- | --- | --- |
| EnergyPulse · explainable telemetry | [Open demo](projects/energypulse/) | [Project README](projects/energypulse/README.md) |
| Ask Your Data · transparent analytics | [Open demo](projects/ask-your-data/) | [Project README](projects/ask-your-data/README.md) |
| Modernize Studio · bounded SQL examples | [Open demo](projects/modernize-studio/) | [Project README](projects/modernize-studio/README.md) |

## Run locally

From the repository root:

```powershell
python -m http.server 8000
```

Open `http://localhost:8000/` and any project route above. Run all automated tests with Node.js 20 or newer:

```powershell
node --test
```

Observed locally on 14 October 2026: **23 tests passed, 0 failed** (5 portfolio checks, 7 Ask Your Data checks, 6 EnergyPulse checks, 5 Modernize Studio checks). The project READMEs explain what those tests cover and how to reproduce the browser behavior. Browser routes require an HTTP server because project JavaScript modules and the local JSON fixture are loaded by the browser.

## Integrity

All demonstration readings and order data are seeded or bundled synthetic fixtures. EnergyPulse simulates replay, Ask Your Data computes in JavaScript and shows **illustrative SQL that is not executed**, and Modernize Studio accepts only three exact reviewed SQL examples. None is a claim about a client system or a production performance gain. For publication and evidence rules, see [PORTFOLIO_POLICY.md](PORTFOLIO_POLICY.md).
