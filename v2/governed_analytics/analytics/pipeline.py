"""Deterministic producer, contract-enforced Bronze load and SQL mart build."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = ("products", "orders", "order_lines", "returns")
MODEL_VERSION = "1.0.0"
log = logging.getLogger(__name__)


def _write(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def generate(directory: Path = DATA, order_count: int = 4000) -> dict:
    """Create invented fixtures with stable IDs and no personal information."""
    if order_count < 1 or order_count > 100_000:
        raise ValueError("order_count must be 1..100000")
    directory.mkdir(parents=True, exist_ok=True)
    products = [{"product_id": f"P{i:02}", "category": ("tools", "parts", "supplies")[i % 3]}
                for i in range(1, 13)]
    orders, lines, returns = [], [], []
    base = datetime(2026, 4, 1, tzinfo=timezone.utc)
    for n in range(1, order_count + 1):
        order_id = f"O{n:06}"
        placed = base + timedelta(hours=(n * 7) % 1440, minutes=53 if n % 17 == 0 else 0)
        currency = "USD" if n % 3 else "COP"
        status = "cancelled" if n % 11 == 0 else "completed"
        orders.append({"order_id": order_id, "placed_at": placed.isoformat(),
                       "status": status, "currency": currency})
        for k in range(1, n % 3 + 2):
            lid = f"L{n:06}-{k}"
            product = products[(n + k) % len(products)]["product_id"]
            quantity = k
            unit = (800 + (n % 41) * 17) if currency == "USD" else (250000 + (n % 41) * 5000)
            discount = unit // 10 if n % 5 == 0 else 0
            lines.append({"line_id": lid, "order_id": order_id, "product_id": product,
                          "quantity": quantity, "unit_minor": unit, "discount_minor": discount})
            if status == "completed" and n % 7 == 0 and k == 1:
                accepted = placed + timedelta(days=3)
                returns.append({"return_id": f"R{n:06}", "line_id": lid,
                                "accepted_at": accepted.isoformat(), "amount_minor": unit // 2,
                                "status": "accepted"})
            if status == "completed" and n % 19 == 0 and k == 1:
                returns.append({"return_id": f"RX{n:06}", "line_id": lid,
                                "accepted_at": (placed + timedelta(days=4)).isoformat(),
                                "amount_minor": unit // 3, "status": "rejected"})
    for name, rows in zip(SOURCES, (products, orders, lines, returns)):
        _write(directory / f"{name}.jsonl", rows)
    manifest = {"synthetic": True, "seed": "formula-v1", "source_counts": {
        "products": len(products), "orders": len(orders), "order_lines": len(lines), "returns": len(returns)},
        "sha256": {name: hashlib.sha256((directory / f"{name}.jsonl").read_bytes()).hexdigest()
                   for name in SOURCES}}
    (directory / "source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _utc(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc).replace(tzinfo=None).isoformat(sep=" ")


def _read(directory: Path, name: str) -> list[dict]:
    with (directory / f"{name}.jsonl").open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def build(directory: Path = DATA, database: Path | None = None) -> dict:
    """Build from persisted JSONL every time; atomic replacement prevents partial snapshots."""
    database = database or directory / "warehouse.duckdb"
    directory.mkdir(parents=True, exist_ok=True)
    tmp = database.with_name(database.name + ".building")
    tmp.unlink(missing_ok=True)
    counts = {name: 0 for name in SOURCES}
    rejected: list[dict] = []
    con = duckdb.connect(str(tmp))
    try:
        con.execute("CREATE TABLE raw_products (product_id VARCHAR PRIMARY KEY, category VARCHAR NOT NULL)")
        con.execute("CREATE TABLE raw_orders (order_id VARCHAR PRIMARY KEY, placed_at TIMESTAMP NOT NULL, status VARCHAR NOT NULL, currency VARCHAR NOT NULL)")
        con.execute("CREATE TABLE raw_order_lines (line_id VARCHAR PRIMARY KEY, order_id VARCHAR NOT NULL, product_id VARCHAR NOT NULL, quantity INTEGER NOT NULL, unit_minor BIGINT NOT NULL, discount_minor BIGINT NOT NULL)")
        con.execute("CREATE TABLE raw_returns (return_id VARCHAR PRIMARY KEY, line_id VARCHAR NOT NULL, accepted_at TIMESTAMP NOT NULL, amount_minor BIGINT NOT NULL, status VARCHAR NOT NULL)")
        con.execute("BEGIN TRANSACTION")
        products, orders, lines, returns = (_read(directory, name) for name in SOURCES)
        seen: dict[str, set[str]] = {name: set() for name in SOURCES}
        accepted_ids = {"products": set(), "orders": set(), "order_lines": set()}
        batches: dict[str, list[tuple]] = {name: [] for name in SOURCES}

        def reject(source: str, row: dict, reason: str) -> None:
            rejected.append({"source": source, "source_id": next(iter(row.values()), None), "reason": reason})

        for row in products:
            try:
                pid, category = row["product_id"], row["category"]
                if not isinstance(pid, str) or not pid or category not in ("tools", "parts", "supplies"):
                    raise ValueError("invalid product contract")
                if pid in seen["products"]:
                    raise ValueError("duplicate product_id")
                seen["products"].add(pid)
                batches["products"].append((pid, category))
                accepted_ids["products"].add(pid); counts["products"] += 1
            except (KeyError, TypeError, ValueError) as exc:
                reject("products", row, str(exc))
        for row in orders:
            try:
                oid, status, currency = row["order_id"], row["status"], row["currency"]
                if status not in ("completed", "cancelled") or currency not in ("USD", "COP"):
                    raise ValueError("invalid status/currency")
                if oid in seen["orders"]:
                    raise ValueError("duplicate order_id")
                stamp = _utc(row["placed_at"])
                seen["orders"].add(oid)
                batches["orders"].append((oid, stamp, status, currency))
                accepted_ids["orders"].add(oid); counts["orders"] += 1
            except (KeyError, TypeError, ValueError) as exc:
                reject("orders", row, str(exc))
        for row in lines:
            try:
                lid, oid, pid = row["line_id"], row["order_id"], row["product_id"]
                qty, unit, discount = row["quantity"], row["unit_minor"], row["discount_minor"]
                if lid in seen["order_lines"] or oid not in accepted_ids["orders"] or pid not in accepted_ids["products"]:
                    raise ValueError("duplicate line or missing dimension")
                if any(type(v) is not int for v in (qty, unit, discount)) or qty <= 0 or unit < 0 or discount < 0 or discount > qty * unit:
                    raise ValueError("invalid money/quantity")
                seen["order_lines"].add(lid)
                batches["order_lines"].append((lid, oid, pid, qty, unit, discount))
                accepted_ids["order_lines"].add(lid); counts["order_lines"] += 1
            except (KeyError, TypeError, ValueError) as exc:
                reject("order_lines", row, str(exc))
        order_status = {r["order_id"]: r["status"] for r in orders if r.get("order_id") in accepted_ids["orders"]}
        line_order = {r["line_id"]: r["order_id"] for r in lines if r.get("line_id") in accepted_ids["order_lines"]}
        line_values = {r["line_id"]: r["quantity"] * r["unit_minor"] - r["discount_minor"] for r in lines
                       if r.get("line_id") in accepted_ids["order_lines"]}
        returned_by_line: dict[str, int] = {}
        for row in returns:
            try:
                rid, lid, status = row["return_id"], row["line_id"], row["status"]
                amount = row["amount_minor"]
                if rid in seen["returns"] or lid not in accepted_ids["order_lines"]:
                    raise ValueError("duplicate return or missing line")
                if order_status[line_order[lid]] != "completed":
                    raise ValueError("return against cancelled order")
                if status not in ("accepted", "rejected") or type(amount) is not int or amount < 0:
                    raise ValueError("invalid return")
                stamp = _utc(row["accepted_at"])
                if status == "accepted":
                    new_total = returned_by_line.get(lid, 0) + amount
                    if new_total > line_values[lid]:
                        raise ValueError("accepted returns exceed discounted line")
                    returned_by_line[lid] = new_total
                seen["returns"].add(rid)
                batches["returns"].append((rid, lid, stamp, amount, status))
                counts["returns"] += 1
            except (KeyError, TypeError, ValueError) as exc:
                reject("returns", row, str(exc))
        # DuckDB is columnar: bulk COPY is materially faster than row inserts.
        for source in SOURCES:
            if not batches[source]: continue
            staging = directory / f".{source}.staging.csv"
            with staging.open("w", newline="", encoding="utf-8") as stream:
                csv.writer(stream).writerows(batches[source])
            safe_path = str(staging).replace("'", "''")
            con.execute(f"COPY raw_{source} FROM '{safe_path}' (FORMAT CSV, HEADER FALSE)")
            staging.unlink()
        model_bytes = (ROOT / "models" / "build.sql").read_bytes()
        model = model_bytes.decode("utf-8")
        con.execute(model)
        source_hash = hashlib.sha256("".join(hashlib.sha256((directory / f"{n}.jsonl").read_bytes()).hexdigest() for n in SOURCES).encode()).hexdigest()
        model_hash = hashlib.sha256(model_bytes).hexdigest()
        loader_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        run_id = hashlib.sha256((source_hash + model_hash + loader_hash + duckdb.__version__ + MODEL_VERSION + json.dumps(rejected, sort_keys=True)).encode()).hexdigest()[:16]
        con.execute("CREATE TABLE run_manifest AS SELECT ?::VARCHAR AS run_id, ?::VARCHAR AS model_version, ?::VARCHAR AS model_sha256, ?::VARCHAR AS source_sha256, ?::INTEGER AS source_count, ?::INTEGER AS rejected_count, strftime(current_timestamp, '%Y-%m-%dT%H:%M:%SZ') AS processed_at",
                    [run_id, MODEL_VERSION, model_hash, source_hash, sum(counts.values()), len(rejected)])
        mart_count = con.execute("SELECT count(*) FROM fct_order_lines").fetchone()[0]
        con.execute("COMMIT")
        # Publish an immutable Parquet generation before changing the DB pointer.
        # An interrupted build leaves only an unreferenced generation, not mixed versions.
        parquet_root = directory / "parquet"
        parquet_root.mkdir(exist_ok=True)
        parquet = parquet_root / run_id
        expected_tables = ("fct_order_lines", "fct_returns", "fct_orders", "dim_product")
        if parquet.exists():
            for table in expected_tables:
                artifact = parquet / f"{table}.parquet"
                if not artifact.is_file():
                    raise ValueError(f"Incomplete Parquet generation: {artifact}")
                safe_path = str(artifact).replace("'", "''")
                actual = con.execute(f"SELECT count(*) FROM read_parquet('{safe_path}')").fetchone()[0]
                expected = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                if actual != expected:
                    raise ValueError(f"Parquet generation row count mismatch: {table}")
        else:
            staging = Path(tempfile.mkdtemp(prefix=f".{run_id}-", dir=parquet_root))
            for table in expected_tables:
                target = str(staging / f"{table}.parquet").replace("'", "''")
                con.execute(f"COPY {table} TO '{target}' (FORMAT PARQUET)")
            staging.rename(parquet)
    finally:
        con.close()
    tmp.replace(database)
    (directory / "rejections.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rejected), encoding="utf-8")
    result = {"run_id": run_id,
              "accepted": counts, "rejected": len(rejected), "mart_lines": mart_count,
              "database": str(database), "parquet_generation": str(parquet), "model_version": MODEL_VERSION}
    (directory / "build_manifest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    log.info(json.dumps({"stage": "build", **result}))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("seed", "build", "all"))
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--orders", type=int, default=4000)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.action in ("seed", "all"):
        print(json.dumps(generate(args.data, args.orders)))
    if args.action in ("build", "all"):
        print(json.dumps(build(args.data)))


if __name__ == "__main__":
    main()
