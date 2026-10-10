"""Rebuild the V1.0-V4.1 B01 input-readiness evidence for the 2026E benchmark.

Run from anywhere:

    python benchmarks/2026E/run_readiness.py

This only proves the required inputs are present and hashable. `READY` means the
inputs are complete, never that the problem has been solved.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.benchmark.benchmark_runner import run_readiness_check  # noqa: E402

BENCHMARK_ID = "CUMCM-2026E"
BENCHMARK_DIR = Path(__file__).resolve().parent
INPUTS = BENCHMARK_DIR / "inputs"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# 2026E declares 附件1 (投放数据) and 附件2 (result2/3/4 结果模板). The problem
# statement lists exactly three template files for E, so there is no result1.
ATTACHMENTS = [
    {"attachment_id": "problem_statement", "path": INPUTS / "E题.pdf", "media_type": "application/pdf"},
    {"attachment_id": "attachment_1", "path": INPUTS / "附件1.xlsx", "media_type": XLSX},
    {"attachment_id": "attachment_2_result2", "path": INPUTS / "附件2" / "result2.xlsx", "media_type": XLSX},
    {"attachment_id": "attachment_2_result3", "path": INPUTS / "附件2" / "result3.xlsx", "media_type": XLSX},
    {"attachment_id": "attachment_2_result4", "path": INPUTS / "附件2" / "result4.xlsx", "media_type": XLSX},
]


def main() -> int:
    result = run_readiness_check(BENCHMARK_DIR, BENCHMARK_ID, ATTACHMENTS)
    print(f"{BENCHMARK_ID}: {result['status']} (gate={result['gate_decision']})")
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
