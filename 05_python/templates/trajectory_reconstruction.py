"""
Generic event-stream trajectory reconstruction template for D/E modeling.

Purpose
-------
Transform records of the form
    entity_id + timestamp + node/event_location
into ordered trajectories and transition events.

This is intentionally domain-agnostic. Do not hard-code contest-specific
node names, directions, distances, or business rules here.

Typical uses
------------
- vehicle / pedestrian / robot / equipment event logs
- sensor observations on a network
- customer or device movement between locations

Key safeguards
--------------
1. Sort by entity and time before constructing transitions.
2. Keep duplicate timestamps instead of silently dropping records.
3. Expose gaps between observations; do not infer missing transitions.
4. Allow a maximum-gap rule to mark transitions as uncertain.
5. Preserve original row identifiers for traceability.
6. Save a manifest describing the run and input hash.

Example
-------
python trajectory_reconstruction.py \
  --input data/input.csv \
  --output-dir results/trajectory \
  --entity-col entity_id \
  --time-col timestamp \
  --node-col node \
  --max-gap-minutes 30

Input can be CSV/TSV. For very large CSV files, preprocessing should first
use data_audit.py or an equivalent chunked ingestion layer. This template is
kept intentionally simple and transparent so that a problem-specific layer
can add network/path constraints after the basic event transitions are built.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import pandas as pd


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def read_table(path: Path, sep: str | None = None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt", ".tsv"}:
        if sep is None:
            sep = "\t" if suffix == ".tsv" else ","
        return pd.read_csv(path, sep=sep)
    if suffix in {".xlsx", ".xlsm"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported input format: {suffix}")


def reconstruct(
    df: pd.DataFrame,
    entity_col: str,
    time_col: str,
    node_col: str,
    max_gap_minutes: float | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = [entity_col, time_col, node_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    work = df.copy()
    work["_source_row"] = range(len(work))
    work["_parsed_time"] = pd.to_datetime(work[time_col], errors="coerce")
    if work["_parsed_time"].isna().any():
        bad = int(work["_parsed_time"].isna().sum())
        raise ValueError(f"Cannot parse {bad} timestamps in {time_col}")

    work = work.sort_values([entity_col, "_parsed_time", "_source_row"], kind="mergesort").reset_index(drop=True)

    grouped = work.groupby(entity_col, sort=False, dropna=False)
    work["prev_node"] = grouped[node_col].shift(1)
    work["prev_time"] = grouped["_parsed_time"].shift(1)
    work["next_node"] = grouped[node_col].shift(-1)
    work["next_time"] = grouped["_parsed_time"].shift(-1)

    work["prev_gap_seconds"] = (work["_parsed_time"] - work["prev_time"]).dt.total_seconds()
    work["next_gap_seconds"] = (work["next_time"] - work["_parsed_time"]).dt.total_seconds()

    work["is_entity_start"] = work["prev_time"].isna()
    work["is_duplicate_timestamp"] = work["_parsed_time"].eq(work["prev_time"])

    transitions = work.loc[~work["is_entity_start"], [
        entity_col,
        "_source_row",
        "prev_node",
        node_col,
        "prev_time",
        "_parsed_time",
        "prev_gap_seconds",
    ]].copy()
    transitions = transitions.rename(columns={
        "_source_row": "to_source_row",
        "prev_node": "from_node",
        node_col: "to_node",
        "prev_time": "from_time",
        "_parsed_time": "to_time",
        "prev_gap_seconds": "gap_seconds",
    })

    transitions["same_node"] = transitions["from_node"].eq(transitions["to_node"])
    transitions["gap_exceeds_limit"] = False
    if max_gap_minutes is not None:
        limit = float(max_gap_minutes) * 60.0
        transitions["gap_exceeds_limit"] = transitions["gap_seconds"] > limit
        transitions["transition_confidence"] = transitions["gap_exceeds_limit"].map(
            {True: "uncertain_gap", False: "time_consistent"}
        )
    else:
        transitions["transition_confidence"] = "not_assessed"

    # A transition is an observed pair only. No missing node is invented.
    transitions["inferred"] = False

    return work, transitions


def main() -> None:
    parser = argparse.ArgumentParser(description="Generic event-stream trajectory reconstruction")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", default="results/trajectory")
    parser.add_argument("--entity-col", required=True)
    parser.add_argument("--time-col", required=True)
    parser.add_argument("--node-col", required=True)
    parser.add_argument("--max-gap-minutes", type=float, default=None)
    parser.add_argument("--sep", default=None)
    parser.add_argument("--problem", default="generic")
    parser.add_argument("--question", default="trajectory")
    args = parser.parse_args()

    input_path = Path(args.input)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = read_table(input_path, args.sep)
    events, transitions = reconstruct(
        df,
        entity_col=args.entity_col,
        time_col=args.time_col,
        node_col=args.node_col,
        max_gap_minutes=args.max_gap_minutes,
    )

    events_path = out_dir / "ordered_events.csv"
    transitions_path = out_dir / "transitions.csv"
    events.to_csv(events_path, index=False)
    transitions.to_csv(transitions_path, index=False)

    manifest = {
        "run_id": f"trajectory_{pd.Timestamp.now(tz='UTC').strftime('%Y%m%dT%H%M%SZ')}",
        "problem": args.problem,
        "question": args.question,
        "model": "ordered_event_trajectory_reconstruction",
        "status": "RUN_COMPLETE",
        "input": {
            "path": str(input_path),
            "sha256": sha256_file(input_path),
            "rows": int(len(df)),
            "columns": list(df.columns),
        },
        "parameters": {
            "entity_col": args.entity_col,
            "time_col": args.time_col,
            "node_col": args.node_col,
            "max_gap_minutes": args.max_gap_minutes,
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "pandas": pd.__version__,
        },
        "outputs": [str(events_path), str(transitions_path)],
        "notes": [
            "Observed transitions are not treated as proof of an unobserved path.",
            "Gap flags are diagnostic and require problem-specific interpretation.",
            "Network constraints and hidden-state inference belong in a separate layer.",
        ],
    }
    (out_dir / "trajectory_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps({
        "rows": len(df),
        "transitions": len(transitions),
        "events_output": str(events_path),
        "transitions_output": str(transitions_path),
        "manifest": str(out_dir / "trajectory_manifest.json"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
