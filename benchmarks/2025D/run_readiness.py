"""Rebuild the V1.0-V4.1 B01 input-readiness evidence for the 2025D benchmark.

Run from anywhere:  python benchmarks/2025D/run_readiness.py

2025D ships two mine layouts (附件1, 附件2) and eight result templates
(附件3/result{1..4}-{1,2}.xlsx) covering both layouts. `READY` means the inputs are
complete, never that the problem has been solved.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.benchmark.benchmark_runner import run_readiness_check  # noqa: E402

BENCHMARK_ID = "CUMCM-2025D"
BENCHMARK_DIR = Path(__file__).resolve().parent
INPUTS = BENCHMARK_DIR / "inputs"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

ATTACHMENTS = [
    {"attachment_id": "problem_statement", "path": INPUTS / "D题.pdf", "media_type": "application/pdf"},
    {"attachment_id": "attachment_1", "path": INPUTS / "附件1.xlsx", "media_type": XLSX},
    {"attachment_id": "attachment_2", "path": INPUTS / "附件2.xlsx", "media_type": XLSX},
]
for question in (1, 2, 3, 4):
    for layout in (1, 2):
        name = f"result{question}-{layout}.xlsx"
        ATTACHMENTS.append({
            "attachment_id": f"attachment_3_{name.removesuffix('.xlsx')}",
            "path": INPUTS / "附件3" / name,
            "media_type": XLSX,
        })


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
