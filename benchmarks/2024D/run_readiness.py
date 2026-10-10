"""Rebuild the V1.0-V4.1 B01 input-readiness evidence for the 2024D benchmark.

Run from anywhere:  python benchmarks/2024D/run_readiness.py

2024D is a pure analytical problem: the statement asks for depth-charge hit
probabilities and contains no 附件 at all, so the problem statement is the only
required input. `READY` means the inputs are complete, never that the problem has
been solved.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.benchmark.benchmark_runner import run_readiness_check  # noqa: E402

BENCHMARK_ID = "CUMCM-2024D"
BENCHMARK_DIR = Path(__file__).resolve().parent
INPUTS = BENCHMARK_DIR / "inputs"

# No 附件: the statement text was checked for the word 附件 and contains none.
ATTACHMENTS = [
    {"attachment_id": "problem_statement", "path": INPUTS / "D题.pdf", "media_type": "application/pdf"},
]


def main() -> int:
    result = run_readiness_check(BENCHMARK_DIR, BENCHMARK_ID, ATTACHMENTS)
    print(f"{BENCHMARK_ID}: {result['status']} (gate={result['gate_decision']})")
    for stage in result["stages"]:
        print(f"  {stage['stage_id']}: {stage['status']} - {stage['message']}")
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
