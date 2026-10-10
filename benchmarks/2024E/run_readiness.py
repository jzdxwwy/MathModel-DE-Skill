"""Rebuild the V1.0-V4.1 B01 input-readiness evidence for the 2024E benchmark.

Run from anywhere:  python benchmarks/2024E/run_readiness.py

2024E's main dataset is 附件2.csv: 467.9 MB / 8,844,993 rows of crossing records.
It is deliberately NOT committed (see README section 6), so a fresh clone reports
BLOCKED for it. Place the official file at inputs/附件2.csv and compare the SHA256
to convert the benchmark to READY.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.benchmark.benchmark_runner import run_readiness_check  # noqa: E402

BENCHMARK_ID = "CUMCM-2024E"
BENCHMARK_DIR = Path(__file__).resolve().parent
INPUTS = BENCHMARK_DIR / "inputs"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

ATTACHMENTS = [
    {"attachment_id": "problem_statement", "path": INPUTS / "E题.pdf", "media_type": "application/pdf"},
    {"attachment_id": "attachment_1", "path": INPUTS / "附件1.xlsx", "media_type": XLSX},
    {"attachment_id": "attachment_2", "path": INPUTS / "附件2.csv", "media_type": "text/csv"},
    {"attachment_id": "attachment_3", "path": INPUTS / "附件3.pdf", "media_type": "application/pdf"},
    {"attachment_id": "paper_format", "path": INPUTS / "format2024.doc", "media_type": "application/msword"},
]


def main() -> int:
    result = run_readiness_check(BENCHMARK_DIR, BENCHMARK_ID, ATTACHMENTS)
    print(f"{BENCHMARK_ID}: {result['status']} (gate={result['gate_decision']})")
    for stage in result["stages"]:
        print(f"  {stage['stage_id']}: {stage['status']} - {stage['message']}")
        if stage["status"] == "BLOCKED":
            print(f"    missing: {stage['input_refs']}")
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
