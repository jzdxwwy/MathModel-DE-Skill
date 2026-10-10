"""Cost-benefit quadrant classifier for D/E "segment the items" tasks.

Deterministic and data-driven. It builds a cost score and a benefit score for each
item (an item being one row, or one group of rows), labels the items that carry no
cost at all as a separate class, and splits the remainder into four quadrants by a
configurable quantile of each score.

Design constraints, matching the project's rules:

* Both scores are declared by the caller: which columns, which direction, which
  relative weights. Nothing is inferred from a column name.
* **`direction` means "a larger raw value raises this score"** — nothing else.
  For a cost indicator that means a larger raw value means *more cost*
  (`消费额` is `"+"`), NOT "better". This differs from the evaluation template,
  where `-` marks a smaller-is-better column; passing `-` for `消费额` here would
  silently invert every cost quadrant.
* The "no cost / no benefit" class is decided on **raw column values**, not on the
  normalised score: min-max normalisation always pushes the cheapest item to 0, so
  a threshold on the score would label exactly one item instead of the real group.
* Direction, weights, thresholds, quantile and the resulting label counts all go
  into the manifest so every class assignment can be traced back.
* Missing values in a score indicator are a hard error, reported with the count, so
  a sparse column cannot silently turn into "median benefit".

What this is NOT: it does not decide which fields measure "cost" or "benefit".
That is a modelling decision the caller must make and defend in the paper.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

DATA_PATH = Path("data/input.csv")
ITEM_COLS: list[str] = []
COST_INDICATORS: list[dict] = []
BENEFIT_INDICATORS: list[dict] = []
COST_WEIGHTS: dict = {}
BENEFIT_WEIGHTS: dict = {}
ZERO_COST_COLUMN = None
ZERO_COST_VALUE = 0.0
ZERO_BENEFIT_COLUMN = None
ZERO_BENEFIT_VALUE = 0.0
SPLIT_QUANTILE = 0.5
AGGREGATE = "sum"
LABELS = {
    "low_cost_high_benefit": "low_cost_high_benefit",
    "high_cost_high_benefit": "high_cost_high_benefit",
    "low_cost_low_benefit": "low_cost_low_benefit",
    "high_cost_low_benefit": "high_cost_low_benefit",
    "no_cost_no_benefit": "no_cost_no_benefit",
}
SEED = 20260913

EPS = 1e-12


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _referenced(indicators: list[dict]) -> list[str]:
    columns: list[str] = []
    for spec in indicators:
        ratio = spec.get("ratio")
        columns.extend(ratio if ratio else [spec["name"]])
    return list(dict.fromkeys(str(c) for c in columns))


def _indicator(table: pd.DataFrame, spec: dict) -> pd.Series:
    ratio = spec.get("ratio")
    if not ratio:
        return table[str(spec["name"])].astype(float)
    numerator, denominator = str(ratio[0]), str(ratio[1])
    return table[numerator].astype(float) / table[denominator].astype(float).replace(0, np.nan)


def _weights(names: list[str], declared: dict) -> np.ndarray:
    if not declared:
        return np.full(len(names), 1.0 / len(names))
    values = np.array([float(declared.get(name, 0.0)) for name in names], dtype=float)
    total = values.sum()
    if total <= EPS:
        raise ValueError("declared weights sum to zero")
    return values / total


def _score(table: pd.DataFrame, indicators: list[dict], declared_weights: dict, label: str) -> tuple[pd.Series, dict]:
    names, directions, normalised = [], [], []
    for spec in indicators:
        name = str(spec.get("name"))
        direction = str(spec.get("direction", "+"))
        if direction not in {"+", "-"}:
            raise ValueError(f"{label} indicator {name!r}: direction must be '+' or '-'")
        names.append(name)
        directions.append(direction)
        normalised.append(_indicator(table, spec))
    if not names:
        raise ValueError(f"{label} indicators are empty")

    frame = pd.DataFrame(dict(zip(names, normalised)), index=table.index)
    missing = {name: int(frame[name].isna().sum()) for name in names if frame[name].isna().any()}
    if missing:
        raise ValueError(
            f"{label} indicator(s) have missing or non-numeric values {missing}; "
            f"a sparse column must not silently become a median"
        )

    weights = _weights(names, declared_weights)
    scaled = pd.DataFrame(index=frame.index)
    for name, direction in zip(names, directions):
        column = frame[name].astype(float)
        low, high = float(column.min()), float(column.max())
        if high - low <= EPS:
            scaled[name] = 0.0
            continue
        value = (column - low) / (high - low)
        scaled[name] = value if direction == "+" else 1.0 - value
    score = (scaled.to_numpy() * weights).sum(axis=1)
    detail = {
        "indicators": [{"name": n, "direction": d} for n, d in zip(names, directions)],
        "weights": {n: float(w) for n, w in zip(names, weights)},
        "raw_min": {n: float(frame[n].min()) for n in names},
        "raw_max": {n: float(frame[n].max()) for n in names},
    }
    return pd.Series(score, index=frame.index), detail


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    if not ITEM_COLS:
        raise ValueError("ITEM_COLS is empty; the caller must declare the item identity columns")
    absent = [c for c in ITEM_COLS if c not in df.columns]
    if absent:
        raise ValueError(f"item column(s) not found: {absent}; available columns: {list(df.columns)}")
    if ZERO_COST_COLUMN and ZERO_COST_COLUMN not in df.columns:
        raise ValueError(f"zero-cost column not found: {ZERO_COST_COLUMN!r}")

    needed = list(dict.fromkeys(
        _referenced(COST_INDICATORS) + _referenced(BENEFIT_INDICATORS)
        + ([ZERO_COST_COLUMN] if ZERO_COST_COLUMN else [])
        + ([ZERO_BENEFIT_COLUMN] if ZERO_BENEFIT_COLUMN else [])
    ))
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"columns not found: {missing}; available columns: {list(df.columns)}")

    if AGGREGATE not in {"mean", "sum", "last"}:
        raise ValueError(f"unknown AGGREGATE: {AGGREGATE!r}")

    numeric = pd.DataFrame({c: pd.to_numeric(df[c], errors="coerce") for c in needed})
    for column in ITEM_COLS:
        numeric[column] = df[column].astype(str).values
    table = numeric.groupby(ITEM_COLS, sort=True)[needed].agg(AGGREGATE)

    # Decide the no-cost class on raw values FIRST. Rows without cost also
    # legitimately lack benefit fields (890 of the 2227 rows in the real 2026E
    # Sheet3 have an empty 跳出率), and their normalised scores would be
    # meaningless. Scores are therefore built only over the rows being compared,
    # which is also the correct population for min-max normalisation.
    zero_mask = pd.Series(True, index=table.index)
    rule = []
    if ZERO_COST_COLUMN:
        zero_mask &= table[ZERO_COST_COLUMN].astype(float) <= float(ZERO_COST_VALUE)
        rule.append(f"{ZERO_COST_COLUMN} <= {ZERO_COST_VALUE} (无成本)")
    if ZERO_BENEFIT_COLUMN:
        zero_mask &= table[ZERO_BENEFIT_COLUMN].astype(float) <= float(ZERO_BENEFIT_VALUE)
        rule.append(f"{ZERO_BENEFIT_COLUMN} <= {ZERO_BENEFIT_VALUE} (无效益)")
    if not rule:
        raise ValueError("declare ZERO_COST_COLUMN (and optionally ZERO_BENEFIT_COLUMN) to define the no-cost class")

    rest = ~zero_mask
    if int(rest.sum()) < 2:
        raise ValueError("fewer than two items remain after the no-cost class; cannot split quadrants")

    compared = table[rest]
    cost_score, cost_detail = _score(compared, COST_INDICATORS, COST_WEIGHTS, "cost")
    benefit_score, benefit_detail = _score(compared, BENEFIT_INDICATORS, BENEFIT_WEIGHTS, "benefit")
    cost_score = cost_score.reindex(table.index)
    benefit_score = benefit_score.reindex(table.index)

    cost_cut = float(cost_score[rest].quantile(float(SPLIT_QUANTILE)))
    benefit_cut = float(benefit_score[rest].quantile(float(SPLIT_QUANTILE)))

    classes = pd.Series(LABELS["no_cost_no_benefit"], index=table.index, dtype=object)
    high_cost = rest & (cost_score >= cost_cut)
    low_cost = rest & (cost_score < cost_cut)
    high_benefit = benefit_score >= benefit_cut
    classes[low_cost & high_benefit] = LABELS["low_cost_high_benefit"]
    classes[high_cost & high_benefit] = LABELS["high_cost_high_benefit"]
    classes[low_cost & ~high_benefit] = LABELS["low_cost_low_benefit"]
    classes[high_cost & ~high_benefit] = LABELS["high_cost_low_benefit"]

    result = table.reset_index()
    result["cost_score"] = cost_score.values
    result["benefit_score"] = benefit_score.values
    result["class"] = classes.values

    out = Path("results")
    out.mkdir(exist_ok=True)
    result_path = out / "cost_benefit_classes.csv"
    result.to_csv(result_path, index=False)

    counts = {str(k): int(v) for k, v in classes.value_counts().items()}
    anomalies: list[str] = []
    if ZERO_COST_COLUMN and ZERO_BENEFIT_COLUMN:
        free = table[ZERO_COST_COLUMN].astype(float) <= float(ZERO_COST_VALUE)
        productive = table[ZERO_BENEFIT_COLUMN].astype(float) > float(ZERO_BENEFIT_VALUE)
        n = int((free & productive).sum())
        if n:
            anomalies.append(
                f"{n} item(s) have no cost but a positive {ZERO_BENEFIT_COLUMN}; "
                f"they are excluded from the no-cost class by the two-condition rule"
            )

    manifest = {
        "run_id": "cost-benefit-quadrant",
        "problem": "DE-template",
        "question": "Q2",
        "input_hash": sha256_file(DATA_PATH),
        "python": sys.version,
        "packages": {"numpy": np.__version__, "pandas": pd.__version__},
        "seed": SEED,
        "model": "CostBenefit-Quadrant",
        "parameters": {
            "item_cols": ITEM_COLS,
            "aggregate": AGGREGATE,
            "items": int(len(result)),
            "split_quantile": float(SPLIT_QUANTILE),
            "cost_cut": cost_cut,
            "benefit_cut": benefit_cut,
            "no_cost_rule": rule,
            "cost": cost_detail,
            "benefit": benefit_detail,
            "class_counts": counts,
        },
        "command": "python 05_python/templates/cost_benefit_classifier.py",
        "outputs": [str(result_path), str(out / "cost_benefit_manifest.json")],
        "status": "RUN_COMPLETE",
        "notes": json.dumps({
            "method": "direction-corrected min-max composite scores + quantile quadrants",
            "no_cost_class_is_decided_on_raw_values": True,
            "scores_are_undefined_for_the_no_cost_class": True,
            "class_counts": counts,
            "anomalies": anomalies,
            "indicator_selection_is_a_caller_decision": True,
        }, ensure_ascii=False),
    }
    (out / "cost_benefit_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(counts, ensure_ascii=False, indent=2))
    for item in anomalies:
        print("ANOMALY:", item)


if __name__ == "__main__":
    main()
