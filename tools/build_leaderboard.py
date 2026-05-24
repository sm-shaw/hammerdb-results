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
            "Prototype data output for HammerDB result artifacts.",
            "Intended live publication repository: https://github.com/TPC-Council/hammerdb-results",
            "Intended live GitHub Pages site: https://tpc-council.github.io/hammerdb-results/",
            "Official public entry point: https://www.tpc.org/opensource/opensource5.asp",
            "Community-submitted HammerDB results",
            "Unaudited",
            "Not official TPC benchmark results",
        ],
        "rows": rows,
    }
    LEADERBOARD_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def _card(row: dict) -> str:
    report = f"report.html?artifact={quote(row.get('source_path',''), safe='')}"
    if row.get("benchmark") == "TPROC-C":
        main_a, main_b = f"NOPM {row.get('nopm','—')}", f"TPM {row.get('tpm','—')}"
    else:
        main_a, main_b = f"Geomean {row.get('geomean_seconds','—')}s", f"Total Query {row.get('total_query_time_seconds','—')}s"
    chips = [
        ("warehouses", row.get("warehouses")), ("virtual_users", row.get("virtual_users")),
        ("rampup_minutes", row.get("rampup_minutes")), ("duration_minutes", row.get("duration_minutes"))]
    chip_html = "".join(f"<span class='chip'>{escape(k)}: {escape(str(v))}</span>" for k,v in chips if v is not None)
    sys = " · ".join([x for x in [row.get("cpu_model"), row.get("cpu_count") and f"CPU {row.get('cpu_count')}", row.get("memory"), row.get("os_name")] if x])
    return f"""<article class='result'>
<div class='top'><span class='rank'>#{escape(str(row.get('rank','')))}</span><h3>{escape(str(row.get('database_display','')))}</h3><span class='badge'>{escape(str(row.get('benchmark','')))}</span></div>
<p class='meta'>Release {escape(str(row.get('release','')))} · HammerDB {escape(str(row.get('hdb_version','')))} · {escape(str(row.get('timestamp','')))}</p>
<div class='metrics'><div><label>Main</label><strong>{escape(main_a)}</strong></div><div><label>Secondary</label><strong>{escape(main_b)}</strong></div></div>
<div class='chips'>{chip_html}</div>
<p class='meta'>{escape(sys or 'System summary unavailable')}</p>
<a class='btn' href='{escape(report)}'>View report</a>
</article>"""

def _write_html(rows:list[dict])->None:
    html=f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>HammerDB Result Artifacts</title><style>
body{{margin:0;background:#f6f8fc;color:#111827;font-family:Inter,Arial,sans-serif}}.wrap{{max-width:1100px;margin:0 auto;padding:24px}}
.hero,.panel,.result{{background:#fff;border:1px solid #e1e7f5;border-radius:16px;box-shadow:0 4px 16px rgba(17,24,39,.05)}}
.hero{{padding:20px}}.badgeP{{display:inline-block;background:#eef2ff;color:#3742a6;padding:4px 10px;border-radius:999px;font-size:.8rem;font-weight:700}}
.subtitle{{color:#4b5563}}.warn{{margin-top:10px;background:#fff7e6;border-left:4px solid #f59e0b;padding:10px;border-radius:8px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0}}@media(max-width:760px){{.grid{{grid-template-columns:1fr}}}}
.panel{{padding:14px}}.btn{{display:inline-block;background:#2563eb;color:#fff;text-decoration:none;padding:9px 12px;border-radius:10px;font-weight:600}}
.list{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}}.result{{padding:14px}}
.top{{display:flex;align-items:center;gap:10px}}.rank{{background:#e0e7ff;color:#1e3a8a;padding:4px 10px;border-radius:999px;font-weight:700}}
.badge{{background:#f1f5f9;padding:4px 8px;border-radius:8px;font-size:.82rem}}.meta{{color:#6b7280;font-size:.92rem}}
.metrics{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}}.metrics div{{background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:8px}}
.metrics label{{display:block;color:#6b7280;font-size:.8rem}}.chips{{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}}.chip{{background:#eef2f7;border:1px solid #dde3ed;border-radius:999px;padding:4px 8px;font-size:.8rem}}
</style></head><body><main class='wrap'>
<section class='hero'><span class='badgeP'>Prototype</span><h1>HammerDB Result Artifacts</h1>
<p class='subtitle'>Community-submitted HammerDB benchmark result artifacts, reviewed through GitHub.</p>
<div class='warn'>These are community-submitted HammerDB results. They are not official TPC benchmark results.</div></section>
<div class='grid'><section class='panel'><h2>Support HammerDB</h2><p>Star the HammerDB project before submitting a result artifact.</p><a class='btn' href='https://github.com/TPC-Council/HammerDB'>Star HammerDB on GitHub</a></section>
<section class='panel'><h2>Submission guidance</h2><p>To submit a result, open the benchmark report in HammerDB and use Share with TPC-OSS.</p></section></div>
<section class='list'>{''.join(_card(r) for r in rows)}</section></main></body></html>"""
    INDEX_HTML.write_text(html, encoding='utf-8')

def main()->int:
    SITE_ROOT.mkdir(parents=True, exist_ok=True)
    rows=_load_rows(); _write_json(rows); _write_html(rows)
    print(f"Generated {LEADERBOARD_JSON.relative_to(REPO_ROOT)} and {INDEX_HTML.relative_to(REPO_ROOT)} with {len(rows)} row(s).")
    return 0
if __name__=='__main__': raise SystemExit(main())
