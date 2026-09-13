"""Safe abstract stochastic coverage optimization template.

Use for non-weapon applications such as sensor deployment, inspection,
warehouse-robot coverage, or environmental monitoring.

The model maximizes the probability that at least one circular coverage
region contains a randomly located target point. Replace the objective and
constraints with the actual non-sensitive application model.
"""
from pathlib import Path
import json
import sys
import hashlib
import numpy as np
from scipy.optimize import differential_evolution

SEED = 20260913
DOMAIN = (-10.0, 10.0, -10.0, 10.0)
RADIUS = 2.0
N_SENSORS = 3
SIGMA_X = 2.0
SIGMA_Y = 2.0
N_MC = 50000


def sample_targets(n=N_MC, seed=SEED):
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, SIGMA_X, n)
    y = rng.normal(0.0, SIGMA_Y, n)
    xmin, xmax, ymin, ymax = DOMAIN
    mask = (x >= xmin) & (x <= xmax) & (y >= ymin) & (y <= ymax)
    return x[mask], y[mask]


def coverage_probability(params, x, y):
    sensors = np.asarray(params).reshape(N_SENSORS, 2)
    covered = np.zeros(len(x), dtype=bool)
    for sx, sy in sensors:
        covered |= (x - sx) ** 2 + (y - sy) ** 2 <= RADIUS ** 2
    return float(np.mean(covered))


def objective(params, x, y):
    return -coverage_probability(params, x, y)


def main():
    x, y = sample_targets()
    xmin, xmax, ymin, ymax = DOMAIN
    bounds = [(xmin, xmax), (ymin, ymax)] * N_SENSORS
    result = differential_evolution(
        objective,
        bounds=bounds,
        args=(x, y),
        seed=SEED,
        maxiter=40,
        popsize=8,
        polish=True,
        workers=1,
    )
    p = -float(result.fun)
    sensors = np.asarray(result.x).reshape(N_SENSORS, 2)

    # Independent verification with a fresh random stream.
    xv, yv = sample_targets(n=N_MC, seed=SEED + 1)
    p_verify = coverage_probability(result.x, xv, yv)
    se = np.sqrt(max(p_verify * (1 - p_verify), 0.0) / len(xv))

    out = Path("results")
    out.mkdir(exist_ok=True)
    payload = {
        "coverage_probability_train": p,
        "coverage_probability_verify": p_verify,
        "verify_95ci": [p_verify - 1.96 * se, p_verify + 1.96 * se],
        "sensor_positions": sensors.tolist(),
        "success": bool(result.success),
        "message": result.message,
    }
    (out / "stochastic_coverage_result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manifest = {
        "run_id": "stochastic-coverage-optimization",
        "problem": "DE-safe-coverage-benchmark",
        "question": "Q1",
        "input_hash": hashlib.sha256(b"synthetic-internal-data").hexdigest(),
        "python": sys.version,
        "model": "Differential Evolution + Monte Carlo verification",
        "parameters": {
            "domain": DOMAIN, "radius": RADIUS, "n_sensors": N_SENSORS,
            "sigma_x": SIGMA_X, "sigma_y": SIGMA_Y,
            "n_mc": N_MC, "seed": SEED,
        },
        "command": "python 05_python/templates/stochastic_coverage_optimization.py",
        "outputs": ["results/stochastic_coverage_result.json"],
        "status": "RUN_COMPLETE",
        "notes": "Safe abstract coverage benchmark. Do not adapt this template to weapon targeting or other harmful applications.",
    }
    (out / "stochastic_coverage_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
