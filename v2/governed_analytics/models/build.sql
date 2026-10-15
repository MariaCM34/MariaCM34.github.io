-- Version 1.0.0. Sales grain is one order line; returns remain separate facts.
CREATE TABLE dim_product AS SELECT product_id, category FROM raw_products;
CREATE TABLE fct_order_lines AS
 SELECT l.line_id, l.order_id, l.product_id, p.category, o.placed_at AS event_at,
        o.currency, o.status, l.quantity * l.unit_minor AS gross_minor,
        l.quantity * l.unit_minor - l.discount_minor AS sales_minor
 FROM raw_order_lines l
 JOIN raw_orders o USING (order_id)
 JOIN dim_product p USING (product_id);
CREATE TABLE fct_returns AS
 SELECT r.return_id, r.line_id, l.order_id, l.product_id, l.category,
        r.accepted_at AS event_at, l.currency, r.amount_minor, r.status
 FROM raw_returns r JOIN fct_order_lines l USING (line_id);
CREATE TABLE fct_orders AS SELECT order_id, placed_at AS event_at, currency, status FROM raw_orders;
