"""One-factor-at-a-time sensitivity template."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

BASE = {"x1": 1.0, "x2": 1.0, "x3": 1.0}
GRID = np.linspace(0.8, 1.2, 9)


def objective(params):
    # Toy objective; replace this with the real contest model.
    return 2.0 * params["x1"] + 0.5 * params["x2"] ** 2 - params["x3"]


def main():
    base_value = objective(BASE)
    rows = []
    for name in BASE:
        for value in GRID:
            p = BASE.copy(); p[name] = value
            y = objective(p)
            rows.append({"parameter": name, "value": value, "objective": y, "delta": y - base_value})
    result = pd.DataFrame(rows)
    summary = result.groupby("parameter")["delta"].apply(lambda s: float(s.abs().max())).sort_values(ascending=False)
    out = Path("results"); out.mkdir(exist_ok=True)
    result_path = out / "sensitivity.csv"
    result.to_csv(result_path, index=False)
    manifest = {
        "run_id": "sensitivity-oat",
        "problem": "DE-template",
        "question": "Q1",
        "python": sys.version,
        "model": "OAT-sensitivity",
        "parameters": {"base": BASE, "grid": GRID.tolist()},
        "command": "python 05_python/templates/sensitivity.py",
        "outputs": [str(result_path), str(out / "sensitivity_manifest.json")],
        "status": "RUN_COMPLETE",
        "notes": json.dumps({"baseline_objective": base_value, "ranking": summary.to_dict()}, ensure_ascii=False),
    }
    (out / "sensitivity_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
