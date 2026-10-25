"""Rebuild the whole project from cached raw data.

    python src/run_all.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "download_data.py",
    "build_panel.py",
    "analysis.py",
    "comparative.py",
    "figures.py",
    "figures_comparative.py",
]


def main() -> int:
    for step in STEPS:
        print(f"\n=== {step} ===")
        subprocess.run([sys.executable, str(ROOT / "src" / step)], check=True, cwd=ROOT)
    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
