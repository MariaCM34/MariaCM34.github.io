# MariaCM34 — Data Engineering Portfolio

A bilingual (Spanish/English), GitHub Pages–compatible portfolio. Source owner: `MariaCM34`.

This repository ships with an existing professional homepage and scoped specifications for **three independent demo products**. Each demo starts as *not implemented*; agents must deliver it and verify it before any homepage link claims a live demo.

- [Tonight's sprint and gates](SPRINT.md)
- [Instructions for local agents](AGENTS.md)
- [Getting started on Windows](START_HERE_ES.md)
- [Agent assignment prompts](prompts/)
- [Evidence and portfolio rules](PORTFOLIO_POLICY.md)

## Development

After creating the project files, preview locally from the repository root:

```powershell
python -m http.server 8000
```

Browse `http://localhost:8000`. Automated smoke tests (Node.js 20+):

```powershell
node --test tests/*.test.mjs
```

No production credentials or proprietary client materials should be committed. GitHub Pages is static; **a live LLM cannot safely use a secret API key from browser JavaScript**.
