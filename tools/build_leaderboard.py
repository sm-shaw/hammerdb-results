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

def _short_os(v: object) -> str:
    s = str(v or "").replace("LTS", "").strip()
    parts = s.split()
    return " ".join(parts[:2]) if parts else "—"

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
        "disclaimer": ["Community-submitted HammerDB results", "Unaudited", "Not official TPC benchmark results"],
        "rows": rows,
    }
    LEADERBOARD_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def _row_html(row: dict) -> str:
    report = f"report.html?artifact={quote(row.get('source_path',''), safe='')}"
    db = row.get("database_display") or row.get("database") or "Unknown"
    benchmark = row.get("benchmark") or "—"
    if benchmark == "TPROC-C":
        result_html = f"<div class='main-metric'>{escape(_fmt_num(row.get('nopm')))} <span>NOPM</span></div><div class='sub-metric'>TPM {escape(_fmt_num(row.get('tpm')))}</div>"
    else:
        result_html = f"<div class='main-metric'>{escape(_fmt_num(row.get('geomean_seconds')))} <span>Geomean</span></div><div class='sub-metric'>Total Query Time {escape(_fmt_num(row.get('total_query_time_seconds')))}</div>"
    chips = [("Warehouses", row.get("warehouses")), ("VUs", row.get("virtual_users")), ("Rampup", row.get("rampup_minutes")), ("Duration", row.get("duration_minutes"))]
    cfg = "".join(f"<span class='chip'>{k}: {escape(_fmt_num(v))}</span>" for k, v in chips if v is not None)
    compact_sys = " · ".join([x for x in [row.get("cpu_count") and f"CPU {row.get('cpu_count')}", row.get("memory"), _short_os(row.get("os_name"))] if x and x != "—"])
    return f"""<article class='lb-row'>
<div class='left'><div class='rank'>#{escape(str(row.get('rank','—')))}</div><div><strong>{escape(str(db))}</strong><div class='muted'>Release {escape(str(row.get('release') or '—'))} · {escape(str(benchmark))}</div></div></div>
<div class='mid'><div class='result'>{result_html}</div><div class='config'>{cfg}</div></div>
<div class='right'><div class='system'>{escape(compact_sys or 'System unavailable')}</div><div class='date'>{escape(str(row.get('timestamp') or '—'))}</div><a class='btn' href='{escape(report)}'>View report</a></div>
</article>"""

def _write_html(rows: list[dict]) -> None:
    db_count = len({(r.get("database_display") or r.get("database") or "Unknown") for r in rows})
    top_nopm = max((r.get("nopm") for r in rows if isinstance(r.get("nopm"), (int, float))), default=None)
    html = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>HammerDB Result Artifacts</title>
<style>:root{{--bg:#fff;--page:#fff;--panel:#fff;--line:#e2e8f0;--line-strong:#cbd5e1;--muted:#64748b;--blue:#2563eb;--text:#0f172a}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);font-family:Inter,Segoe UI,Arial,sans-serif;color:var(--text)}}
.wrap{{max-width:1220px;margin:0 auto;padding:0 24px 32px}}.hero{{background:#fff;color:var(--text);padding:22px 0 0;margin-bottom:0}}
.brandbar{{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;margin-bottom:12px}}.brand-left{{display:flex;align-items:flex-end;gap:18px}}.brand-hammerdb{{height:62px;width:auto;display:block}}.brand-tpc{{height:62px;width:auto;display:block;margin-top:0}}
.hero h1{{margin:0;font-size:2.2rem;letter-spacing:-.03em;line-height:1.08}}.hero p{{max-width:780px;color:#334155;margin:0}}.badges{{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 0}}.badge{{padding:6px 12px;border-radius:999px;background:#f8fafc;border:1px solid var(--line-strong);color:#1e3a8a;font-weight:700;font-size:.84rem}}
.warn{{margin-top:16px;padding:12px 14px;border-radius:12px;background:#fffaf3;border:1px solid #fdba74;color:#9a3412;font-weight:600;margin-bottom:0}}
.top-grid{{display:grid;grid-template-columns:1.4fr 1fr;gap:16px;margin:8px 0 16px}}.card{{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:18px 20px;box-shadow:0 1px 2px rgba(15,23,42,.04)}}
.btn{{display:inline-block;background:#111827;color:#fff;text-decoration:none;padding:9px 12px;border-radius:10px;font-weight:800}}.star{{color:#facc15;margin-right:4px}}.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0 20px}}
.stat{{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:14px 16px;box-shadow:0 1px 2px rgba(15,23,42,.035)}}.stat .k{{color:var(--muted);font-size:.84rem}}.stat .v{{margin-top:6px;font-size:1.5rem;font-weight:850;letter-spacing:-.02em}}
.lb{{display:flex;flex-direction:column;gap:10px}}.lb-row{{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:14px;display:grid;grid-template-columns:1.15fr 1.4fr .95fr;gap:12px;align-items:center;box-shadow:0 1px 2px rgba(15,23,42,.035)}}
.lb-row:hover{{border-color:var(--line-strong);box-shadow:0 8px 20px rgba(15,23,42,.06)}}.left{{display:flex;gap:10px;align-items:center}}.rank{{font-weight:850;color:#1d4ed8;min-width:38px}}.left strong{{font-size:1.03rem}}.muted{{color:var(--muted);font-size:.84rem}}
.main-metric{{font-size:1.18rem;font-weight:850;letter-spacing:-.015em}}.main-metric span{{font-size:.72rem;color:var(--muted);text-transform:uppercase}}.sub-metric{{color:var(--muted);font-size:.86rem;margin-top:2px}}
.config{{display:flex;flex-wrap:wrap;gap:6px;margin-top:7px}}.chip{{background:#f8fafc;border:1px solid #dbeafe;color:#25407a;border-radius:999px;padding:2px 8px;font-size:.76rem;font-weight:700}}
.right{{text-align:right}}.system{{font-size:.88rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.date{{color:var(--muted);font-size:.82rem;margin:4px 0 7px}}.right .btn{{background:var(--blue)}}
@media(max-width:980px){{.top-grid,.stats{{grid-template-columns:1fr}}.lb-row{{grid-template-columns:1fr}}.right{{text-align:left}}.system{{white-space:normal}}}}@media(max-width:700px){{.brandbar{{align-items:center}}.brand-hammerdb{{height:48px}}.brand-tpc{{height:48px}}.brand-left{{gap:12px}}.hero h1{{font-size:1.8rem}}}}</style></head><body>
<header class='hero'><div class='wrap'><div class='brandbar'><div class='brand-left'><img class='brand-hammerdb' src='assets/images/hammerDB-H-logo-FINAL.png' alt='HammerDB'><h1>HammerDB Result Artifacts</h1></div><img class='brand-tpc' src='assets/images/tpclogo.png' alt='TPC'></div><p>Community-submitted HammerDB benchmark result artifacts, reviewed through GitHub.</p><div class='badges'><span class='badge'>Prototype</span><span class='badge'>Community Submitted</span><span class='badge'>Unofficial</span></div><div class='warn'>These are community-submitted HammerDB results. They are not official TPC benchmark results.</div></div></header>
<main class='wrap'><section class='top-grid'><article class='card'><h2 style='margin:0 0 8px'>Star HammerDB on GitHub</h2><p>Help others discover HammerDB by starring the project.</p><a class='btn' href='https://github.com/TPC-Council/HammerDB'><span class='star'>★</span> Star HammerDB</a></article><article class='card'><h3 style='margin:0 0 8px'>Submission guidance</h3><p style='margin:0;color:var(--muted)'>To submit a result, open the benchmark report in HammerDB and use Share with TPC-OSS.</p></article></section>
<section class='stats'><article class='stat'><div class='k'>Published results</div><div class='v'>{len(rows)}</div></article><article class='stat'><div class='k'>Databases</div><div class='v'>{db_count}</div></article><article class='stat'><div class='k'>Top NOPM</div><div class='v'>{escape(_fmt_num(top_nopm))}</div></article></section>
<section class='lb'>{''.join(_row_html(r) for r in rows)}</section></main></body></html>"""
    INDEX_HTML.write_text(html, encoding='utf-8')

def main() -> int:
    SITE_ROOT.mkdir(parents=True, exist_ok=True)
    rows = _load_rows(); _write_json(rows); _write_html(rows)
    print(f"Generated {LEADERBOARD_JSON.relative_to(REPO_ROOT)} and {INDEX_HTML.relative_to(REPO_ROOT)} with {len(rows)} row(s).")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
