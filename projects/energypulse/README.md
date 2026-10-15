# EnergyPulse — explainable telemetry operations demo

**Public demonstration. All assets, readings, and incidents are fictional and synthetic.** This static project does not use a production historian, client system, real telemetry stream, backend, external API, or AI model.

## Business problem

A fictional industrial facility needs to find readings outside asset-specific operating limits and explain each alert to an operator. The demo turns hourly measurements into traceable incidents: the selected asset and window, observed value, precise comparator and threshold, and timestamp remain visible. It illustrates a practical data engineering workflow without implying a deployment or measured business outcome.

## Try it

From the repository root:

```sh
python -m http.server 8000
```

Open `http://localhost:8000/projects/energypulse/`. A local HTTP server is required for JavaScript module loading. No installation or build step is needed.

The browser page supports:

1. Choose among Pump A, Compressor B, and Chiller C and filter to a UTC day or all three days.
2. Switch chart signals; inspect the actual SVG line, limit and flagged points.
3. Select an incident to see the exact violated rule and observed measurement.
4. Replay the selected readings at a fixed display interval. This is a replay of bundled simulated data, not live streaming.
5. Download the selected, synthetic readings as CSV, inspect the raw table, and switch between Spanish and English.

## Architecture and schema

`fixture.mjs` owns asset metadata and generates 216 deterministic readings: 3 assets × 3 days × 24 hourly UTC samples. Nine out-of-range points are deliberately injected. There is no randomness, network access or user data. `rules.mjs` selects windows and evaluates the three explicit rules. `app.mjs` handles browser state, SVG rendering, replay, CSV and translations; it does not define anomaly logic. `index.html` and `style.css` provide semantic page structure and responsive presentation.

Each reading has `id`, `assetId`, `timestamp` (ISO 8601 UTC), `temperature` (°C), `vibration` (mm/s), and `pressure` (bar). Each asset defines `temperatureLimit`, `vibrationLimit`, and `pressureFloor`. An anomaly occurs when temperature **>** its limit, vibration **>** its limit, or pressure **<** its floor. Equality is normal. Alert records retain the reading ID, metric, measured value, limit, comparator and unit.

This design trades realism for auditability: hourly samples and isolated threshold breaches make every outcome reproducible. It does not model noise, missing telemetry, correlated failures, alert persistence, operator acknowledgements, or maintenance context.

## Verification

Run from the repository root:

```sh
node --test projects/energypulse/tests/*.test.mjs
```

Observed on 2026-10-14: **6 tests passed, 0 failed** with Node.js 24.12.0. Cases cover fixture determinism and size, precise anomaly values, normal readings and equality boundaries, an empty window, selection isolation for two assets, and the full nine-incident count. Browser checks and HTTP results are reported to the sprint coordinator separately.

## Limits and future adaptation

All thresholds are illustrative and hard-coded. A real operating process would validate limits with engineering owners, handle time zones and late or missing events, version threshold definitions, and persist an audit log. The page makes no safety or predictive maintenance claim.

A future Databricks streaming adaptation could ingest a governed event stream, store versioned rules and late-event handling, and expose aggregate results through a secure service. **That adaptation is not implemented here.** This public release remains a static, browser-only demonstration.
