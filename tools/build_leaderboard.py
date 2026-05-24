#!/usr/bin/env python3
"""Build leaderboard JSON + static HTML from HammerDB result artifacts."""

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
    rows: list[dict] = []
    for file_path in sorted(RESULTS_ROOT.rglob("*.json")):
        rel_path = file_path.relative_to(REPO_ROOT).as_posix()
        payload = json.loads(file_path.read_text(encoding="utf-8"))

        job = payload.get("job", {})
        cfg = payload.get("benchmark_config", {})
        result = payload.get("result", {})
        system = payload.get("system", {})

        row = {
            "jobid": job.get("jobid"),
            "benchmark": job.get("benchmark"),
            "database": job.get("database"),
            "database_display": job.get("database_display"),
            "release": job.get("release"),
            "timestamp": job.get("timestamp"),
            "hdb_version": job.get("hdb_version"),
            "nopm": result.get("nopm"),
            "tpm": result.get("tpm"),
            "geomean_seconds": result.get("geomean_seconds"),
            "total_query_time_seconds": result.get("total_query_time_seconds"),
            "warehouses": cfg.get("warehouses"),
            "virtual_users": cfg.get("virtual_users"),
            "rampup_minutes": cfg.get("rampup_minutes"),
            "duration_minutes": cfg.get("duration_minutes"),
            "cpu_model": system.get("cpumodel"),
            "cpu_count": system.get("cpucount"),
            "memory": system.get("memory"),
            "system_type": system.get("system_type"),
            "os_name": system.get("os_name"),
            "storage": system.get("storage"),
            "source_path": rel_path,
        }
        rows.append(row)

    rows.sort(key=lambda r: (r.get("nopm") is None, -(r.get("nopm") or 0), r.get("jobid") or ""))
    for idx, row in enumerate(rows, start=1):
        row["rank"] = idx
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


def _metric_summary(row: dict) -> str:
    if row.get("benchmark") == "TPROC-C":
        return f"NOPM {row.get('nopm', '—')} · TPM {row.get('tpm', '—')}"
    return f"Geomean(s) {row.get('geomean_seconds', '—')} · Total Query(s) {row.get('total_query_time_seconds', '—')}"


def _write_html(rows: list[dict]) -> None:
    cards = []
    for row in rows:
        report_href = f"report.html?artifact={quote(row.get('source_path', ''), safe='')}"
        config_bits = []
        if row.get("warehouses") is not None:
            config_bits.append(f"Warehouses: {row['warehouses']}")
        if row.get("virtual_users") is not None:
            config_bits.append(f"Virtual users: {row['virtual_users']}")
        config_text = " · ".join(config_bits) if config_bits else "Benchmark configuration in report"
        cards.append(
            f"""
      <article class="result-card">
        <div class="row-top"><span class="rank">#{escape(str(row.get('rank', '')))}</span><span class="db">{escape(str(row.get('database_display', '')))}</span></div>
        <div class="meta">{escape(str(row.get('release', '')))} · {escape(str(row.get('benchmark', '')))} · {escape(str(row.get('hdb_version', '')))}</div>
        <div class="meta">{escape(str(row.get('timestamp', '')))}</div>
        <div class="headline">{escape(_metric_summary(row))}</div>
        <div class="meta">{escape(config_text)}</div>
        <a class="btn" href="{escape(report_href)}">View report</a>
      </article>
            """.rstrip()
        )

    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>HammerDB Result Artifacts Prototype</title>
  <style>
    :root {{ --bg:#0b1020; --surface:#131a2e; --text:#e9eefb; --muted:#a9b5d6; --accent:#7aa2ff; --warn:#ffd98a; --ok:#9ce0aa; }}
    body {{ margin:0; font-family:Inter,Arial,sans-serif; background:#f4f7ff; color:#10162a; }}
    .wrap {{ max-width: 1024px; margin: 0 auto; padding: 24px; }}
    .hero {{ background:linear-gradient(140deg,var(--bg),#1c2a52); color:var(--text); border-radius:16px; padding:24px; }}
    .hero h1 {{ margin:0 0 10px; font-size:1.9rem; }}
    .hero p {{ margin:6px 0; color:var(--muted); }}
    .notice,.cta,.disclaimer {{ margin-top:16px; border-radius:12px; padding:14px 16px; background:#fff; border:1px solid #d8e0f4; }}
    .notice {{ border-left:5px solid #f0b429; }}
    .cta {{ border-left:5px solid #4a90e2; }}
    .disclaimer {{ border-left:5px solid #8f9bb3; }}
    .grid {{ margin-top:18px; display:grid; gap:14px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }}
    .result-card {{ background:#fff; border:1px solid #d8e0f4; border-radius:14px; padding:14px; box-shadow:0 2px 10px rgba(9,30,66,.06); }}
    .row-top {{ display:flex; justify-content:space-between; align-items:center; }}
    .rank {{ background:#eef3ff; color:#2b4ca7; font-weight:700; border-radius:999px; padding:4px 10px; }}
    .db {{ font-weight:700; font-size:1.08rem; }}
    .meta {{ color:#4a5678; margin-top:6px; font-size:.95rem; }}
    .headline {{ margin-top:10px; font-weight:700; }}
    .btn {{ display:inline-block; margin-top:12px; background:var(--accent); color:white; text-decoration:none; padding:8px 12px; border-radius:8px; }}
  </style>
</head>
<body>
  <main class=\"wrap\">
    <section class=\"hero\">
      <h1>HammerDB Result Artifacts Prototype</h1>
      <p>Modern prototype leaderboard generated from GitHub-reviewed HammerDB summaryjson artifacts.</p>
      <p>Intended live publication path: TPC-Council/hammerdb-results.</p>
    </section>

    <section class=\"notice\">
      <strong>Prototype only.</strong> Intended live publication path: TPC-Council/hammerdb-results, linked from the TPC HammerDB Artifact Results page.
    </section>

    <section class=\"cta\">
      <strong>First, star the HammerDB project on GitHub:</strong>
      <a href=\"https://github.com/TPC-Council/HammerDB\">https://github.com/TPC-Council/HammerDB</a>
      <p>To submit a result, open the benchmark report in HammerDB and use Share with TPC-OSS.</p>
    </section>

    <section class=\"disclaimer\">
      <div>Community-submitted HammerDB results</div>
      <div>Unaudited</div>
      <div>Not official TPC benchmark results</div>
    </section>

    <section class=\"grid\">{''.join(cards)}</section>
  </main>
</body>
</html>
"""
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
