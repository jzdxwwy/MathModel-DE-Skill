"""One-factor-at-a-time sensitivity template.
Replace objective() with the contest model objective."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

BASE = {"x1": 1.0, "x2": 1.0, "x3": 1.0}
GRID = np.linspace(0.8, 1.2, 9)


def objective(params):
    # Toy objective; replace with the real model.
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
    result.to_csv(out / "sensitivity.csv", index=False)
    manifest = {"template":"sensitivity", "baseline_objective":base_value, "ranking":summary.to_dict(), "status":"RUN_COMPLETE"}
    (out / "sensitivity_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
