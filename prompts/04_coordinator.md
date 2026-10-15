# Coordinator / reviewer — integration AFTER agent commits

Read `AGENTS.md`, `SPRINT.md`, `PORTFOLIO_POLICY.md`. This task starts ONLY after receiving three agent reports and verifying branch state. You may change root `index.html`, root README, CI and cross-project navigation; do not silently rewrite agents' own project implementations.

Review independently: inspect diffs, run local HTTP server, test at desktop and mobile, run `node --test tests/*.test.mjs`, scan for secrets and fictional claims and dead links. Verify each project's README matches behavior.

Homepage should become a polished bilingual recruiter-facing portfolio combining:
- real *professional experience case studies* (anonymous, no source code claim)
- publicly reproducible *demo projects* (synthetic; buttons **Live demo**, **Source code**, **Technical case study** only when corresponding target exists)
- truthful skills and education
- verified training credentials ONLY when exact certificates/evidence are supplied (Claude Academy courses are not professional certificates). Never invent Databricks credentials.

Keep strong minimal visual system, no carousel animation overload, accessible contrast, responsive cards. Design before writing. Do not claim three demos are ready if any isn't.

Validate public GitHub Pages URLs by visiting them after approved push. Report exact working URLs and failed checks. Do not publish to an account different from `MariaCM34`.
