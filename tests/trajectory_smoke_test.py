"""Smoke test for the generic trajectory reconstruction template.

Uses only synthetic data. It checks ordering, transition construction,
duplicate timestamps, large-gap flags, and manifest creation.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "05_python" / "templates" / "trajectory_reconstruction.py"
TMP = ROOT / "tests" / "_tmp_trajectory"


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    input_path = TMP / "input.csv"
    output_dir = TMP / "results"

    df = pd.DataFrame({
        "entity": ["A", "A", "A", "B", "B"],
        "time": [
            "2024-01-01T10:00:00",
            "2024-01-01T10:20:00",
            "2024-01-01T10:20:00",
            "2024-01-01T09:00:00",
            "2024-01-01T10:00:00",
        ],
        "node": ["N1", "N2", "N2", "N3", "N4"],
    })
    # Intentionally shuffle to verify entity-time sorting.
    df.sample(frac=1, random_state=7).to_csv(input_path, index=False)

    cmd = [
        sys.executable,
        str(TEMPLATE),
        "--input", str(input_path),
        "--output-dir", str(output_dir),
        "--entity-col", "entity",
        "--time-col", "time",
        "--node-col", "node",
        "--max-gap-minutes", "15",
        "--problem", "smoke_test",
        "--question", "trajectory",
    ]
    subprocess.run(cmd, check=True, cwd=ROOT)

    events = pd.read_csv(output_dir / "ordered_events.csv")
    transitions = pd.read_csv(output_dir / "transitions.csv")
    manifest = json.loads((output_dir / "trajectory_manifest.json").read_text(encoding="utf-8"))

    assert len(events) == 5
    assert len(transitions) == 3
    assert events.loc[events["entity"] == "A", "_parsed_time"].tolist() == sorted(
        events.loc[events["entity"] == "A", "_parsed_time"].tolist()
    )
    assert transitions["same_node"].any()
    assert transitions["gap_exceeds_limit"].any()
    assert (transitions["transition_confidence"] == "uncertain_gap").any()
    assert manifest["status"] == "RUN_COMPLETE"
    assert manifest["model"] == "ordered_event_trajectory_reconstruction"

    print("trajectory_smoke_test: PASS")


if __name__ == "__main__":
    main()
