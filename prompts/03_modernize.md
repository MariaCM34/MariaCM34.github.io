# Agent C — Modernize Studio: explainable SQL modernization

Read `AGENTS.md`, `SPRINT.md`, `PORTFOLIO_POLICY.md`. Own ONLY `projects/modernize-studio/**` in an isolated branch/worktree.

Build a sophisticated interactive static proof-of-concept for migrating a small, intentionally defined subset of **T-SQL into Snowflake-compatible SQL/dbt style**, with an explicit supported-subset disclaimer. Do not claim a general automatic migration system.

Must deliver: choice of 3+ synthetic legacy T-SQL examples; input code; safe transformation for documented simple constructs; output SQL and side-by-side highlighted changes; automated suggested validation checks (schema, row-count, nulls, duplicates, equivalence where simulatable); explicit risks/warnings; user-accessible README and project notes. If input outside supported subset, gracefully explain unsupported; NEVER silently fabricate conversion.

At least 4 tests: supported feature, unsupported dialect construct, quotes/comments safety, mismatch detection. If no SQL parser is available, limit to 2 or 3 known templates and label deterministic proof rather than unsafe regex-based general conversion. No LLM claim unless actually integrated securely.

No root `index.html` changes; write only owned project path, commit and report test results/limitations/URL path/commit SHA.
