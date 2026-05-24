#!/usr/bin/env python3
from __future__ import annotations
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_ROOT = REPO_ROOT / "results"
SITE_ROOT = REPO_ROOT / "site"
LEADERBOARD_JSON = SITE_ROOT / "leaderboard.json"
INDEX_HTML = SITE_ROOT / "index.html"

def _load_rows() -> list[dict]:
    rows=[]
    for fp in sorted(RESULTS_ROOT.rglob("*.json")):
        rel=fp.relative_to(REPO_ROOT).as_posix()
        p=json.loads(fp.read_text(encoding="utf-8"))
        j,c,r,s=p.get("job",{}),p.get("benchmark_config",{}),p.get("result",{}),p.get("system",{})
        rows.append({"jobid":j.get("jobid"),"benchmark":j.get("benchmark"),"database":j.get("database"),"database_display":j.get("database_display"),"release":j.get("release"),"timestamp":j.get("timestamp"),"hdb_version":j.get("hdb_version"),"nopm":r.get("nopm"),"tpm":r.get("tpm"),"geomean_seconds":r.get("geomean_seconds"),"total_query_time_seconds":r.get("total_query_time_seconds"),"warehouses":c.get("warehouses"),"virtual_users":c.get("virtual_users"),"rampup_minutes":c.get("rampup_minutes"),"duration_minutes":c.get("duration_minutes"),"cpu_model":s.get("cpumodel"),"cpu_count":s.get("cpucount"),"memory":s.get("memory"),"os_name":s.get("os_name"),"source_path":rel})
    rows.sort(key=lambda r:(r.get("nopm") is None,-(r.get("nopm") or 0),r.get("jobid") or ""))
    for i,r in enumerate(rows,1): r["rank"]=i
    return rows

def _write_json(rows:list[dict])->None:
    payload={"generated_at_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat(),"title":"HammerDB Result Artifacts Prototype Data","disclaimer":["Prototype data output for HammerDB result artifacts.","Intended live publication repository: https://github.com/TPC-Council/hammerdb-results","Intended live GitHub Pages site: https://tpc-council.github.io/hammerdb-results/","Official public entry point: https://www.tpc.org/opensource/opensource5.asp","Community-submitted HammerDB results","Unaudited","Not official TPC benchmark results"],"rows":rows}
    LEADERBOARD_JSON.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

def _stats(rows:list[dict])->tuple[str,str,str]:
    count=str(len(rows))
    dbs=str(len({(r.get("database_display") or r.get("database") or "").strip() for r in rows if (r.get("database_display") or r.get("database"))}))
    nopm_vals=[r.get("nopm") for r in rows if isinstance(r.get("nopm"),(int,float))]
    top=f"{int(max(nopm_vals)):,}" if nopm_vals else "—"
    return count,dbs,top

def _result_cell(r:dict)->str:
    if r.get("benchmark")=="TPROC-C":
        return f"<div class='result-main'>NOPM {escape(str(r.get('nopm','—')))}</div><div class='result-sub'>TPM {escape(str(r.get('tpm','—')))}</div>"
    return f"<div class='result-main'>Geomean {escape(str(r.get('geomean_seconds','—')))}</div><div class='result-sub'>Total Query Time {escape(str(r.get('total_query_time_seconds','—')))}</div>"

def _write_html(rows:list[dict])->None:
    published,dbs,top=_stats(rows)
    body=[]
    for r in rows:
        chips=[]
        for label,key in (("Warehouses","warehouses"),("VUs","virtual_users"),("Rampup","rampup_minutes"),("Duration","duration_minutes")):
            if r.get(key) is not None: chips.append(f"<span class='chip'>{label}: {escape(str(r[key]))}</span>")
        sys=" · ".join(x for x in [r.get("cpu_model"),r.get("cpu_count") and f"CPU {r.get('cpu_count')}",r.get("memory"),r.get("os_name")] if x) or "—"
        href=f"report.html?artifact={quote(r.get('source_path',''),safe='')}"
        body.append(f"""<tr>
<td><span class='rank'>#{escape(str(r.get('rank','')))}</span></td>
<td><div class='db'>{escape(str(r.get('database_display') or r.get('database') or '—'))}</div><div class='meta'>Release {escape(str(r.get('release') or '—'))}</div></td>
<td><span class='badge'>{escape(str(r.get('benchmark') or '—'))}</span></td>
<td>{_result_cell(r)}</td>
<td><div class='chips'>{''.join(chips) or '<span class="meta">—</span>'}</div></td>
<td><div class='meta'>{escape(sys)}</div></td>
<td><div class='meta'>{escape(str(r.get('timestamp') or '—'))}</div><div class='meta'>HammerDB {escape(str(r.get('hdb_version') or '—'))}</div></td>
<td><a class='btn' href='{escape(href)}'>View report</a></td>
</tr>""")

    html=f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>HammerDB Result Artifacts</title><style>
:root{{--bg:#0a1430;--bg2:#1d2f68;--surface:#fff;--text:#0f172a;--muted:#64748b;--line:#e2e8f0;--primary:#2563eb;}}
*{{box-sizing:border-box}}body{{margin:0;background:#f3f6fc;color:var(--text);font-family:Inter,Segoe UI,Arial,sans-serif}}.wrap{{max-width:1180px;margin:0 auto;padding:24px}}
.hero{{background:radial-gradient(1200px 300px at 10% -10%,#3456b4,transparent),linear-gradient(135deg,var(--bg),var(--bg2));color:#edf2ff;border-radius:18px;padding:28px 30px;box-shadow:0 16px 30px rgba(10,20,48,.22)}}
.hero h1{{margin:10px 0 6px;font-size:2rem}}.hero p{{margin:0;color:#c7d3ff}}.badges{{display:flex;gap:8px;flex-wrap:wrap}}.pill{{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.2);padding:5px 10px;border-radius:999px;font-size:.8rem}}
.warn{{margin-top:14px;background:rgba(255,196,87,.15);border:1px solid rgba(255,196,87,.45);padding:10px;border-radius:10px;color:#ffe6a8}}
.topcards{{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:12px;margin-top:14px}}@media(max-width:900px){{.topcards{{grid-template-columns:1fr}}}}
.card{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px;box-shadow:0 4px 14px rgba(2,6,23,.05)}}.cta h3,.info h3{{margin:0 0 6px}}
.star{{display:inline-block;margin-top:8px;background:#111827;color:#fff;padding:9px 12px;border-radius:10px;text-decoration:none;font-weight:700}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:14px 0}}@media(max-width:760px){{.stats{{grid-template-columns:1fr}}}}
.stat .label{{color:var(--muted);font-size:.83rem}}.stat .val{{font-size:1.45rem;font-weight:800;margin-top:4px}}
.board{{background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:0 6px 16px rgba(2,6,23,.06)}}
table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;border-bottom:1px solid #eef2f7;vertical-align:top;text-align:left}}th{{font-size:.82rem;color:#64748b;background:#f8fbff}}
@media(max-width:980px){{thead{{display:none}}table,tbody,tr,td{{display:block;width:100%}}tr{{border-bottom:1px solid #eef2f7}}td{{padding:8px 12px}}td::before{{content:attr(data-label);display:block;font-size:.74rem;color:#64748b;margin-bottom:3px}}}}
.rank{{background:#e0e7ff;color:#1e3a8a;padding:4px 10px;border-radius:999px;font-weight:700}}.db{{font-weight:700}}.meta{{color:var(--muted);font-size:.9rem}}
.badge{{background:#eef2ff;color:#3730a3;border-radius:999px;padding:4px 9px;font-size:.8rem;font-weight:700}}.result-main{{font-size:1.05rem;font-weight:800}}.result-sub{{color:#64748b;font-size:.9rem}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}}.chip{{background:#f1f5f9;border:1px solid #e2e8f0;border-radius:999px;padding:4px 8px;font-size:.78rem}}
.btn{{display:inline-block;background:var(--primary);color:#fff;text-decoration:none;padding:8px 11px;border-radius:10px;font-weight:700;white-space:nowrap}}
.footer-note{{margin-top:12px;color:#475569;font-size:.92rem}}
</style></head><body><main class='wrap'>
<section class='hero'><div class='badges'><span class='pill'>Prototype</span><span class='pill'>Community Submitted</span><span class='pill'>Unofficial</span></div>
<h1>HammerDB Result Artifacts</h1><p>Community-submitted HammerDB benchmark result artifacts, reviewed through GitHub.</p>
<div class='warn'>These are community-submitted HammerDB results. They are not official TPC benchmark results.</div></section>
<section class='topcards'><article class='card cta'><h3>Star HammerDB on GitHub</h3><p>Join the project community and help others discover HammerDB.</p><a class='star' aria-label='Star HammerDB on GitHub' href='https://github.com/TPC-Council/HammerDB'>★ Star HammerDB</a></article>
<article class='card info' style='grid-column:span 2'><h3>Submission guidance</h3><p>To submit a result, open the benchmark report in HammerDB and use Share with TPC-OSS.</p></article></section>
<section class='stats'><article class='card stat'><div class='label'>Published results</div><div class='val'>{published}</div></article><article class='card stat'><div class='label'>Databases</div><div class='val'>{dbs}</div></article><article class='card stat'><div class='label'>Top NOPM</div><div class='val'>{top}</div></article></section>
<section class='board'><table><thead><tr><th>Rank</th><th>Database</th><th>Benchmark</th><th>Result</th><th>Configuration</th><th>System</th><th>Date</th><th>Action</th></tr></thead><tbody>{''.join(body)}</tbody></table></section>
<p class='footer-note'>Community-submitted HammerDB results • Unaudited • Not official TPC benchmark results</p>
</main></body></html>"""
    INDEX_HTML.write_text(html,encoding="utf-8")

def main()->int:
    SITE_ROOT.mkdir(parents=True,exist_ok=True)
    rows=_load_rows();_write_json(rows);_write_html(rows)
    print(f"Generated {LEADERBOARD_JSON.relative_to(REPO_ROOT)} and {INDEX_HTML.relative_to(REPO_ROOT)} with {len(rows)} row(s).")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
