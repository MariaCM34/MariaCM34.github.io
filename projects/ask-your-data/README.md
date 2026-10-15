# Ask Your Data

An interactive, static analytics demonstration for a **fictional retail business**. All 17 order lines are synthetic and deterministic. The page maps a narrow set of English and Spanish business questions to explicit intents, then computes results locally in JavaScript. It does **not** use an LLM or execute the illustrative SQL shown in the interface.

## Try it

From the repository root, run `python -m http.server 8000`, then open `http://localhost:8000/projects/ask-your-data/`. The route is also compatible with GitHub Pages. Ask a suggested question, change dates, enter an unsupported question, or switch language.

## Business problem and architecture

A retail analyst wants quick, inspectable answers to common sales questions. `engine.js` contains a five-intent allowlist: monthly trend, top products, category comparison, cancellation rate, and gross/net sales. Pattern matching selects only one known intent. Arbitrary SQL, expressions, network calls, and code execution are not accepted. The browser loads `data/orders.json` via a relative path and renders the computed table, chart, row count, date filter, matched intent, and an illustrative SQL template. The SQL is documentation, not a claim of execution.

The fixture models one order line per row with `id`, ISO `date`, `product`, `category`, `quantity`, `unitPrice`, `discount`, and `status`. Gross sales sum `quantity × unitPrice` for completed lines. Net sales subtract discounts from completed lines and subtract the original discounted amount for returned lines. Cancellations contribute no sales. Invalid amount rows contribute zero to sales but still appear in scan and cancellation counts. The cancelled `S017` line intentionally has a null price to demonstrate that quality signal.

## Verification

Run `node --test projects/ask-your-data/tests/*.test.mjs` from the repository root. On 2026-10-14, seven tests passed, zero failed: bilingual intent mapping, unsupported input, date filter and empty range, cancellations and returns, null/negative amount handling, invalid dates, and a UI state regression ensuring that an unsupported question clears prior evidence. The test suite reads the same fixture the browser uses.

## Limitations and reproducibility

This is a fixed prototype, not general natural-language understanding. Some unsupported wording may match a broad keyword and return a known intent; users should inspect the matched intent. The dataset has only three months and three normal products, with USD amounts and no tax, shipping, partial returns, timezone conversion, or currency conversion. The chart is a basic bar view. SQL templates use explanatory `month(date)` syntax and are not bound to a SQL dialect. No user data leaves the browser. Recompute all outputs by reviewing the fixture and pure functions in `engine.js` or running the Node tests.
