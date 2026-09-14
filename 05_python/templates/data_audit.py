"""Generic large-tabular-data audit template for CUMCM D/E Skill.

Purpose
-------
Profile a large CSV/TSV/XLSX dataset without solving the underlying contest
problem. The output is a compact machine-readable data profile that can be
used to decide which modeling modules are appropriate.

Supported inputs
----------------
- CSV/TSV: chunked pandas.read_csv
- XLSX: openpyxl read_only mode, row streaming

The template deliberately does not infer business meaning. Field semantics
should be supplied through a separate problem configuration after inspection.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

SEED = 2026
DEFAULT_CHUNK_SIZE = 100_000


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(block_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def safe_json_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return str(value)


def profile_chunked_text(path: Path, sep: str, chunk_size: int) -> dict:
    total_rows = 0
    columns = None
    dtypes = None
    missing = Counter()
    unique_samples = {}
    min_values = {}
    max_values = {}
    numeric_sum = Counter()
    numeric_count = Counter()

    for chunk in pd.read_csv(path, sep=sep, chunksize=chunk_size, low_memory=False):
        if columns is None:
            columns = list(chunk.columns)
            dtypes = {c: str(chunk[c].dtype) for c in columns}
            unique_samples = {c: set() for c in columns}

        total_rows += len(chunk)
        for c in columns:
            s = chunk[c]
            missing[c] += int(s.isna().sum())

            # Keep only a bounded distinct sample for audit reporting.
            if len(unique_samples[c]) < 50:
                for v in s.dropna().astype(str).head(1000):
                    unique_samples[c].add(v)
                    if len(unique_samples[c]) >= 50:
                        break

            if pd.api.types.is_numeric_dtype(s):
                vals = pd.to_numeric(s, errors="coerce").dropna()
                if not vals.empty:
                    min_values[c] = min(min_values.get(c, math.inf), float(vals.min()))
                    max_values[c] = max(max_values.get(c, -math.inf), float(vals.max()))
                    numeric_sum[c] += float(vals.sum())
                    numeric_count[c] += int(vals.count())

    columns = columns or []
    return {
        "rows": total_rows,
        "columns": columns,
        "column_count": len(columns),
        "dtypes": dtypes or {},
        "missing": dict(missing),
        "missing_rate": {
            c: (missing[c] / total_rows if total_rows else None) for c in columns
        },
        "distinct_value_sample": {
            c: sorted(values)[:50] for c, values in unique_samples.items()
        },
        "numeric_min": min_values,
        "numeric_max": max_values,
        "numeric_mean": {
            c: numeric_sum[c] / numeric_count[c]
            for c in numeric_count
            if numeric_count[c]
        },
    }


def profile_xlsx(path: Path, sheet_name: str | None) -> dict:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("XLSX audit requires openpyxl") from exc

    wb = load_workbook(path, read_only=True, data_only=True)
    sheets = wb.sheetnames
    selected = sheet_name or sheets[0]
    if selected not in sheets:
        raise ValueError(f"Unknown sheet: {selected}; available={sheets}")

    ws = wb[selected]
    rows = ws.iter_rows(values_only=True)
    header = next(rows, None)
    if header is None:
        return {"rows": 0, "columns": [], "column_count": 0, "sheets": sheets}

    columns = [str(x) if x is not None else f"Unnamed_{i}" for i, x in enumerate(header)]
    total_rows = 0
    missing = Counter()
    unique_samples = {c: set() for c in columns}
    numeric_min, numeric_max = {}, {}
    numeric_sum, numeric_count = Counter(), Counter()

    for row in rows:
        total_rows += 1
        for i, c in enumerate(columns):
            v = row[i] if i < len(row) else None
            if v is None or (isinstance(v, float) and math.isnan(v)):
                missing[c] += 1
                continue
            if len(unique_samples[c]) < 50:
                unique_samples[c].add(str(v))
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                numeric_min[c] = min(numeric_min.get(c, math.inf), float(v))
                numeric_max[c] = max(numeric_max.get(c, -math.inf), float(v))
                numeric_sum[c] += float(v)
                numeric_count[c] += 1

    wb.close()
    return {
        "rows": total_rows,
        "columns": columns,
        "column_count": len(columns),
        "sheets": sheets,
        "selected_sheet": selected,
        "missing": dict(missing),
        "missing_rate": {
            c: (missing[c] / total_rows if total_rows else None) for c in columns
        },
        "distinct_value_sample": {
            c: sorted(values)[:50] for c, values in unique_samples.items()
        },
        "numeric_min": numeric_min,
        "numeric_max": numeric_max,
        "numeric_mean": {
            c: numeric_sum[c] / numeric_count[c]
            for c in numeric_count
            if numeric_count[c]
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a large CSV/TSV/XLSX dataset")
    parser.add_argument("--input", required=True, help="Input data file")
    parser.add_argument("--output", default="results/data_profile.json")
    parser.add_argument("--sep", default=None, help="CSV delimiter; auto-detect if omitted")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--sheet", default=None, help="XLSX sheet name")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        raise FileNotFoundError(path)

    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        profile = profile_xlsx(path, args.sheet)
    elif suffix in {".csv", ".tsv", ".txt"}:
        sep = args.sep
        if sep is None:
            sep = "\t" if suffix == ".tsv" else ","
        profile = profile_chunked_text(path, sep, args.chunk_size)
    else:
        raise ValueError("Supported formats: CSV, TSV, XLSX, XLSM")

    result = {
        "run_id": datetime.now().strftime("%Y%m%dT%H%M%S"),
        "problem": "generic-data-audit",
        "question": "pre-model data audit",
        "model": "schema-and-quality-profile",
        "status": "RUN_COMPLETE",
        "input": {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        },
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "seed": SEED,
        },
        "profile": profile,
        "notes": [
            "This profile is descriptive only; it does not infer business semantics.",
            "Do not use sample distinct values as evidence of complete category coverage.",
            "For modeling, define field semantics and leakage rules in a problem configuration.",
        ],
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "rows": profile.get("rows"), "columns": profile.get("columns")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
