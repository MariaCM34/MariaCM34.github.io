"""Dependency-free, escaped static evidence viewer (read-only)."""

from __future__ import annotations

from html import escape
import json
from pathlib import Path
from difflib import unified_diff


STYLE = """
:root{color-scheme:dark;font-family:Inter,system-ui,Arial,sans-serif;background:#0d1321;color:#f3f7fb}
*{box-sizing:border-box}body{margin:0;line-height:1.5}main{max-width:1120px;margin:auto;padding:28px 20px 80px}
h1{font-size:clamp(2rem,5vw,3.8rem);line-height:1.08;margin:12px 0}h2{font-size:1.25rem;margin:0 0 14px}
p{color:#b7c8d8}.eyebrow{color:#70e1cd;text-transform:uppercase;letter-spacing:.15em;font-size:.76rem;font-weight:700}
.hero{padding:28px;border:1px solid #35506b;border-radius:20px;background:linear-gradient(125deg,#152a3e,#111928)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:14px;margin:22px 0}
.card{border:1px solid #334b62;border-radius:16px;background:#162337;padding:20px;min-width:0}
.muted{color:#9eb4c8;font-size:.9rem}.mono,pre,code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
pre{background:#08131f;border:1px solid #2b4055;padding:15px;border-radius:12px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere}
.badge{display:inline-block;padding:5px 11px;border-radius:20px;font-weight:800;font-size:.8rem;letter-spacing:.06em}
.PASS{background:#133d36;color:#8af0c8}.FAIL{background:#4b252b;color:#ffb9b9}.REVIEW{background:#48391e;color:#ffdf94}
a{color:#80e4d6}button,select{background:#1e344b;color:#fff;border:1px solid #63849d;border-radius:8px;padding:8px 12px;font:inherit}
button{cursor:pointer}button:focus-visible,select:focus-visible,a:focus-visible{outline:3px solid #f7ca61;outline-offset:3px}
table{border-collapse:collapse;width:100%;font-size:.92rem}th,td{text-align:left;padding:8px;border-bottom:1px solid #365069;vertical-align:top;overflow-wrap:anywhere}
.table-wrap{overflow-x:auto}.bar{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:18px 0}
.flow{display:flex;gap:10px;flex-wrap:wrap}.flow span{background:#223b50;padding:8px 12px;border-radius:9px}.flow span:not(:last-child):after{content:' →'}
details{margin:10px 0}summary{cursor:pointer;color:#8ce5d5}small{color:#a7bdd0}
"""


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _pre(value: object) -> str:
    return f"<pre>{_e(value)}</pre>"


def render_report(report: dict, output: Path) -> None:
    differences = report.get("differences", [])
    rows = "".join(f"<tr><td>{_e(item.get('kind'))}</td><td>{_e(item.get('key', item.get('row', '—')))}</td><td>{_e(item.get('detail', json.dumps(item, default=str)))}</td></tr>" for item in differences)
    if not rows:
        rows = '<tr><td colspan="3">No differences detected in the executed fixture results.</td></tr>'
    sql = f"<div class='grid'><section class='card'><h2>SQLite source SQL</h2>{_pre(report.get('source_sql','Not executed'))}</section><section class='card'><h2>DuckDB translated SQL</h2>{_pre(report.get('target_sql','Not generated'))}</section></div>"
    delta = "\n".join(unified_diff(report.get("source_sql", "").splitlines(), report.get("target_sql", "").splitlines(), fromfile="source.sqlite.sql", tofile="target.duckdb.sql", lineterm=""))
    checks = [
        ("Contract and fixture validated", bool(report.get("input_hashes"))),
        ("AST allowlist and dialect translation accepted", bool(report.get("target_sql"))),
        ("Both engines actually executed", bool(report.get("result_hashes"))),
        ("Declared typed comparison passed", report["status"] == "PASS"),
    ]
    checklist = "".join(f"<li>{'✓' if okay else '✕'} {_e(label)}</li>" for label, okay in checks)
    rows_link = (f'<a href="{_e(report["executed_rows_file"])}">Both executed outputs</a>'
                 if report.get("executed_rows_file") else "No executed rows; assessment stopped for review")
    body = f"""<main><a href="index.html">← All cases</a><div class="hero"><div class="eyebrow">Synthetic • executed evidence • SQLite → DuckDB</div>
    <h1>{_e(report['case_id'])}</h1><span class="badge {_e(report['status'])}">{_e(report['status'])}</span>
    <p>PASS means only that this fixture agreed under its declared comparison rule. FAIL blocks the case; REVIEW needs human analysis.</p>
    <small>Run {_e(report['run_id'])} · UTC {_e(report['executed_at_utc'])}</small></div>
    <div class="flow" aria-label="Execution flow"><span>Versioned case + two fixtures</span><span>SQLGlot AST review</span><span>SQLite + DuckDB execution</span><span>Typed comparison</span><span>Evidence report</span></div>
    <div class="grid"><div class="card"><h2>Actual engines</h2><p>{_e(report['engines']['source'])}<br>{_e(report['engines']['target'])}<br>{_e(report['parser'])}</p></div>
    <div class="card"><h2>Executed rows</h2><p>SQLite: {_e(report.get('row_counts',{}).get('source','—'))}<br>DuckDB: {_e(report.get('row_counts',{}).get('target','—'))}</p></div>
    <div class="card"><h2>Decision</h2><p>{_e(report.get('error', 'No execution error.'))}</p></div></div>
    {sql}<div class="grid"><section class="card"><h2>Generated SQL diff</h2>{_pre(delta or 'No textual change')}</section><section class="card"><h2>Compatibility checklist</h2><ul>{checklist}</ul><p class="muted">Rules applied: {_e(', '.join(report.get('applied_rules', [])) or 'none; stopped for review')}</p></section></div>
    <section class="card"><h2>Record-level differences</h2><div class="table-wrap"><table><thead><tr><th>Kind</th><th>Key / row</th><th>Evidence</th></tr></thead><tbody>{rows}</tbody></table></div></section>
    <div class="grid"><section class="card"><h2>Declared comparator</h2>{_pre(json.dumps(report.get('comparison',{}),indent=2))}</section>
    <section class="card"><h2>Provenance and hashes</h2>{_pre(json.dumps({'input_hashes':report.get('input_hashes'), 'result_hashes':report.get('result_hashes'),'rules_version':report.get('rules_version'),'fixture_version':report.get('fixture_version'),'source_provenance':report.get('source_provenance')},indent=2))}</section></div>
    <section class="card"><h2>Evidence and scope</h2><p><a href="{_e(report['run_id'])}-report.json">JSON decision</a> · {rows_link}</p>
    <p>Only synthetic SQLite and DuckDB fixtures were run. No SQL Server or Snowflake equivalence is claimed. SHA-256 indicates integrity, not signer identity.</p></section></main>"""
    output.write_text(f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{_e(report["case_id"])} · Migration Assurance</title><style>{STYLE}</style>{body}</html>', encoding="utf-8")


def render_index(reports: list[dict], output: Path) -> None:
    cards = []
    for r in reports:
        counts = r.get("row_counts", {})
        summary = r.get("error") or f"Source {counts.get('source', '—')} rows → target {counts.get('target', '—')} rows"
        cards.append(f'<article class="card case" data-status="{_e(r["status"])}"><span class="badge {_e(r["status"])}">{_e(r["status"])}</span><h2>{_e(r["case_id"])}</h2><p>{_e(summary)}</p><a href="{_e(r["run_id"])}-report.html">Inspect executed evidence →</a></article>')
    cards = "".join(cards)
    # Filter controls modify only already-exported evidence; no SQL is submitted by the browser.
    body = f'''<main><div class="hero"><div class="eyebrow">Synthetic data · local reference implementation</div><h1>Migration Assurance</h1><p>SQL migration is a claim to test, not a string to rewrite. These cases were parsed, translated, run against separate SQLite and DuckDB databases, then compared with declared types.</p><small>Static snapshot generated from executed local runs. No live public SQL execution.</small></div><div class="bar"><label for="status">Decision filter</label><select id="status"><option value="ALL">All</option><option>PASS</option><option>FAIL</option><option>REVIEW</option></select><span id="count" aria-live="polite"></span></div><div class="grid">{cards}</div><section class="card"><h2>Interpretation</h2><p>PASS covers only the tested inputs, engines and comparison contract. FAIL means observed difference. REVIEW means unsupported or unsafe input; no success claim. The deliberate A-001 amount mismatch is expected to fail.</p></section></main><script>const s=document.querySelector('#status'),a=[...document.querySelectorAll('.case')],c=document.querySelector('#count');function f(){{let n=0;for(const x of a){{const show=s.value==='ALL'||x.dataset.status===s.value;x.hidden=!show;if(show)n++}}c.textContent=n+' of '+a.length+' cases'}}s.addEventListener('change',f);f()</script>'''
    output.write_text(f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Migration Assurance · Executed evidence</title><style>{STYLE}</style>{body}</html>',encoding="utf-8")
