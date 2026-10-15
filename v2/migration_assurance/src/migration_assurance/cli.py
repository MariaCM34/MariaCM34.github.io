"""Run a reviewed case or the bounded built-in suite and export evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from .engine import assess
from .html import render_index, render_report
from .suite import CASES


def run_suite(output: Path) -> list[dict]:
    output.mkdir(parents=True, exist_ok=True)
    cases_dir, fixtures_dir = output / "cases", output / "fixtures"
    cases_dir.mkdir(exist_ok=True)
    fixtures_dir.mkdir(exist_ok=True)
    data_dir = Path(__file__).resolve().parents[2] / "data"
    for name in ("base.json", "mismatch.json", "target_missing.json"):
        shutil.copyfile(data_dir / name, fixtures_dir / name)
    reports = []
    for case in CASES:
        path = cases_dir / f"{case['case_id']}.json"
        path.write_text(json.dumps(case, indent=2), encoding="utf-8", newline="\n")
        report = assess(path, output)
        render_report(report, output / f"{report['run_id']}-report.html")
        reports.append(report)
        print(f"{case['case_id']}: {report['status']} (expected {case['expected_status']})")
    render_index(reports, output / "index.html")
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded SQLite→DuckDB migration evidence")
    sub = parser.add_subparsers(dest="command", required=True)
    suite = sub.add_parser("suite", help="Execute all reviewed synthetic cases")
    suite.add_argument("--out", type=Path, required=True)
    one = sub.add_parser("assess", help="Assess a trusted local case JSON")
    one.add_argument("--case", type=Path, required=True)
    one.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "suite":
        reports = run_suite(args.out)
        count = sum(r["status"] != c["expected_status"] for r, c in zip(reports, CASES))
        print(f"{len(reports)} assessed; {count} unexpected decisions; viewer: {args.out / 'index.html'}")
        return 1 if count else 0
    report = assess(args.case, args.out)
    render_report(report, args.out / f"{report['run_id']}-report.html")
    print(f"{report['case_id']}: {report['status']} | {args.out / report['report_file']}")
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
