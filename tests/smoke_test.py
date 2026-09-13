"""Offline smoke test for the executable D/E templates.

Uses synthetic data only. It never solves or evaluates a real contest problem.
Run from repository root:
    python tests/smoke_test.py
"""
from pathlib import Path
import json
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "tests" / "_smoke_workspace"
TEMPLATES = ROOT / "05_python" / "templates"
REQUIRED = {"run_id", "problem", "question", "model", "status"}


def make_data():
    WORK.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(12345)
    n = 40
    x1 = np.arange(n, dtype=float)
    x2 = rng.normal(size=n)
    y = 3.0 * x1 + 2.0 * x2 + rng.normal(scale=0.5, size=n)
    pd.DataFrame({"time": pd.date_range("2026-01-01", periods=n, freq="D"), "x1": x1, "x2": x2, "target": y}).to_csv(WORK / "data.csv", index=False)
    (WORK / "data").mkdir(exist_ok=True)
    shutil.copy2(WORK / "data.csv", WORK / "data" / "input.csv")


def run(script: str):
    completed = subprocess.run([sys.executable, str(TEMPLATES / script)], cwd=WORK, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"{script} failed:\nSTDOUT={completed.stdout}\nSTDERR={completed.stderr}")
    return completed


def check_manifest(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = REQUIRED - data.keys()
    if missing:
        raise AssertionError(f"{path}: missing required fields {sorted(missing)}")
    if data["status"] != "RUN_COMPLETE":
        raise AssertionError(f"{path}: unexpected status {data['status']}")


def main():
    if WORK.exists():
        shutil.rmtree(WORK)
    make_data()

    run("baseline_regression.py")
    check_manifest(WORK / "results" / "run_manifest.json")
    pred = pd.read_csv(WORK / "results" / "baseline_predictions.csv")
    assert len(pred) == 8 and pred.notna().all().all()

    run("time_series_cv.py")
    check_manifest(WORK / "results" / "time_series_manifest.json")
    ts = pd.read_csv(WORK / "results" / "time_series_cv.csv")
    assert len(ts) == 30 and ts[["MAE", "RMSE"]].notna().all().all()

    run("monte_carlo.py")
    check_manifest(WORK / "results" / "monte_carlo_manifest.json")
    mc = json.loads((WORK / "results" / "monte_carlo_manifest.json").read_text(encoding="utf-8"))
    assert mc["parameters"]["N"] == 100_000

    run("sensitivity.py")
    check_manifest(WORK / "results" / "sensitivity_manifest.json")
    sens = pd.read_csv(WORK / "results" / "sensitivity.csv")
    assert len(sens) == 27

    print("SMOKE TEST PASSED: 4 templates executed successfully on synthetic data.")
    print(f"Workspace: {WORK}")


if __name__ == "__main__":
    main()
