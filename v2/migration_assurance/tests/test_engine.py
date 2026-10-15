from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path

import pytest

from migration_assurance.cli import run_suite
from migration_assurance.engine import _check_ast, _compare, assess
from migration_assurance.suite import CASES, DECIMAL, INTEGER, TEXT


DATA = Path(__file__).resolve().parents[1] / "data"


def write_case(tmp_path, spec, target="base.json", mutate=None):
    rows = json.loads((DATA / target).read_text(encoding="utf-8"))
    if mutate:
        mutate(rows["orders"])
    fixture = tmp_path / "target.json"
    fixture.write_text(json.dumps(rows), encoding="utf-8")
    case = deepcopy(spec)
    case["source_fixture"] = str(DATA / "base.json")
    case["target_fixture"] = str(fixture)
    case_path = tmp_path / "case.json"
    case_path.write_text(json.dumps(case), encoding="utf-8")
    return case_path


def test_full_executed_suite_has_eleven_distinct_supported_queries(tmp_path):
    reports = run_suite(tmp_path)
    assert len(reports) == 17
    assert [r["status"] for r in reports] == [c["expected_status"] for c in CASES]
    supported = reports[:11]
    assert len({r["source_sql"] for r in supported}) == 11
    for r in supported:
        assert r["status"] == "PASS"
        assert r["result_hashes"]["source"]
        assert r["result_hashes"]["target"]
        assert (tmp_path / r["executed_rows_file"]).exists()
        assert r["row_counts"]["source"] == r["row_counts"]["target"]
    assert (tmp_path / "index.html").exists()


def test_deliberate_amount_mismatch_is_record_level_fail(tmp_path):
    p = write_case(tmp_path, CASES[11], target="mismatch.json")
    r = assess(p, tmp_path)
    assert r["status"] == "FAIL"
    assert any(d.get("detail") == "A-001.amount: expected 10.00; actual 11.00" for d in r["differences"])
    assert r["input_hashes"]["source_fixture"] != r["input_hashes"]["target_fixture"]


def test_missing_key_and_count_detected(tmp_path):
    p = write_case(tmp_path, CASES[12], target="target_missing.json")
    r = assess(p, tmp_path)
    assert r["status"] == "FAIL"
    assert any(d["kind"] == "missing_key" and d["key"] == "A-004" for d in r["differences"])
    assert any(d["kind"] == "row_count" for d in r["differences"])


def test_duplicate_aware_multiset_counts_changed_duplicates(tmp_path):
    def mutate(rows):
        rows[3]["status"] = "pending"  # paid: source 3, target 2; pending: source 1, target 2
    p = write_case(tmp_path, CASES[10], mutate=mutate)
    r = assess(p, tmp_path)
    assert r["status"] == "FAIL"
    assert any(d["kind"] == "multiset" and d["source_count"] != d["target_count"] for d in r["differences"])


def test_null_semantics_difference_detected(tmp_path):
    def mutate(rows):
        rows[1]["amount"] = "0.00"
    p = write_case(tmp_path, CASES[0], mutate=mutate)
    r = assess(p, tmp_path)
    assert r["status"] == "FAIL"
    assert any(d["key"] == "A-002" and d["expected"] is None and str(d["actual"]) == "0.00" for d in r["differences"] if d["kind"] == "value")


def test_comparator_type_order_and_tolerance():
    cmp = {"mode": "keyed", "key": "order_id", "columns": {"order_id": TEXT, "amount": DECIMAL}, "ordered": True, "timezone": "UTC"}
    a = [["A", Decimal("10.00")], ["B", Decimal("11.00")]]
    assert _compare(["order_id", "amount"], a, ["order_id", "amount"], list(reversed(a)), cmp)["status"] == "FAIL"
    assert _compare(["order_id", "amount"], a, ["order_id", "amount"], [["A", "bad"], ["B", "11.00"]], cmp)["differences"][0]["kind"] == "type"
    assert _compare(["order_id", "amount"], [["A", "10.00"]], ["order_id", "amount"], [["A", "10.00"]], cmp)["status"] == "PASS"


@pytest.mark.parametrize("sql", [
    "DELETE FROM orders", "SELECT order_id FROM orders; DROP TABLE orders",
    "SELECT order_id FROM orders LIMIT 2", "SELECT load_extension('x') FROM orders",
    "SELECT * FROM users", "SELECT o.order_id FROM orders o JOIN users u ON o.order_id=u.id",
    "WITH x AS (SELECT * FROM orders) SELECT * FROM x", "SELECT random() FROM orders",
])
def test_unsafe_or_ambiguous_sql_is_review(sql):
    with pytest.raises(ValueError):
        _check_ast(sql)


def test_report_exposes_review_and_never_executed_rows_for_mutation(tmp_path):
    p = write_case(tmp_path, CASES[13])
    r = assess(p, tmp_path)
    assert r["status"] == "REVIEW"
    assert "SELECT" in r["error"]
    assert "executed_rows_file" not in r


def test_repeat_decision_and_input_hashes_stable(tmp_path):
    p = write_case(tmp_path, CASES[0])
    a, b = assess(p, tmp_path), assess(p, tmp_path)
    assert a["status"] == b["status"] == "PASS"
    assert a["input_hashes"] == b["input_hashes"]
    assert a["result_hashes"] == b["result_hashes"]
    assert a["run_id"] != b["run_id"]
    assert (tmp_path / a["report_file"]).exists() and (tmp_path / b["report_file"]).exists()


def test_invalid_contract_is_review(tmp_path):
    spec = deepcopy(CASES[0])
    spec["comparison"]["columns"]["amount"].pop("tolerance")
    p = write_case(tmp_path, spec)
    r = assess(p, tmp_path)
    assert r["status"] == "REVIEW"
    assert "tolerance" in r["error"]


def test_ordered_contract_checks_ast_not_literal_text(tmp_path):
    spec = deepcopy(CASES[0])
    spec["source_sql"] = "SELECT order_id FROM orders WHERE status = 'ORDER BY'"
    spec["comparison"]["columns"] = {"order_id": TEXT}
    p = write_case(tmp_path, spec)
    r = assess(p, tmp_path)
    assert r["status"] == "REVIEW"
    assert "AST ORDER BY" in r["error"]
    assert "executed_rows_file" not in r


def test_bad_fixture_date_is_review_even_when_query_does_not_project_it(tmp_path):
    def mutate(rows):
        rows[0]["ordered_on"] = "2026-02-30"
    p = write_case(tmp_path, CASES[0], mutate=mutate)
    r = assess(p, tmp_path)
    assert r["status"] == "REVIEW"
    assert "ordered_on" in r["error"]


def test_html_escapes_case_name(tmp_path):
    spec = deepcopy(CASES[0])
    spec["case_id"] = "<script>alert(1)</script>"
    p = write_case(tmp_path, spec)
    r = assess(p, tmp_path)
    from migration_assurance.html import render_report
    html_path = tmp_path / "report.html"
    render_report(r, html_path)
    html = html_path.read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
