# Synthetic schema and comparison contract

## `orders` input grain

One row per unique `order_id` in each fixture. Source and target fixture files are independently read and loaded into separate SQLite and DuckDB files. The target is **not** copied from an executed source database. The demo intentionally changes one target value and has another target fixture missing one key.

| Field | SQLite | DuckDB | Meaning |
|---|---|---|---|
| `order_id` | TEXT PRIMARY KEY | VARCHAR PRIMARY KEY | Synthetic business key, e.g. A-001. |
| `amount` | DECIMAL(12,2) affinity | DECIMAL(12,2) | Nullable synthetic currency-like amount; no currency conversion or financial ledger claim. |
| `status` | TEXT | VARCHAR | `paid`, `cancelled`, or `pending` in baseline fixture. |
| `region` | TEXT | VARCHAR | Synthetic region. |
| `quantity` | INTEGER | INTEGER | Units for arithmetic test. |
| `ordered_on` | TEXT | VARCHAR | ISO calendar date string, UTC convention; no timestamp/timezone conversion in subset v1. |

The baseline has five records. `A-002.amount` is NULL; `A-001` and `A-004` both have `10.00`; `paid` repeats three times. This exercises NULL, duplicate-aware multiset, and grouped sums. `data/mismatch.json` changes `A-001.amount` to `11.00`; `data/target_missing.json` omits `A-004`.

Each case declares `comparison.mode` (`keyed` or `multiset`), output column names/types in exact sequence, `key` when keyed, `ordered`, `timezone: UTC`, and decimal `scale`/`tolerance`. The currently reviewed decimal rule is scale 2, absolute tolerance 0.005. That tolerance is a comparison policy, **not** proof that SQLite stored exact decimal values. A source/target type discrepancy is normalized only under the declared type; conversion failure is FAIL. Multiset decimals require zero tolerance because fuzzy duplicate matching would be ambiguous.

Evidence report fields include case/run IDs, UTC timestamp, source/target/parser versions, rules and fixture versions, source and target SQL, hashes of case/fixtures/SQL/executed results, row counts, engine types, comparison policy, differences, decision, and limits. SHA-256 is an integrity digest, not a digital signature.
