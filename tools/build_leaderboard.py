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


def _fmt_num(v: object) -> str:
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        if isinstance(v, float) and not v.is_integer():
            return f"{v:,.2f}"
        return f"{int(v):,}"
    return str(v)


def _load_rows() -> list[dict]:
    rows = []
    for fp in sorted(RESULTS_ROOT.rglob("*.json")):
        rel = fp.relative_to(REPO_ROOT).as_posix()
        p = json.loads(fp.read_text(encoding="utf-8"))
        job, cfg, res, sys = p.get("job", {}), p.get("benchmark_config", {}), p.get("result", {}), p.get("system", {})
        rows.append({
            "jobid": job.get("jobid"), "benchmark": job.get("benchmark"), "database": job.get("database"),
            "database_display": job.get("database_display"), "release": job.get("release"), "timestamp": job.get("timestamp"),
            "hdb_version": job.get("hdb_version"), "nopm": res.get("nopm"), "tpm": res.get("tpm"),
            "geomean_seconds": res.get("geomean_seconds"), "total_query_time_seconds": res.get("total_query_time_seconds"),
            "warehouses": cfg.get("warehouses"), "virtual_users": cfg.get("virtual_users"), "rampup_minutes": cfg.get("rampup_minutes"),
            "duration_minutes": cfg.get("duration_minutes"), "cpu_model": sys.get("cpumodel"), "cpu_count": sys.get("cpucount"),
            "memory": sys.get("memory"), "os_name": sys.get("os_name"), "source_path": rel,
        })
    rows.sort(key=lambda r: (r.get("nopm") is None, -(r.get("nopm") or 0), r.get("jobid") or ""))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def _write_json(rows: list[dict]) -> None:
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "title": "HammerDB Result Artifacts Prototype Data",
        "disclaimer": [
            "Community-submitted HammerDB results",
            "Unaudited",
            "Not official TPC benchmark results",
        ],
        "rows": rows,
    }
    LEADERBOARD_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _row_html(row: dict) -> str:
    encoded = quote(row.get("source_path", ""), safe="")
    report = f"report.html?artifact={encoded}"
    db = row.get("database_display") or row.get("database") or "Unknown"
    release = row.get("release") or "—"
    benchmark = row.get("benchmark") or "—"
    if benchmark == "TPROC-C":
        main = f"<div class='main-metric'>{escape(_fmt_num(row.get('nopm')))} <span>NOPM</span></div><div class='sub-metric'>TPM {_fmt_num(row.get('tpm'))}</div>"
    else:
        main = f"<div class='main-metric'>{escape(_fmt_num(row.get('geomean_seconds')))} <span>Geomean</span></div><div class='sub-metric'>Total Query Time {_fmt_num(row.get('total_query_time_seconds'))}</div>"
    chips = [
        ("Warehouses", row.get("warehouses")),
        ("VUs", row.get("virtual_users")),
        ("Rampup", row.get("rampup_minutes")),
        ("Duration", row.get("duration_minutes")),
    ]
    cfg = "".join(f"<span class='chip'>{k}: {escape(_fmt_num(v))}</span>" for k, v in chips if v is not None)
    sys_bits = [x for x in [row.get("cpu_model"), row.get("cpu_count") and f"CPU x{row.get('cpu_count')}", row.get("memory"), row.get("os_name")] if x]
    sys_txt = " · ".join(escape(str(x)) for x in sys_bits) if sys_bits else "System details unavailable"
    date = row.get("timestamp") or "—"
    return f"""<article class='lb-row'>
<div class='cell rank'>{escape(str(row.get('rank','—')))}</div>
<div class='cell database'><strong>{escape(str(db))}</strong><span class='muted'>Release {escape(str(release))}</span></div>
<div class='cell benchmark'><span class='pill'>{escape(str(benchmark))}</span></div>
<div class='cell result'>{main}</div>
<div class='cell config'>{cfg or '<span class="muted">No configuration data</span>'}</div>
<div class='cell system'>{sys_txt}</div>
<div class='cell date'>{escape(str(date))}</div>
<div class='cell action'><a class='btn' href='{escape(report)}'>View report</a></div>
</article>"""


def _write_html(rows: list[dict]) -> None:
    db_count = len({(r.get("database_display") or r.get("database") or "Unknown") for r in rows})
    top_nopm = max((r.get("nopm") for r in rows if isinstance(r.get("nopm"), (int, float))), default=None)
    html = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>HammerDB Result Artifacts</title>
<style>
:root{{--bg:#f4f7ff;--navy:#0b1535;--card:#ffffff;--text:#0f172a;--muted:#64748b;--line:#dbe4f0;--blue:#2563eb}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);font-family:Inter,Segoe UI,Arial,sans-serif;color:var(--text)}}
.wrap{{max-width:1220px;margin:0 auto;padding:0 20px 28px}}.hero{{background:linear-gradient(135deg,#08112f,#12275f);color:#fff;padding:48px 0 40px;margin-bottom:22px}}
.hero h1{{margin:10px 0 12px;font-size:2.2rem}}.hero p{{max-width:780px;color:#d8e2ff}}
.badges{{display:flex;gap:8px;flex-wrap:wrap}}.badge{{padding:6px 12px;border-radius:999px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.26);font-weight:600;font-size:.84rem}}
.warn{{margin-top:16px;padding:12px 14px;border-radius:12px;background:rgba(245,158,11,.16);border:1px solid rgba(245,158,11,.35);color:#ffe7bd;font-weight:500}}
.top-grid{{display:grid;grid-template-columns:1.4fr 1fr;gap:14px;margin-top:-10px}}@media(max-width:980px){{.top-grid{{grid-template-columns:1fr}}}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 18px;box-shadow:0 8px 24px rgba(15,23,42,.05)}}
.cta h2{{margin:0 0 8px}}.cta .btn{{margin-top:10px}}.btn{{display:inline-block;background:#111827;color:#fff;text-decoration:none;padding:10px 14px;border-radius:10px;font-weight:700}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:16px 0 20px}}@media(max-width:760px){{.stats{{grid-template-columns:1fr}}}}
.stat{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px}}.stat .k{{color:var(--muted);font-size:.84rem}}.stat .v{{margin-top:6px;font-size:1.55rem;font-weight:800}}
.header-row,.lb-row{{display:grid;grid-template-columns:58px 190px 120px 170px 250px 1fr 165px 120px;gap:10px;align-items:center}}
.header-row{{color:var(--muted);font-size:.82rem;font-weight:700;padding:0 10px 8px}}.lb{{display:flex;flex-direction:column;gap:10px}}
.lb-row{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px 10px;box-shadow:0 4px 14px rgba(15,23,42,.04)}}
.cell{{min-width:0}}.rank{{font-weight:800;color:#1d4ed8}}.database strong{{display:block;font-size:1.03rem}}.muted{{display:block;color:var(--muted);font-size:.82rem;margin-top:2px}}
.pill{{display:inline-block;padding:5px 10px;border-radius:999px;background:#e6efff;color:#1d4ed8;font-weight:700;font-size:.82rem}}
.main-metric{{font-size:1.1rem;font-weight:800}}.main-metric span{{font-size:.74rem;color:var(--muted);font-weight:700;margin-left:4px;text-transform:uppercase}}
.sub-metric{{color:var(--muted);font-size:.86rem;margin-top:3px}}.config{{display:flex;flex-wrap:wrap;gap:6px}}
.chip{{background:#eef4ff;border:1px solid #d5e3ff;color:#25407a;border-radius:999px;padding:3px 8px;font-size:.78rem;font-weight:600}}
.system,.date{{color:#334155;font-size:.86rem;line-height:1.35}}.action .btn{{background:var(--blue);padding:8px 11px;font-size:.84rem}}
@media(max-width:1160px){{.header-row{{display:none}}.lb-row{{grid-template-columns:1fr;gap:8px}}.cell::before{{content:attr(data-label);display:block;color:var(--muted);font-size:.75rem;font-weight:700;margin-bottom:2px;text-transform:uppercase;letter-spacing:.02em}}.rank::before{{content:'Rank'}}.database::before{{content:'Database'}}.benchmark::before{{content:'Benchmark'}}.result::before{{content:'Result'}}.config::before{{content:'Configuration'}}.system::before{{content:'System'}}.date::before{{content:'Date'}}.action::before{{content:'Action'}}}}
</style></head><body>
<header class='hero'><div class='wrap'><div class='badges'><span class='badge'>Prototype</span><span class='badge'>Community Submitted</span><span class='badge'>Unofficial</span></div>
<h1>HammerDB Result Artifacts</h1>
<p>Community-submitted HammerDB benchmark result artifacts, reviewed through GitHub.</p>
<div class='warn'>These are community-submitted HammerDB results. They are not official TPC benchmark results.</div></div></header>
<main class='wrap'>
<section class='top-grid'><article class='card cta'><h2>Star HammerDB on GitHub</h2><p>Join the project community and help others discover HammerDB.</p><a class='btn' href='https://github.com/TPC-Council/HammerDB'>★ Star HammerDB</a></article>
<article class='card'><h3 style='margin:0 0 8px'>Submission guidance</h3><p style='margin:0;color:var(--muted)'>To submit a result, open the benchmark report in HammerDB and use Share with TPC-OSS.</p></article></section>
<section class='stats'><article class='stat'><div class='k'>Published results</div><div class='v'>{len(rows)}</div></article><article class='stat'><div class='k'>Databases</div><div class='v'>{db_count}</div></article><article class='stat'><div class='k'>Top NOPM</div><div class='v'>{escape(_fmt_num(top_nopm))}</div></article></section>
<section><div class='header-row'><div>Rank</div><div>Database</div><div>Benchmark</div><div>Result</div><div>Configuration</div><div>System</div><div>Date</div><div>Action</div></div>
<div class='lb'>{''.join(_row_html(r) for r in rows)}</div></section>
</main></body></html>"""
    INDEX_HTML.write_text(html, encoding="utf-8")


def main() -> int:
    SITE_ROOT.mkdir(parents=True, exist_ok=True)
    rows = _load_rows()
    _write_json(rows)
    _write_html(rows)
    print(f"Generated {LEADERBOARD_JSON.relative_to(REPO_ROOT)} and {INDEX_HTML.relative_to(REPO_ROOT)} with {len(rows)} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
