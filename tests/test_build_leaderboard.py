from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import build_leaderboard  # noqa: E402


class TprocHSectionTests(unittest.TestCase):
    def test_groups_tproc_h_rows_by_known_scale_factor_order(self) -> None:
        rows = [
            {"rank": 1, "benchmark": "TPROC-H", "database_display": "DB", "scale_factor": 100, "geomean_seconds": 1, "source_path": "results/a.json"},
            {"rank": 2, "benchmark": "TPROC-H", "database_display": "DB", "scale_factor": 1, "geomean_seconds": 2, "source_path": "results/b.json"},
        ]

        html = build_leaderboard._tproc_h_section_html(rows)

        self.assertLess(html.index("SF1"), html.index("SF100"))
        self.assertNotIn("SF10</h3>", html)

    def test_groups_missing_tproc_h_scale_factor_as_unknown(self) -> None:
        rows = [
            {"rank": 1, "benchmark": "TPROC-H", "database_display": "DB", "scale_factor": None, "geomean_seconds": 1, "source_path": "results/a.json"},
        ]

        html = build_leaderboard._tproc_h_section_html(rows)

        self.assertIn("SF unknown", html)


if __name__ == "__main__":
    unittest.main()
