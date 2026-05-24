#!/usr/bin/env python3
"""Build leaderboard JSON + static HTML from HammerDB result artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

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

        if job.get("benchmark") != "TPROC-C":
            continue

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


def _write_html(rows: list[dict]) -> None:
    columns = [
        "rank", "jobid", "benchmark", "database", "database_display", "release", "timestamp", "hdb_version",
        "nopm", "tpm", "warehouses", "virtual_users", "rampup_minutes", "duration_minutes",
        "cpu_model", "cpu_count", "memory", "system_type", "os_name", "storage", "source_path"
    ]
    header = "".join(f"<th>{escape(col)}</th>" for col in columns)
    body = []
    for row in rows:
        cells = "".join(f"<td>{escape(str(row.get(col, '')))}</td>" for col in columns)
        body.append(f"<tr>{cells}</tr>")
    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>HammerDB Result Artifacts Prototype</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; line-height: 1.35; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; }}
    th, td {{ border: 1px solid #ccc; padding: 0.35rem; text-align: left; vertical-align: top; }}
    th {{ background: #f3f3f3; position: sticky; top: 0; }}
    .messages p {{ margin: 0.2rem 0; font-weight: bold; }}
    .note {{ background: #fff4cc; border: 1px solid #e5c76b; padding: 0.75rem; margin: 1rem 0; }}
    .cta {{ background: #eef5ff; border: 1px solid #b9d2ff; padding: 0.75rem; margin: 1rem 0; }}
    .scroll {{ overflow-x: auto; }}
  </style>
</head>
<body>
  <h1>HammerDB Result Artifacts Prototype</h1>
  <div class=\"note\">
    <strong>Prototype only.</strong> Intended live publication path: TPC-Council/hammerdb-results, linked from the TPC HammerDB Artifact Results page.
  </div>
  <div class=\"cta\">
    <h2>Submit a HammerDB result artifact</h2>
    <p>First, star the HammerDB project on GitHub: <a href=\"https://github.com/TPC-Council/HammerDB\">https://github.com/TPC-Council/HammerDB</a></p>
    <p><a href=\"submit.html\">Submit a HammerDB result artifact</a></p>
  </div>
  <div class=\"messages\">
    <p>Community-submitted HammerDB results</p>
    <p>Unaudited</p>
    <p>Not official TPC benchmark results</p>
  </div>
  <div class=\"scroll\">
    <table>
      <thead><tr>{header}</tr></thead>
      <tbody>
        {''.join(body)}
      </tbody>
    </table>
  </div>
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
