# Agent B — EnergyPulse FLAGSHIP: telemetry operations dashboard

Read `AGENTS.md`, `SPRINT.md`, `PORTFOLIO_POLICY.md`. Own ONLY `projects/energypulse/**` on your own branch/worktree.

Make this the PREMIUM portfolio flagship: responsive, visually elegant, business-centered, confidently interactive; spend extra effort on information architecture and measured operations behavior. Fictional industrial facility with seeded deterministic synthetic sensor telemetry. This is a standalone project, NOT a copy of client historian/FDC work.

Required interactions: asset dropdown (3+ assets), time window/day filter, replay a period of readings, inspect anomaly with explanation of exact violated rule. Provide clear metric cards, real rendered charts (Canvas/SVG), simple incident timeline, table of raw measurements and data provenance.

Architecture must separate synthetic fixture generation from anomaly rules and from view rendering. At least 4 tests on deterministic data: anomaly detection, false positives, empty window, asset selection. No fake 'streaming live' labels; use 'replay of simulated data'.

README: business problem, sources=synthetic, tradeoffs, schema, how to reproduce, observed tests, limitations, and future Databricks streaming adaptation marked *not implemented*. ES/EN where feasible.

No root index changes, no other project changes; commit only owned files. Final report files, actual tests, URL path, commit SHA.
