"""Small nonlinear optimization template for D/E decision problems.

Replace objective() and constraints with the actual engineering objective.
Uses scipy.optimize.minimize with explicit bounds and inequality constraints.
"""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
from scipy.optimize import minimize

SEED = 20260913
BOUNDS = [(0.0, 10.0), (0.0, 10.0)]


def objective(x):
    # Toy objective: replace with the contest objective.
    return (x[0] - 3.0) ** 2 + 2.0 * (x[1] - 5.0) ** 2


def constraint_total(x):
    # Feasibility condition: x0 + x1 <= 10.
    return 10.0 - x[0] - x[1]


def main():
    x0 = np.array([2.0, 4.0])
    result = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=BOUNDS,
        constraints=[{"type": "ineq", "fun": constraint_total}],
        options={"maxiter": 1000, "ftol": 1e-10},
    )
    if not result.success:
        raise RuntimeError(result.message)
    x = result.x
    feasible = all(b[0] - 1e-9 <= xi <= b[1] + 1e-9 for xi, b in zip(x, BOUNDS)) and constraint_total(x) >= -1e-8
    if not feasible:
        raise RuntimeError("Optimizer returned an infeasible solution")
    out = Path("results"); out.mkdir(exist_ok=True)
    payload = {"x": x.tolist(), "objective": float(result.fun), "success": bool(result.success), "message": result.message}
    (out / "optimization_result.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "run_id": "nonlinear-optimization",
        "problem": "DE-template",
        "question": "Q1",
        "input_hash": "NO_EXTERNAL_INPUT",
        "python": sys.version,
        "model": "SLSQP",
        "parameters": {"bounds": BOUNDS, "seed": SEED},
        "command": "python 05_python/templates/optimization.py",
        "outputs": ["results/optimization_result.json"],
        "status": "RUN_COMPLETE",
        "notes": "Toy objective only. For real problems, compare local/global behavior and independently verify feasibility and optimality assumptions.",
    }
    (out / "optimization_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
