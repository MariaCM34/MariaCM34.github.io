"""Reviewed synthetic migration cases. Every PASS case is executed on both engines."""

from __future__ import annotations

from copy import deepcopy

TEXT = {"type": "text"}
INTEGER = {"type": "integer"}
DECIMAL = {"type": "decimal", "scale": 2, "tolerance": "0.005"}
DATE = {"type": "date"}


def case(case_id: str, sql: str, columns: dict, *, mode: str = "keyed", key: str | None = None,
         ordered: bool = False, target: str = "base.json", expected: str = "PASS") -> dict:
    return {"case_id": case_id, "source_sql": sql, "source_fixture": "../fixtures/base.json",
            "target_fixture": f"../fixtures/{target}", "expected_status": expected,
            "comparison": {"mode": mode, "key": key, "columns": deepcopy(columns),
                           "ordered": ordered, "timezone": "UTC"}}


CASES = [
    case("01-keyed-projection", "SELECT order_id, amount FROM orders ORDER BY order_id", {"order_id": TEXT, "amount": DECIMAL}, key="order_id", ordered=True),
    case("02-filter-status", "SELECT order_id, status FROM orders WHERE status = 'paid' ORDER BY order_id", {"order_id": TEXT, "status": TEXT}, key="order_id", ordered=True),
    case("03-filter-null", "SELECT order_id, amount FROM orders WHERE amount IS NULL ORDER BY order_id", {"order_id": TEXT, "amount": DECIMAL}, key="order_id", ordered=True),
    case("04-group-count", "SELECT status, COUNT(*) AS orders_count FROM orders GROUP BY status ORDER BY status", {"status": TEXT, "orders_count": INTEGER}, key="status", ordered=True),
    case("05-group-sum", "SELECT region, SUM(amount) AS total_amount FROM orders GROUP BY region ORDER BY region", {"region": TEXT, "total_amount": DECIMAL}, key="region", ordered=True),
    case("06-coalesce", "SELECT order_id, COALESCE(amount, 0) AS safe_amount FROM orders ORDER BY order_id", {"order_id": TEXT, "safe_amount": DECIMAL}, key="order_id", ordered=True),
    case("07-having", "SELECT region, COUNT(*) AS orders_count FROM orders GROUP BY region HAVING COUNT(*) > 1 ORDER BY region", {"region": TEXT, "orders_count": INTEGER}, key="region", ordered=True),
    case("08-range", "SELECT order_id, ordered_on FROM orders WHERE ordered_on >= '2026-01-02' AND ordered_on <= '2026-01-04' ORDER BY order_id", {"order_id": TEXT, "ordered_on": DATE}, key="order_id", ordered=True),
    case("09-arithmetic", "SELECT order_id, quantity * 2 AS doubled_quantity FROM orders ORDER BY order_id", {"order_id": TEXT, "doubled_quantity": INTEGER}, key="order_id", ordered=True),
    case("10-ordered-limit", "SELECT order_id, status FROM orders ORDER BY order_id LIMIT 3", {"order_id": TEXT, "status": TEXT}, key="order_id", ordered=True),
    case("11-duplicate-aware-multiset", "SELECT status FROM orders", {"status": TEXT}, mode="multiset"),
    case("12-intentional-mismatch", "SELECT order_id, amount FROM orders ORDER BY order_id", {"order_id": TEXT, "amount": DECIMAL}, key="order_id", ordered=True, target="mismatch.json", expected="FAIL"),
    case("13-missing-key", "SELECT order_id, amount FROM orders ORDER BY order_id", {"order_id": TEXT, "amount": DECIMAL}, key="order_id", ordered=True, target="target_missing.json", expected="FAIL"),
    case("14-review-mutation", "DELETE FROM orders", {"order_id": TEXT}, key="order_id", expected="REVIEW"),
    case("15-review-unordered-limit", "SELECT order_id FROM orders LIMIT 2", {"order_id": TEXT}, key="order_id", expected="REVIEW"),
    case("16-review-unapproved-table", "SELECT order_id FROM users", {"order_id": TEXT}, key="order_id", expected="REVIEW"),
    case("17-review-unsafe-function", "SELECT load_extension('x') FROM orders", {"value": TEXT}, mode="multiset", expected="REVIEW"),
]
