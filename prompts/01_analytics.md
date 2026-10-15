# Agent A — Ask Your Data: transparent natural-language analytics proof

Read `AGENTS.md`, `SPRINT.md`, `PORTFOLIO_POLICY.md`. Own ONLY `projects/ask-your-data/**`. Use one dedicated branch/worktree.

Goal: build a polished static interactive 'Ask Your Data' demo that convinces a Data Engineering / Analytics Engineering recruiter. Business scenario: fictional retail company, synthetic sales/order/product data.

Must implement:
1. An attractive responsive HTML/CSS/JS user interface with ES/EN support, input prompts and >=5 suggested natural-language business questions.
2. A **safe, explicit allowlisted semantic query mapper** for this prototype (NOT advertised as a live LLM). Display the matched intent, executable SQL, SQL results, and a chart/table with source and date scope. A local SQL engine (SQLite WASM or DuckDB WASM) is preferred if feasible in time; if not possible, use an honest deterministic JS engine with clearly labeled illustrative SQL templates and documented limitations. Do NOT fake SQL execution.
3. Synthetic fixture CSV/JSON with predictable business questions. Cover comparisons, trends, top products, cancellations, and gross/net sales. Clearly state data is synthetic.
4. Source and evidence panel: number of rows scanned, filters, query template, how result was computed, and which cases are unsupported.
5. At least 4 meaningful tests: valid question, unsupported question, date filtering, negative/null/edge data. Actual test outcomes in README.
6. Independent route `/projects/ask-your-data/`; `README.md` includes data model, query safety, architectural decisions, reproducibility, limitations.

Respect scope. Do not modify root `index.html` or other project folders; coordinator integrates links later. Do not claim a Claude-powered agent or LLM feature unless it actually exists with a secure backend and tested evaluations; a browser-hosted secret is prohibited.

Work until tests pass or produce a precise blocker. Final report must include files, actual test commands/results, URL path, commit SHA.
