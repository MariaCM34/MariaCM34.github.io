# Modernize Studio

**Public demonstration with fictional business data.** This is a limited, deterministic proof of how a small reviewed T-SQL subset could be documented for Snowflake-compatible SQL. It is not a general migration system. No SQL is executed or sent to a service.

## Business problem

A team evaluating a platform migration needs a traceable view of what changed and what to test. A plausible-looking rewrite is not enough: unsupported syntax, string literals, data types, and result equivalence need explicit treatment.

## Behavior and architecture

Open `/projects/modernize-studio/` from a local HTTP server. Choose one of three synthetic examples, inspect or edit the T-SQL input, then select **Review conversion**. The `engine.mjs` allowlist accepts only the exact three reviewed templates. It returns a predefined Snowflake-compatible output and a list of changes. Any modified or unrecognized input receives an unsupported state with no output. This deliberate constraint avoids pretending a regular expression is a SQL parser. The input remains editable so the refusal is visible and testable.

The sample cases cover `TOP` to `LIMIT`, `ISNULL` to `COALESCE`, and simple bracketed identifiers. One case includes `ISNULL` inside a comment and quoted string, both preserved unchanged. The examples use fictional `demo_sales` and `demo_orders` tables. They are examples of SQL text, not executed queries. `ui.mjs` only renders the browser state; `engine.mjs` owns the allowlist and validation comparison.

The validation panel compares two tiny, bundled synthetic JavaScript row arrays. Switch to **Introduce mismatch** to see amount, duplicate, and record equivalence failures. The row-count and null-count checks remain green in this scenario. These are suggested classes of migration checks, not evidence of a production migration. Schema/type checks and actual SQL equivalence require an authorized source and target environment and are **not implemented**.

## Reproduce

From the repository root:

```powershell
python -m http.server 8000
```

Open `http://localhost:8000/projects/modernize-studio/` in a browser. Run deterministic tests:

```powershell
node --test projects/modernize-studio/engine.test.mjs
```

Observed locally on 14 October 2026: **5 tests passed, 0 failed**. Cases cover all three supported examples, unsupported dialect/input, quotes and comments, equivalent fixture rows, and a deliberate mismatch.

## Limits and risks

- Only three exact reviewed templates are supported. Changing spacing, comments, identifiers, or SQL text causes a refusal. This is intentionally narrower than a parser.
- No SQL engine, database, dbt compilation, or migration execution is bundled. The displayed SQL is explanatory output.
- Identifier casing, reserved words, null semantics, collation, numeric precision, sort ties, and date/time behavior can differ across systems. Human review is required before real migration.
- The UI is bilingual where practical; sample SQL titles and warning text remain in English.
