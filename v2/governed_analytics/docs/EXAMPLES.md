# Executed examples from the default synthetic seed

Observed with 4,000 orders, 8,000 lines, 711 returns, and 12 product records. Date window is `[2026-04-01, 2026-06-01)` UTC. The exact compiled SQL is returned as `sql_executed` by `/api/query` and written into the evidence export. Values below are **integer minor units**; USD and COP must not be added together.

| Governed question / request | Observed output |
|---|---|
| "What were monthly net sales in USD?" `net_sales`, USD | April 6,145,024 (3,102 sale lines, 164 accepted returns); May 5,954,493 (2,960 sale lines, 173 accepted returns). |
| "What were monthly gross sales in USD?" `gross_sales`, USD | April 6,308,724; May 6,121,401. |
| "How many eligible orders were cancelled?" `cancellation_rate`, USD | April 123 / 1,364 = 9.0176%; May 119 / 1,303 = 9.1328%. |
| "Which categories contributed net sales?" `net_sales_by_category`, USD | April parts 2,030,844, supplies 1,386,337, tools 2,727,843. These sum to April's net sales. |
| "Show only tools net sales" `net_sales`, USD, category tools | April 2,727,843; May 2,643,614. |

The generated SQL is not a display approximation. For the first question, the executed statement is a `WITH sales AS (...)`, `returns AS (...)`, `keys AS (...)` query: sales and accepted returns are grouped separately by UTC month and currency, then joined on those group keys. The exact full text and bound values appear in the API response; the integration test re-executes them against the read-only snapshot and asserts identical rows. Query IDs and elapsed times vary by run, so they are not fabricated here.

Refusal example: `{"metric":"net_sales","start":"2026-04-01","end":"2026-06-01","currency":"USD","sql":"DROP TABLE raw_orders"}` returns 422 with a refusal query ID and no result/SQL. The audit lookup for that ID returns `REFUSED`; the source table remains present. Arbitrary natural-language text is also unsupported, because there is no LLM integration.
