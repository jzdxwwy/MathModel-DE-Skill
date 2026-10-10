"""Rebuild the V1.0-V4.1 B01 input-readiness evidence for the 2026D benchmark.

Run from anywhere:

    python benchmarks/2026D/run_readiness.py

Expected to report BLOCKED until 附件2 (result1-4 结果模板) is obtained. Only the
reference solution's *filled* result files are available locally, and feeding a
reference output back in as an input template would be fabricating the benchmark
input. The exit status is non-zero while the benchmark is not READY.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.benchmark.benchmark_runner import run_readiness_check  # noqa: E402

BENCHMARK_ID = "CUMCM-2026D"
BENCHMARK_DIR = Path(__file__).resolve().parent
INPUTS = BENCHMARK_DIR / "inputs"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# 2026D declares 附件1 and 附件2 (result1-4 结果模板). The four template files are
# declared as required even though they are currently absent, so that readiness
# fails closed instead of quietly reducing the benchmark to its easiest inputs.
ATTACHMENTS = [
    {"attachment_id": "problem_statement", "path": INPUTS / "D题.pdf", "media_type": "application/pdf"},
    {"attachment_id": "attachment_1", "path": INPUTS / "附件1.xlsx", "media_type": XLSX},
    {"attachment_id": "attachment_2_result1", "path": INPUTS / "附件2" / "result1.xlsx", "media_type": XLSX},
    {"attachment_id": "attachment_2_result2", "path": INPUTS / "附件2" / "result2.xlsx", "media_type": XLSX},
    {"attachment_id": "attachment_2_result3", "path": INPUTS / "附件2" / "result3.xlsx", "media_type": XLSX},
    {"attachment_id": "attachment_2_result4", "path": INPUTS / "附件2" / "result4.xlsx", "media_type": XLSX},
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
