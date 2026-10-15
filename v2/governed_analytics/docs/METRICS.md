# Semantic catalog v1.0.0

The sole executable catalog is `analytics/semantic.py`; the UI fetches it from `/api/catalog`, and the query API compiles SQL from it. A definition change requires version bump and changed golden/oracle assertions. The test suite checks independent source-level sums and exact SQL replay.

| Metric | Grain / formula | Counterexample guarded |
|---|---|---|
| `gross_sales` | UTC month × currency; sum `quantity × unit_minor` from completed lines | Cancelled orders contribute zero; discounts do not reduce gross. |
| `net_sales` | UTC month × currency; sum completed `quantity × unit_minor − discount_minor`, minus accepted return minor units whose **acceptance** date is in that month | Return on May 1 for an April sale reduces May, even if May has no sales. Rejected returns do not count. |
| `net_sales_by_category` | UTC month × currency × stable product category; same separate-fact formula as net sales | A line with two partial returns is not multiplied by joining both returns before aggregation. |
| `cancellation_rate` | UTC placement month × currency; `100 × distinct cancelled eligible placed orders / distinct eligible placed orders`, rounded to 4 decimals | A three-line cancelled order counts once in numerator and denominator. Category filter is refused at order grain. |

The `start` date is inclusive and `end` exclusive. They must differ by no more than 366 days; the result is capped at 500 grouped rows. No cross-currency total is returned or implied. Minor units must be interpreted with the relevant currency; COP and USD are separate series. Neither revenue nor cancellation rate incorporates shipping, tax, FX, or customer PII.

Adversarial question: *what could look correct but be wrong?* Joining line sales directly to two return records would double the line's revenue, potentially producing a plausible chart. Tests inject two partial returns on the same line, reconcile from raw JSONL without model SQL, and verify the return-only acceptance month.
