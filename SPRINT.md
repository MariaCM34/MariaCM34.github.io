# Tonight's sprint — one exceptional release, three credible demos

## Goal
Ship a recruiter-ready bilingual homepage with a **working and polished EnergyPulse flagship**, two narrower interactive demos if time permits, links to source/tests/architecture, and visible honesty about the data and technical limitations.

## Jobs-to-be-done
- A recruiter understands experience in 15 seconds.
- A technical lead can try a useful interaction in 60 seconds.
- They can inspect the code and verify the test story in 2 minutes.

## Agent ownership — parallel isolated paths

| Agent | Branch | Owns | Must NOT change |
|---|---|---|---|
| A Analytics | `feat/ask-your-data` | `projects/ask-your-data/**` | root `index.html`, other projects |
| B Telemetry | `feat/energypulse` | `projects/energypulse/**` | root `index.html`, other projects |
| C Modernization | `feat/modernize-studio` | `projects/modernize-studio/**` | root `index.html`, other projects |
| Coordinator/QA after merge | `main` | root portfolio, links, testing, deploy | never silently rewrite agent outputs |

## Timebox (relative to starting)

- **0:00–0:20** Login, worktree setup, assign owners, lock specs and no-go decisions.
- **0:20–1:50** 3 agents implement vertical slices in parallel. At +45 min require screenshots/working page or reduce scope.
- **1:50–2:40** Each agent completes tests, documentation, keyboard/mobile checks, commits.
- **2:40–3:20** Coordinator reviews, merges successful branches one by one, makes integration links and homepage polish.
- **3:20–4:00** Verify on GitHub Pages from an incognito browser, sanity-check metadata, bilingual content, real source links. Publish only qualified components.

If the time budget ends, **ship EnergyPulse only** and label or hide the unfinished demos. A working product is better than three fake demos.

## Acceptance gates

### Gate 0 — Source integrity
- No real client assets or private credentials; synthetic/fictional data labeled; Git public repo access confirmed.

### Gate 1 — Function
- Demo runs in browser via local HTTP server, with 3+ meaningful user interactions and sensible failure states.
- SQL only executed against bundled synthetic data; no unrestricted eval, code execution or network calls to hidden services.

### Gate 2 — Quality
- Test suite passes; meaningful validation cases; mobile layout 360px and desktop tested.
- Each demo README has architecture, tests, limitations and exact commands.

### Gate 3 — Portfolio integration
- Every live 'Demo', 'Source', or 'Read case study' link works and has matching content.
- Overview is Spanish + English; badges are evidence-backed; no made-up numbers.

### Gate 4 — Publish
- `https://mariacm34.github.io/` loads without signing in, and each published demo URL is tested.
- User reviews public personal details; HTTPS is enabled.

## No-go: do not block tonight for
- Paid Snowflake/Databricks accounts, cloud credentials, running Airflow servers, Kafka clusters, Claude API billing, integrating client systems.
- Agent framework abstraction or a complex Kubernetes/docker deployment.
