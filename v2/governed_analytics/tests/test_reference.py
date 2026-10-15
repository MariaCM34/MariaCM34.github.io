"""Independent source-level oracle and adversarial API/data contract checks."""
import json
import hashlib
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone

import duckdb
import pytest
from fastapi.testclient import TestClient

from analytics.api import create_app
from analytics.pipeline import build, generate
from analytics.semantic import CATALOG, VERSION


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def append(path, row):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row) + "\n")


@pytest.fixture
def built(tmp_path):
    generate(tmp_path, 120)
    manifest = build(tmp_path)
    return tmp_path, manifest, TestClient(create_app(tmp_path / "warehouse.duckdb", tmp_path / "audit.sqlite"))


def oracle(path, currency, start="2026-04-01", end="2026-06-01"):
    """Pure source-file arithmetic; no SQL, mart, or semantic compiler calls."""
    orders = {o["order_id"]: o for o in rows(path / "orders.jsonl")}
    lines = {l["line_id"]: l for l in rows(path / "order_lines.jsonl")}
    products = {p["product_id"]: p["category"] for p in rows(path / "products.jsonl")}
    out = defaultdict(lambda: {"net": 0, "gross": 0, "sales_rows": 0, "returns": 0})
    for line in lines.values():
        order = orders[line["order_id"]]
        period = datetime.fromisoformat(order["placed_at"]).astimezone(timezone.utc).strftime("%Y-%m")
        day = datetime.fromisoformat(order["placed_at"]).astimezone(timezone.utc).date().isoformat()
        if order["currency"] != currency or order["status"] != "completed" or not start <= day < end:
            continue
        rec = out[(period, products[line["product_id"]])]
        rec["gross"] += line["quantity"] * line["unit_minor"]
        rec["net"] += line["quantity"] * line["unit_minor"] - line["discount_minor"]
        rec["sales_rows"] += 1
    for refund in rows(path / "returns.jsonl"):
        if refund["status"] != "accepted":
            continue
        line = lines[refund["line_id"]]
        order = orders[line["order_id"]]
        day = datetime.fromisoformat(refund["accepted_at"]).astimezone(timezone.utc).date().isoformat()
        if order["currency"] != currency or not start <= day < end:
            continue
        key = (day[:7], products[line["product_id"]])
        out[key]["net"] -= refund["amount_minor"]
        out[key]["returns"] += 1
    return out


def ask(client, metric="net_sales", currency="USD", **kwargs):
    return client.post("/api/query", json={"metric": metric, "currency": currency,
                                           "start": "2026-04-01", "end": "2026-06-01", **kwargs})


def test_semantic_catalog_snapshot_requires_intentional_review():
    digest = hashlib.sha256(json.dumps({"version": VERSION, "metrics": CATALOG}, sort_keys=True).encode()).hexdigest()
    assert digest == "e6c302fee0d1d89df4319192d8063bda3a0ab5d6634f08d257b1dfafd8a1fa92"


def test_source_volume_and_idempotent_rebuild(tmp_path):
    source = generate(tmp_path, 4000)
    assert sum(source["source_counts"].values()) >= 10_000
    first = build(tmp_path)
    second = build(tmp_path)
    assert first["accepted"] == second["accepted"]
    assert first["run_id"] == second["run_id"]
    parquet = tmp_path / "parquet" / first["run_id"] / "fct_order_lines.parquet"
    assert parquet.exists()
    with duckdb.connect(str(tmp_path / "warehouse.duckdb"), read_only=True) as con:
        assert con.execute("SELECT count(*) FROM read_parquet(?)", [str(parquet)]).fetchone()[0] == first["mart_lines"]
        assert con.execute("SELECT run_id FROM run_manifest").fetchone()[0] == first["run_id"]


def test_interrupted_publish_keeps_previous_database_parquet_pair(tmp_path, monkeypatch):
    generate(tmp_path, 10)
    old = build(tmp_path)
    old_parquet = tmp_path / "parquet" / old["run_id"] / "fct_order_lines.parquet"
    append(tmp_path / "orders.jsonl", {"order_id": "NEW", "placed_at": "2026-05-01T00:00:00Z",
                                      "status": "completed", "currency": "USD"})
    append(tmp_path / "order_lines.jsonl", {"line_id": "NEW-L", "order_id": "NEW", "product_id": "P01",
                                           "quantity": 1, "unit_minor": 100, "discount_minor": 0})
    real_replace = type(tmp_path).replace

    def fail_before_swap(self, target):
        if self.name == "warehouse.duckdb.building":
            raise OSError("injected publication interruption")
        return real_replace(self, target)

    monkeypatch.setattr(type(tmp_path), "replace", fail_before_swap)
    with pytest.raises(OSError, match="injected"):
        build(tmp_path)
    with duckdb.connect(str(tmp_path / "warehouse.duckdb"), read_only=True) as con:
        assert con.execute("SELECT run_id FROM run_manifest").fetchone()[0] == old["run_id"]
        assert con.execute("SELECT count(*) FROM fct_order_lines").fetchone()[0] == old["mart_lines"]
    assert old_parquet.exists()


def test_net_sales_independent_oracle_and_exact_sql(built):
    path, _, client = built
    for currency in ("USD", "COP"):
        response = ask(client, currency=currency)
        assert response.status_code == 200, response.text
        actual = response.json()
        expected = oracle(path, currency)
        for row in actual["rows"]:
            month = row["period"]
            match = [value for (period, _), value in expected.items() if period == month]
            assert row["value"] == sum(v["net"] for v in match)
            assert row["sales_rows"] == sum(v["sales_rows"] for v in match)
            assert row["return_rows"] == sum(v["returns"] for v in match)
        with duckdb.connect(str(path / "warehouse.duckdb"), read_only=True) as con:
            assert con.execute(actual["sql_executed"], actual["parameters"]).fetchall() == [tuple(row.values()) for row in actual["rows"]]
    assert client.get("/api/audit/" + actual["query_id"]).json()["status"] == "EXECUTED"


def test_category_and_gross_reconcile(built):
    path, _, client = built
    expected = oracle(path, "USD")
    category = ask(client, "net_sales_by_category").json()
    assert category["rows"]
    for row in category["rows"]:
        assert row["value"] == expected[(row["period"], row["category"])]["net"]
    gross = ask(client, "gross_sales").json()
    assert sum(r["value"] for r in gross["rows"]) == sum(v["gross"] for v in expected.values())


def test_order_grain_cancellation_denominator(built):
    path, _, client = built
    source = [o for o in rows(path / "orders.jsonl") if o["currency"] == "USD"]
    result = ask(client, "cancellation_rate").json()["rows"]
    assert sum(r["eligible_orders"] for r in result) == len(source)
    assert sum(r["cancelled_orders"] for r in result) == len([o for o in source if o["status"] == "cancelled"])
    assert len(rows(path / "order_lines.jsonl")) > len(rows(path / "orders.jsonl"))


def test_duplicate_invalid_missing_dimension_and_utc_boundary(tmp_path):
    generate(tmp_path, 11)
    original = rows(tmp_path / "orders.jsonl")[0]
    append(tmp_path / "orders.jsonl", original)  # duplicate event
    append(tmp_path / "order_lines.jsonl", {"line_id": "INVALID", "order_id": original["order_id"],
           "product_id": "UNKNOWN", "quantity": 1, "unit_minor": 100, "discount_minor": 0})
    append(tmp_path / "order_lines.jsonl", {"line_id": "NEGATIVE", "order_id": original["order_id"],
           "product_id": "P01", "quantity": 1, "unit_minor": -100, "discount_minor": 0})
    append(tmp_path / "orders.jsonl", {"order_id": "TZ", "placed_at": "2026-04-01T00:30:00+02:00",
                                      "status": "completed", "currency": "USD"})
    append(tmp_path / "order_lines.jsonl", {"line_id": "TZ-1", "order_id": "TZ", "product_id": "P01",
                                           "quantity": 1, "unit_minor": 100, "discount_minor": 0})
    manifest = build(tmp_path)
    assert manifest["rejected"] == 3
    with duckdb.connect(str(tmp_path / "warehouse.duckdb"), read_only=True) as con:
        assert con.execute("SELECT event_at FROM fct_order_lines WHERE line_id = 'TZ-1'").fetchone()[0].isoformat() == "2026-03-31T22:30:00"


def test_partial_return_is_once_and_recognized_acceptance_month(tmp_path):
    generate(tmp_path, 1)
    order = rows(tmp_path / "orders.jsonl")[0]
    line = rows(tmp_path / "order_lines.jsonl")[0]
    append(tmp_path / "returns.jsonl", {"return_id": "PART1", "line_id": line["line_id"],
                                          "accepted_at": "2026-05-01T00:00:00Z", "amount_minor": 100,
                                          "status": "accepted"})
    append(tmp_path / "returns.jsonl", {"return_id": "PART2", "line_id": line["line_id"],
                                          "accepted_at": "2026-05-02T00:00:00Z", "amount_minor": 100,
                                          "status": "accepted"})
    build(tmp_path)
    client = TestClient(create_app(tmp_path / "warehouse.duckdb", tmp_path / "audit.sqlite"))
    values = {r["period"]: r for r in ask(client).json()["rows"]}
    assert values["2026-05"]["value"] == -200
    assert values["2026-05"]["return_rows"] == 2
    assert values["2026-04"]["value"] == sum(
        item["quantity"] * item["unit_minor"] - item["discount_minor"]
        for item in rows(tmp_path / "order_lines.jsonl"))


def test_excess_return_rejection_does_not_poison_later_valid_return(tmp_path):
    generate(tmp_path, 1)
    line = rows(tmp_path / "order_lines.jsonl")[0]
    for rid, amount in (("TOO_BIG", 100000), ("VALID_AFTER", 100)):
        append(tmp_path / "returns.jsonl", {"return_id": rid, "line_id": line["line_id"],
                                              "accepted_at": "2026-05-01T00:00:00Z",
                                              "amount_minor": amount, "status": "accepted"})
    result = build(tmp_path)
    assert result["rejected"] == 1
    with duckdb.connect(str(tmp_path / "warehouse.duckdb"), read_only=True) as con:
        assert con.execute("SELECT return_id FROM fct_returns").fetchall() == [("VALID_AFTER",)]


@pytest.mark.parametrize("payload", [
    {"metric": "drop_table", "start": "2026-04-01", "end": "2026-06-01", "currency": "USD"},
    {"metric": "net_sales", "start": "2026-04-01", "end": "2026-06-01", "currency": "USD'; DROP TABLE raw_orders;--"},
    {"metric": "net_sales", "start": "2026-04-01", "end": "2026-06-01", "currency": "USD", "sql": "DROP TABLE raw_orders"},
])
def test_refusals_audited_without_sql(built, payload):
    path, _, client = built
    response = client.post("/api/query", json=payload)
    assert response.status_code == 422
    assert "rows" not in response.json()
    query_id = response.json()["detail"]["query_id"]
    assert client.get("/api/audit/" + query_id).json()["status"] == "REFUSED"
    with duckdb.connect(str(path / "warehouse.duckdb"), read_only=True) as con:
        assert con.execute("SELECT count(*) FROM raw_orders").fetchone()[0] == 120


def test_audit_file_handles_are_closed_after_write_and_read(built):
    path, _, client = built
    response = ask(client)
    assert response.status_code == 200
    assert client.get("/api/audit/" + response.json()["query_id"]).status_code == 200
    # On Windows this fails if either sqlite3 connection is still open.
    audit = path / "audit.sqlite"
    audit.unlink()
    assert not audit.exists()
