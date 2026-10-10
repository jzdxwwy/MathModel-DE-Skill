"""Entropy-weight + TOPSIS evaluation template for D/E comprehensive-evaluation tasks.

Deterministic and data-driven: it reads a real table, aggregates the referenced
columns per entity, builds the declared indicators (a raw column or a ratio of
two columns), derives objective weights with the entropy-weight method and ranks
the entities with TOPSIS.

Design constraints, matching the project's rules:

* No hard-coded objective and no synthetic input. Every number comes from
  DATA_PATH plus the declared indicator definitions.
* Ratios are built from **aggregated** columns, not averaged per-row ratios:
  CTR is sum(clicks)/sum(views), not mean(daily CTR). Averaging per-row ratios
  silently reweights days with tiny denominators.
* Direction is explicit per indicator ("+" larger-is-better, "-" smaller-is-
  better); nothing is inferred from the column name.
* Zero-variance indicators carry no information, get weight 0 and are reported.
* If no indicator carries information the template fails instead of ranking noise.

What this is NOT: it does not interpret the problem, choose the indicators, or
argue that the ranking answers a contest question. Indicator selection is the
caller's explicit decision and is recorded in the manifest.

Typical sizing: 3-50 entities, 2-15 indicators.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

DATA_PATH = Path("data/input.csv")
ENTITY_COL = "entity"
INDICATORS: list[dict] = []
AGGREGATE = "mean"
SEED = 20260913

EPS = 1e-12


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _referenced_columns(indicators: list[dict]) -> list[str]:
    columns: list[str] = []
    for spec in indicators:
        ratio = spec.get("ratio")
        columns.extend(ratio if ratio else [spec["name"]])
    return list(dict.fromkeys(str(c) for c in columns))


def _indicator_from_table(table: pd.DataFrame, spec: dict) -> pd.Series:
    ratio = spec.get("ratio")
    if not ratio:
        return table[str(spec["name"])].astype(float)
    numerator, denominator = str(ratio[0]), str(ratio[1])
    return table[numerator].astype(float) / table[denominator].astype(float).replace(0, np.nan)


def _entropy_weights(matrix: np.ndarray) -> tuple[np.ndarray, list[float]]:
    """Entropy weights over an already direction-corrected, non-negative matrix."""
    m, _ = matrix.shape
    if m < 2:
        raise ValueError("entropy weighting needs at least two entities")
    # Shift clear of zero so log() is defined; min-max normalisation already puts
    # every column in [0, 1], so the shift does not distort the comparison.
    shifted = matrix + EPS
    proportions = shifted / shifted.sum(axis=0)
    k = 1.0 / np.log(m)
    entropies = -k * (proportions * np.log(proportions)).sum(axis=0)
    divergence = 1.0 - entropies
    divergence[divergence < EPS] = 0.0
    total = divergence.sum()
    if total <= EPS:
        raise ValueError("every indicator has zero variance, so no objective weight can be derived")
    return divergence / total, entropies.tolist()


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    if ENTITY_COL not in df.columns:
        raise ValueError(f"entity column not found: {ENTITY_COL!r}; available columns: {list(df.columns)}")
    if not INDICATORS:
        raise ValueError("INDICATORS is empty; the caller must declare the evaluation indicators")

    names, directions = [], []
    for spec in INDICATORS:
        name = str(spec.get("name"))
        direction = str(spec.get("direction", "+"))
        if direction not in {"+", "-"}:
            raise ValueError(f"indicator {name!r}: direction must be '+' or '-'")
        ratio = spec.get("ratio")
        if ratio and (not isinstance(ratio, (list, tuple)) or len(ratio) != 2):
            raise ValueError(f"indicator {name!r}: ratio must be [numerator, denominator]")
        names.append(name)
        directions.append(direction)

    referenced = _referenced_columns(INDICATORS)
    missing = [c for c in referenced if c not in df.columns]
    if missing:
        raise ValueError(f"columns not found: {missing}; available columns: {list(df.columns)}")

    if AGGREGATE not in {"mean", "sum", "last"}:
        raise ValueError(f"unknown AGGREGATE: {AGGREGATE!r}")

    frame = pd.DataFrame({c: pd.to_numeric(df[c], errors="coerce") for c in referenced})
    frame[ENTITY_COL] = df[ENTITY_COL].astype(str).values
    table = frame.groupby(ENTITY_COL, sort=True)[referenced].agg(AGGREGATE)

    indicator_values = {}
    for spec, name in zip(INDICATORS, names):
        indicator_values[name] = _indicator_from_table(table, spec)

    table = pd.DataFrame(indicator_values, index=table.index)
    raw = table.to_numpy(dtype=float)
    non_finite = [names[j] for j in range(raw.shape[1]) if not np.isfinite(raw[:, j]).all()]
    if non_finite:
        raise ValueError(
            f"indicator(s) are missing or non-numeric after aggregation: {non_finite}; "
            f"check zero denominators and empty groups"
        )

    # Direction-correct with min-max so that "larger is better" holds everywhere.
    corrected = np.zeros_like(raw)
    zero_variance: list[str] = []
    for j in range(raw.shape[1]):
        column = raw[:, j]
        low, high = float(column.min()), float(column.max())
        if high - low <= EPS:
            zero_variance.append(names[j])
            corrected[:, j] = 0.0
            continue
        scaled = (column - low) / (high - low)
        corrected[:, j] = scaled if directions[j] == "+" else 1.0 - scaled

    weights, entropies = _entropy_weights(corrected)

    weighted = corrected * weights
    ideal = weighted.max(axis=0)
    anti_ideal = weighted.min(axis=0)
    d_plus = np.sqrt(((weighted - ideal) ** 2).sum(axis=1))
    d_minus = np.sqrt(((weighted - anti_ideal) ** 2).sum(axis=1))
    denominator = d_plus + d_minus
    closeness = np.where(denominator <= EPS, 0.0, d_minus / np.where(denominator <= EPS, 1.0, denominator))

    entities = [str(x) for x in table.index.tolist()]
    ranking = pd.DataFrame({
        ENTITY_COL: entities,
        "closeness": closeness,
        "d_plus": d_plus,
        "d_minus": d_minus,
        "rank": range(1, len(entities) + 1),
    })
    for name in names:
        ranking[name] = table[name].values

    weights_table = pd.DataFrame({
        "indicator": names,
        "direction": directions,
        "entropy": entropies,
        "weight": weights,
    })

    out = Path("results")
    out.mkdir(exist_ok=True)
    ranking_path = out / "entropy_topsis_scores.csv"
    weights_path = out / "entropy_topsis_weights.csv"
    ranking.to_csv(ranking_path, index=False)
    weights_table.to_csv(weights_path, index=False)

    manifest = {
        "run_id": "entropy-topsis",
        "problem": "DE-template",
        "question": "Q1",
        "input_hash": sha256_file(DATA_PATH),
        "python": sys.version,
        "packages": {"numpy": np.__version__, "pandas": pd.__version__},
        "seed": SEED,
        "model": "EntropyWeight-TOPSIS",
        "parameters": {
            "entity_col": ENTITY_COL,
            "aggregate": AGGREGATE,
            "entities": len(entities),
            "indicator_source_columns": referenced,
            "indicators": [
                {"name": n, "direction": d, "ratio": spec.get("ratio")}
                for n, d, spec in zip(names, directions, INDICATORS)
            ],
            "weights": {n: float(w) for n, w in zip(names, weights)},
            "zero_variance_indicators": zero_variance,
        },
        "command": "python 05_python/templates/entropy_topsis.py",
        "outputs": [str(ranking_path), str(weights_path), str(out / "entropy_topsis_manifest.json")],
        "status": "RUN_COMPLETE",
        "notes": json.dumps({
            "method": "entropy weight + TOPSIS",
            "entropy_constant_k": 1.0 / float(np.log(len(entities))),
            "ratio_built_from_aggregated_columns": True,
            "zero_variance_indicators": zero_variance,
            "top_entity": ranking.iloc[0][ENTITY_COL],
            "top_closeness": float(ranking.iloc[0]["closeness"]),
            "indicator_selection_is_a_caller_decision": True,
        }, ensure_ascii=False),
    }
    (out / "entropy_topsis_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(weights_table.to_string(index=False))
    print()
    print(ranking[[ENTITY_COL, "closeness", "rank"]].to_string(index=False))


if __name__ == "__main__":
    main()
