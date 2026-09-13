"""Offline smoke test for the executable D/E templates.

Uses synthetic data only. It never solves or evaluates a real contest problem.
Run from repository root: python tests/smoke_test.py
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


def make_regression_data():
    WORK.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(12345)
    n = 40
    x1 = np.arange(n, dtype=float)
    x2 = rng.normal(size=n)
    y = 3.0 * x1 + 2.0 * x2 + rng.normal(scale=0.5, size=n)
    df = pd.DataFrame({
        "time": pd.date_range("2026-01-01", periods=n, freq="D"),
        "x1": x1, "x2": x2, "target": y,
    })
    df.to_csv(WORK / "data.csv", index=False)
    (WORK / "data").mkdir(exist_ok=True)
    shutil.copy2(WORK / "data.csv", WORK / "data" / "input.csv")


def make_classification_data():
    rng = np.random.default_rng(54321)
    n = 60
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    target = ((x1 + 0.8 * x2) > 0).astype(int)
    pd.DataFrame({"x1": x1, "x2": x2, "target": target}).to_csv(WORK / "data" / "input.csv", index=False)


def make_graph_data():
    pd.DataFrame({
        "u": ["A", "A", "B", "B", "C", "D"],
        "v": ["B", "C", "C", "D", "Z", "Z"],
        "weight": [2, 5, 1, 4, 3, 1],
    }).to_csv(WORK / "data" / "edges.csv", index=False)


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
    make_regression_data()

    run("baseline_regression.py")
    check_manifest(WORK / "results" / "run_manifest.json")
    pred = pd.read_csv(WORK / "results" / "baseline_predictions.csv")
    assert len(pred) == 8 and pred.notna().all().all()

    run("time_series_cv.py")
    check_manifest(WORK / "results" / "time_series_manifest.json")
    ts = pd.read_csv(WORK / "results" / "time_series_cv.csv")
    assert len(ts) == 30 and ts[["MAE", "RMSE"]].notna().all().all()

    run("model_compare.py")
    check_manifest(WORK / "results" / "model_comparison_manifest.json")
    comparison = pd.read_csv(WORK / "results" / "model_comparison.csv")
    assert len(comparison) == 3 and comparison[["MAE", "RMSE", "R2"]].notna().all().all()

    run("monte_carlo.py")
    check_manifest(WORK / "results" / "monte_carlo_manifest.json")
    mc = json.loads((WORK / "results" / "monte_carlo_manifest.json").read_text(encoding="utf-8"))
    assert mc["N"] == 100_000

    run("sensitivity.py")
    check_manifest(WORK / "results" / "sensitivity_manifest.json")
    sens = pd.read_csv(WORK / "results" / "sensitivity.csv")
    assert len(sens) == 27

    run("optimization.py")
    check_manifest(WORK / "results" / "optimization_manifest.json")
    opt = json.loads((WORK / "results" / "optimization_result.json").read_text(encoding="utf-8"))
    assert opt["success"] and len(opt["x"]) == 2

    make_graph_data()
    run("graph_shortest_path.py")
    check_manifest(WORK / "results" / "shortest_path_manifest.json")
    graph = json.loads((WORK / "results" / "shortest_path.json").read_text(encoding="utf-8"))
    assert graph["path"] == ["A", "B", "C", "Z"] and abs(graph["distance"] - 6.0) < 1e-9

    make_classification_data()
    run("classification_cv.py")
    check_manifest(WORK / "results" / "classification_cv_manifest.json")
    clf = pd.read_csv(WORK / "results" / "classification_cv.csv")
    assert len(clf) == 5 and clf[["accuracy", "f1_macro", "roc_auc"]].notna().all().all()

    print("SMOKE TEST PASSED: 8 templates executed successfully on synthetic data.")
    print(f"Workspace: {WORK}")


if __name__ == "__main__":
    main()
