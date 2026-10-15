"""Parse, execute on two independent engines, and compare bounded result sets."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from pathlib import Path
import sqlite3
import subprocess
import tempfile
from typing import Any
import uuid

import duckdb
import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel, ParseError, UnsupportedError

from . import FIXTURE_VERSION, RULES_VERSION

MAX_ROWS = 1000
MAX_FIXTURE_ROWS = 1000
MAX_SQL_CHARS = 8000

# A deliberately small, auditable SQL subset. New nodes require review and tests.
ALLOWED_NODES = (
    exp.Select, exp.From, exp.Where, exp.Group, exp.Having, exp.Order, exp.Ordered,
    exp.Limit, exp.Column, exp.Identifier, exp.Table, exp.Star, exp.Literal,
    exp.Alias, exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE,
    exp.And, exp.Or, exp.Not, exp.Is, exp.Null, exp.Paren, exp.Add, exp.Sub,
    exp.Mul, exp.Div, exp.Sum, exp.Count, exp.Min, exp.Max, exp.Avg,
    exp.Coalesce, exp.Case, exp.If, exp.In, exp.Between, exp.Cast,
    exp.DataType, exp.Boolean, exp.Neg, exp.Distinct,
)


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return sha256(raw).hexdigest()


def _source_provenance() -> dict[str, Any]:
    package = Path(__file__).resolve().parents[2]
    hashes = {p.relative_to(package).as_posix(): sha256(p.read_bytes()).hexdigest()
              for p in sorted((package / "src").rglob("*.py"))}
    root = package.parents[1]
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True, timeout=3).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "--", "v2/migration_assurance"], cwd=root, text=True, capture_output=True, check=True, timeout=3).stdout.strip())
    except (OSError, subprocess.SubprocessError):
        head, dirty = None, None
    return {"git_head": head, "package_dirty": dirty, "source_code_hashes": hashes}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_ast(sql: str, *, require_order: bool = False) -> tuple[str, list[str]]:
    if not sql or len(sql) > MAX_SQL_CHARS or "\x00" in sql:
        raise ValueError("SQL must be nonempty, at most 8000 characters, without NUL")
    try:
        statements = sqlglot.parse(sql, read="sqlite", error_level=ErrorLevel.RAISE)
    except ParseError as exc:
        raise ValueError(f"SQLite parse error: {exc}") from exc
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise ValueError("Exactly one top-level SELECT is supported; DDL/DML and multiple statements require review")
    tree = statements[0]
    if tree.find(exp.With) or tree.find(exp.Subquery) or tree.find(exp.Join):
        raise ValueError("CTEs, subqueries, and joins require review in subset v1")
    if tree.args.get("limit") and not tree.args.get("order"):
        raise ValueError("LIMIT without ORDER BY is nondeterministic and requires review")
    if require_order and not tree.args.get("order"):
        raise ValueError("Ordered comparison requires an AST ORDER BY clause")
    for node in tree.walk():
        if not isinstance(node, ALLOWED_NODES):
            raise ValueError(f"Unsupported SQL construct {type(node).__name__} at {node.sql(dialect='sqlite')[:100]}")
    tables = [t.name for t in tree.find_all(exp.Table)]
    if tables != ["orders"]:
        raise ValueError(f"Only the declared orders table is supported; referenced: {tables}")
    columns = {c.name for c in tree.find_all(exp.Column)}
    unknown = columns - {"order_id", "amount", "status", "region", "quantity", "ordered_on"}
    if unknown:
        raise ValueError(f"Unknown columns: {sorted(unknown)}")
    # SQLGlot rewrites are syntactic. We preserve the input and explain its boundary.
    try:
        target_sql = tree.sql(dialect="duckdb", unsupported_level=ErrorLevel.RAISE)
    except UnsupportedError as exc:
        raise ValueError(f"Unsupported DuckDB translation: {exc}") from exc
    return target_sql, ["sqlglot:sqlite-to-duckdb-ast", "subset-v1-no-semantic-equivalence-guarantee"]


def _validate_spec(spec: dict[str, Any]) -> None:
    required = {"case_id", "source_sql", "source_fixture", "target_fixture", "comparison"}
    if missing := required - spec.keys():
        raise ValueError(f"Missing case fields: {sorted(missing)}")
    cmp = spec["comparison"]
    if cmp.get("mode") not in {"keyed", "multiset"}:
        raise ValueError("comparison.mode must be keyed or multiset")
    if cmp["mode"] == "keyed" and not cmp.get("key"):
        raise ValueError("keyed comparison requires key")
    if not isinstance(cmp.get("columns"), dict) or not cmp["columns"]:
        raise ValueError("comparison.columns must declare every output column and type")
    for name, rule in cmp["columns"].items():
        if rule.get("type") not in {"text", "integer", "decimal", "date"}:
            raise ValueError(f"Unsupported comparison type for {name}")
        if rule["type"] == "decimal":
            if "scale" not in rule or "tolerance" not in rule:
                raise ValueError(f"Decimal {name} requires explicit scale and tolerance")
            if not 0 <= int(rule["scale"]) <= 9 or Decimal(str(rule["tolerance"])) < 0:
                raise ValueError(f"Invalid decimal comparison rule for {name}")
            if cmp["mode"] == "multiset" and Decimal(str(rule["tolerance"])) != 0:
                raise ValueError("Multiset decimal comparison requires zero tolerance; fuzzy duplicate matching is ambiguous")
    if cmp.get("timezone") != "UTC":
        raise ValueError("comparison.timezone must explicitly be UTC (no timestamp conversion in subset v1)")
    if cmp.get("ordered") not in {True, False}:
        raise ValueError("comparison.ordered must be explicit")


def _validate_fixture(rows: list[dict[str, Any]]) -> None:
    if not isinstance(rows, list) or len(rows) > MAX_FIXTURE_ROWS:
        raise ValueError("Fixture must be a list of at most 1000 records")
    cols = {"order_id", "amount", "status", "region", "quantity", "ordered_on"}
    ids = set()
    for index, row in enumerate(rows):
        if set(row) != cols:
            raise ValueError(f"Fixture row {index}: expected columns {sorted(cols)}")
        if not isinstance(row["order_id"], str) or row["order_id"] in ids:
            raise ValueError(f"Fixture row {index}: nonunique or invalid order_id")
        ids.add(row["order_id"])
        if row["amount"] is not None:
            try:
                value = Decimal(str(row["amount"]))
            except InvalidOperation as exc:
                raise ValueError(f"Fixture row {index}: invalid amount") from exc
            if not value.is_finite() or value.as_tuple().exponent < -2:
                raise ValueError(f"Fixture row {index}: amount must have at most 2 decimal places")
        if not isinstance(row["quantity"], int) or isinstance(row["quantity"], bool):
            raise ValueError(f"Fixture row {index}: invalid quantity")
        for field in ("status", "region", "ordered_on"):
            if not isinstance(row[field], str):
                raise ValueError(f"Fixture row {index}: invalid {field}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["ordered_on"]):
            raise ValueError(f"Fixture row {index}: ordered_on must be ISO date")
        try:
            datetime.strptime(row["ordered_on"], "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"Fixture row {index}: invalid ordered_on date") from exc


def _load_sqlite(path: Path, rows: list[dict[str, Any]]) -> None:
    db = sqlite3.connect(path)
    try:
        db.execute("CREATE TABLE orders(order_id TEXT PRIMARY KEY, amount DECIMAL(12,2), status TEXT, region TEXT, quantity INTEGER, ordered_on TEXT)")
        db.executemany("INSERT INTO orders VALUES(?,?,?,?,?,?)", [tuple(r[k] for k in ("order_id", "amount", "status", "region", "quantity", "ordered_on")) for r in rows])
        db.commit()
    finally:
        db.close()


def _load_duckdb(path: Path, rows: list[dict[str, Any]]) -> None:
    db = duckdb.connect(str(path))
    try:
        db.execute("CREATE TABLE orders(order_id VARCHAR PRIMARY KEY, amount DECIMAL(12,2), status VARCHAR, region VARCHAR, quantity INTEGER, ordered_on VARCHAR)")
        db.executemany("INSERT INTO orders VALUES(?,?,?,?,?,?)", [tuple(r[k] for k in ("order_id", "amount", "status", "region", "quantity", "ordered_on")) for r in rows])
    finally:
        db.close()


def _execute_sqlite(path: Path, sql: str) -> tuple[list[str], list[list[Any]], list[str]]:
    db = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        db.set_progress_handler(lambda: 1, 100_000)  # bounded fixture/AST subset; interrupt unusually long queries
        cursor = db.execute(sql)
        names = [d[0] for d in cursor.description]
        rows = [list(r) for r in cursor.fetchmany(MAX_ROWS + 1)]
        if len(rows) > MAX_ROWS:
            raise ValueError("Source result exceeds 1000-row cap")
        types = [type(row[i]).__name__ for i in range(len(names)) for row in rows[:1]]
        return names, rows, types
    finally:
        db.close()


def _execute_duckdb(path: Path, sql: str) -> tuple[list[str], list[list[Any]], list[str]]:
    db = duckdb.connect(str(path), read_only=True)
    try:
        cursor = db.execute(sql)
        names = [d[0] for d in cursor.description]
        rows = [list(r) for r in cursor.fetchmany(MAX_ROWS + 1)]
        if len(rows) > MAX_ROWS:
            raise ValueError("Target result exceeds 1000-row cap")
        types = [str(d[1]) for d in cursor.description]
        return names, rows, types
    finally:
        db.close()


def _canonical(value: Any, rule: dict[str, Any]) -> Any:
    if value is None:
        return None
    kind = rule["type"]
    if kind == "text" or kind == "date":
        if not isinstance(value, str):
            raise ValueError(f"Expected {kind}, got {type(value).__name__}")
        if kind == "date":
            datetime.strptime(value, "%Y-%m-%d")
        return value
    if kind == "integer":
        if isinstance(value, bool) or Decimal(str(value)) != int(Decimal(str(value))):
            raise ValueError(f"Expected integer, got {value}")
        return int(value)
    if kind == "decimal":
        numeric = Decimal(str(value))
        if not numeric.is_finite():
            raise ValueError("Nonfinite decimal")
        return numeric.quantize(Decimal(1).scaleb(-int(rule["scale"])))
    raise ValueError(f"Unknown type {kind}")


def _compare(names_a: list[str], rows_a: list[list[Any]], names_b: list[str], rows_b: list[list[Any]], cmp: dict[str, Any]) -> dict[str, Any]:
    diffs: list[dict[str, Any]] = []
    expected_names = list(cmp["columns"])
    if names_a != expected_names or names_b != expected_names:
        return {"status": "FAIL", "differences": [{"kind": "schema", "expected": expected_names, "source": names_a, "target": names_b}]}
    rules = cmp["columns"]
    try:
        a = [{n: _canonical(v, rules[n]) for n, v in zip(names_a, row)} for row in rows_a]
        b = [{n: _canonical(v, rules[n]) for n, v in zip(names_b, row)} for row in rows_b]
    except (ValueError, InvalidOperation) as exc:
        return {"status": "FAIL", "differences": [{"kind": "type", "detail": str(exc)}]}
    if len(a) != len(b):
        diffs.append({"kind": "row_count", "source": len(a), "target": len(b)})
    if cmp["mode"] == "keyed":
        key = cmp["key"]
        if key not in expected_names:
            raise ValueError("Declared key must appear in comparison columns")
        ca, cb = Counter(r[key] for r in a), Counter(r[key] for r in b)
        for side, counts in (("source", ca), ("target", cb)):
            for k, count in counts.items():
                if count > 1:
                    diffs.append({"kind": "duplicate_key", "side": side, "key": k, "count": count})
        ma, mb = {r[key]: r for r in a}, {r[key]: r for r in b}
        for k in sorted(ma.keys() | mb.keys(), key=str):
            if k not in ma or k not in mb:
                diffs.append({"kind": "missing_key", "key": k, "source_present": k in ma, "target_present": k in mb})
                continue
            for col, rule in rules.items():
                left, right = ma[k][col], mb[k][col]
                if rule["type"] == "decimal" and left is not None and right is not None:
                    same = abs(left - right) <= Decimal(str(rule["tolerance"]))
                else:
                    same = left == right
                if not same:
                    diffs.append({"kind": "value", "key": k, "column": col, "expected": left, "actual": right, "detail": f"{k}.{col}: expected {left}; actual {right}"})
    else:
        def signature(row: dict[str, Any]) -> str:
            return json.dumps(row, sort_keys=True, default=str)
        ca, cb = Counter(map(signature, a)), Counter(map(signature, b))
        for row in sorted(ca.keys() | cb.keys()):
            if ca[row] != cb[row]:
                diffs.append({"kind": "multiset", "row": json.loads(row), "source_count": ca[row], "target_count": cb[row]})
    if cmp["ordered"] and a != b:
        diffs.append({"kind": "order", "detail": "Output sequence differs"})
    return {"status": "FAIL" if diffs else "PASS", "differences": diffs[:100], "difference_count": len(diffs)}


def assess(case_path: Path, output_dir: Path) -> dict[str, Any]:
    """Assess a trusted local case; persist both executed outputs and evidence."""
    case_path = case_path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    spec: dict[str, Any] = {}
    run_id = uuid.uuid4().hex[:16]
    now = datetime.now(timezone.utc).isoformat()
    report: dict[str, Any] = {"run_id": run_id, "executed_at_utc": now, "case_id": spec.get("case_id", case_path.stem), "scope": "SQLite→DuckDB synthetic fixtures only", "rules_version": RULES_VERSION, "fixture_version": FIXTURE_VERSION, "source_provenance": _source_provenance(), "engines": {"source": f"SQLite {sqlite3.sqlite_version}", "target": f"DuckDB {duckdb.__version__}"}, "parser": f"SQLGlot {sqlglot.__version__}", "status": "REVIEW", "stage": "validation", "differences": []}
    try:
        spec = _read_json(case_path)
        report["case_id"] = spec.get("case_id", case_path.stem)
        _validate_spec(spec)
        source_path = (case_path.parent / spec["source_fixture"]).resolve()
        target_path = (case_path.parent / spec["target_fixture"]).resolve()
        source_rows, target_rows = _read_json(source_path)["orders"], _read_json(target_path)["orders"]
        _validate_fixture(source_rows)
        _validate_fixture(target_rows)
        target_sql, rules = _check_ast(spec["source_sql"], require_order=spec["comparison"]["ordered"])
        report.update({"source_sql": spec["source_sql"], "target_sql": target_sql, "applied_rules": rules, "input_hashes": {"case": sha256(case_path.read_bytes()).hexdigest(), "source_fixture": sha256(source_path.read_bytes()).hexdigest(), "target_fixture": sha256(target_path.read_bytes()).hexdigest(), "source_sql": sha256(spec["source_sql"].encode()).hexdigest(), "target_sql": sha256(target_sql.encode()).hexdigest()}, "comparison": spec["comparison"], "fixture_counts": {"source": len(source_rows), "target": len(target_rows)}})
        report["stage"] = "execution"
        with tempfile.TemporaryDirectory() as temp:
            source_db, target_db = Path(temp) / "source.sqlite", Path(temp) / "target.duckdb"
            _load_sqlite(source_db, source_rows)
            _load_duckdb(target_db, target_rows)
            names_a, rows_a, types_a = _execute_sqlite(source_db, spec["source_sql"])
            names_b, rows_b, types_b = _execute_duckdb(target_db, target_sql)
        outputs = {"source": {"columns": names_a, "engine_types": types_a, "rows": rows_a}, "target": {"columns": names_b, "engine_types": types_b, "rows": rows_b}}
        output_json = json.dumps(outputs, default=str, indent=2)
        (output_dir / f"{run_id}-executed-rows.json").write_text(output_json, encoding="utf-8")
        report["result_hashes"] = {side: digest(value) for side, value in outputs.items()}
        report["row_counts"] = {"source": len(rows_a), "target": len(rows_b)}
        report["engine_types"] = {"source": types_a, "target": types_b}
        report["executed_rows_file"] = f"{run_id}-executed-rows.json"
        report["stage"] = "comparison"
        report.update(_compare(names_a, rows_a, names_b, rows_b, spec["comparison"]))
        report["limitations"] = ["PASS covers only these fixtures and SQLite/DuckDB versions", "SQLite DECIMAL affinity may use binary floating point; declared scale/tolerance is applied", "SHA-256 is an integrity digest, not a signature", "No SQL Server or Snowflake execution"]
    except Exception as exc:
        report["status"] = "REVIEW"
        if isinstance(exc, ValueError):
            report["error"] = f"{type(exc).__name__}: {exc}"
        elif isinstance(exc, OSError):
            report["error"] = f"{type(exc).__name__}: local fixture or output unavailable; inspect paths locally"
        else:
            report["error"] = f"{type(exc).__name__}: execution failed; inspect local logs"
    path = output_dir / f"{run_id}-report.json"
    path.write_text(json.dumps(report, default=str, indent=2), encoding="utf-8")
    report["report_file"] = path.name
    return report
