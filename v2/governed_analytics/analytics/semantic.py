"""Versioned, finite semantic catalog. User text is never interpolated into SQL."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

VERSION = "1.0.0"
CATALOG = {
    "net_sales": {"label": "Net sales", "grain": "UTC month and currency", "unit": "minor currency units", "formula": "completed line value after discount, less accepted returns in acceptance month"},
    "gross_sales": {"label": "Gross sales", "grain": "UTC month and currency", "unit": "minor currency units", "formula": "completed line quantity × unit price before discount"},
    "cancellation_rate": {"label": "Cancellation rate", "grain": "UTC month and currency", "unit": "percent", "formula": "distinct cancelled eligible orders / distinct eligible placed orders × 100"},
    "net_sales_by_category": {"label": "Net sales by category", "grain": "UTC month, currency, product category", "unit": "minor currency units", "formula": "completed category line value after discount, less accepted category returns in acceptance month"},
}


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metric: Literal["net_sales", "gross_sales", "cancellation_rate", "net_sales_by_category"]
    start: date
    end: date
    currency: Literal["USD", "COP"]
    category: Literal["tools", "parts", "supplies"] | None = None

    @model_validator(mode="after")
    def bounds(self):
        if self.end <= self.start or (self.end - self.start).days > 366:
            raise ValueError("date range must be non-empty and at most 366 days")
        if self.metric == "cancellation_rate" and self.category is not None:
            raise ValueError("category does not apply to order-grain cancellation rate")
        return self


def compile_query(req: QueryRequest) -> tuple[str, list]:
    """Return reviewed SQL and bound parameters; no arbitrary identifier path."""
    start, end = req.start.isoformat(), req.end.isoformat()
    if req.metric == "cancellation_rate":
        sql = """SELECT strftime(event_at, '%Y-%m') AS period, currency,
 count(DISTINCT order_id) AS eligible_orders,
 count(DISTINCT CASE WHEN status = 'cancelled' THEN order_id END) AS cancelled_orders,
 round(100.0 * count(DISTINCT CASE WHEN status = 'cancelled' THEN order_id END)
       / nullif(count(DISTINCT order_id), 0), 4) AS value
FROM fct_orders WHERE event_at >= ? AND event_at < ? AND currency = ?
GROUP BY 1, 2 ORDER BY 1, 2 LIMIT 500"""
        return sql, [start, end, req.currency]
    if req.metric == "gross_sales":
        sql = """SELECT strftime(event_at, '%Y-%m') AS period, currency,
 sum(gross_minor) AS value, count(*) AS source_rows
FROM fct_order_lines WHERE status = 'completed' AND event_at >= ? AND event_at < ? AND currency = ?
GROUP BY 1, 2 ORDER BY 1, 2 LIMIT 500"""
        return sql, [start, end, req.currency]
    category_sale = " AND category = ?" if req.category else ""
    category_return = " AND category = ?" if req.category else ""
    grouping = ", category" if req.metric == "net_sales_by_category" else ""
    joining = " AND sales.category = returns.category" if grouping else ""
    sales = f"""SELECT strftime(event_at, '%Y-%m') AS period, currency{grouping},
 sum(sales_minor) AS amount, count(*) AS row_count
FROM fct_order_lines WHERE status = 'completed' AND event_at >= ? AND event_at < ? AND currency = ?{category_sale}
GROUP BY 1, 2{', 3' if grouping else ''}"""
    refunds = f"""SELECT strftime(event_at, '%Y-%m') AS period, currency{grouping},
 sum(amount_minor) AS amount, count(*) AS row_count
FROM fct_returns WHERE status = 'accepted' AND event_at >= ? AND event_at < ? AND currency = ?{category_return}
GROUP BY 1, 2{', 3' if grouping else ''}"""
    # UNION supports months with refunds but no new sales. Separate facts prevent multiplication.
    sql = f"""WITH sales AS ({sales}), returns AS ({refunds}),
 keys AS (SELECT period, currency{grouping} FROM sales UNION SELECT period, currency{grouping} FROM returns)
SELECT keys.period, keys.currency{', keys.category' if grouping else ''},
 coalesce(sales.amount, 0) - coalesce(returns.amount, 0) AS value,
 coalesce(sales.row_count, 0) AS sales_rows, coalesce(returns.row_count, 0) AS return_rows
FROM keys LEFT JOIN sales ON keys.period = sales.period AND keys.currency = sales.currency{ ' AND keys.category = sales.category' if grouping else ''}
LEFT JOIN returns ON keys.period = returns.period AND keys.currency = returns.currency{ ' AND keys.category = returns.category' if grouping else ''}
ORDER BY 1, 2{', 3' if grouping else ''} LIMIT 500"""
    params = [start, end, req.currency]
    if req.category: params.append(req.category)
    params += [start, end, req.currency]
    if req.category: params.append(req.category)
    return sql, params
