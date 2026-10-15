# Ruleset `sqlite-duckdb-subset-1`

| Rule | Input | Output / decision | Rationale and risk |
|---|---|---|---|
| `one-select` | One SQLite top-level SELECT | Continue | Prevent mutations and multiple-statement execution. AST validation may still be insufficient for hostile public input; CLI is trusted local only. |
| `declared-table` | `orders` and six declared columns | Continue; otherwise REVIEW | Scope is tied to synthetic schema. No implicit schema mapping. |
| `node-allowlist` | Reviewed AST node classes only | Continue; otherwise REVIEW with node name and SQL snippet | SQLGlot's broad translator support is not semantic approval. |
| `deterministic-limit` | LIMIT with ORDER BY | Continue; otherwise REVIEW | Unordered top-N result is nondeterministic. Ties may still need explicit secondary key in a real migration. |
| `sqlglot-render` | Accepted SQLite AST | DuckDB candidate SQL, unsupported translation raises REVIEW | Syntax conversion is not equivalence. SQLGlot may add explicit NULL ordering to preserve source semantics. |
| `typed-compare` | Executed rows + declared output types/key/order | PASS, FAIL, or REVIEW | Prevent row-count-only approval; decimal policy and type normalization must be explicit. |

No regex string substitution or hardcoded three-query response is used. The decision log records ruleset ID and applied translation rules; a future semantic rewrite would require its own version, unit tests and differential cases.
