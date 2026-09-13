"""Minimal, reproducible regression baseline for CUMCM E-type problems."""
from pathlib import Path
import hashlib
import json
import platform
import sys
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DATA_PATH = Path("data/input.csv")
TARGET = "target"
FEATURES = []
SEED = 20260913
PROBLEM = "DE-template"
QUESTION = "Q1"
MODEL = "Ridge-baseline"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    df = pd.read_csv(DATA_PATH)
    if TARGET not in df.columns:
        raise ValueError(f"Target column not found: {TARGET}")
    features = FEATURES or [c for c in df.columns if c != TARGET]
    X, y = df[features], df[TARGET]
    num_cols = X.select_dtypes(include=np.number).columns.tolist()
    cat_cols = [c for c in X.columns if c not in num_cols]
    pre = ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), num_cols),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), cat_cols),
    ])
    model = Pipeline([("pre", pre), ("model", Ridge(alpha=1.0))])
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=SEED)
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    metrics = {"MAE": float(mean_absolute_error(yte, pred)), "RMSE": float(np.sqrt(mean_squared_error(yte, pred))), "R2": float(r2_score(yte, pred))}
    out = Path("results"); out.mkdir(exist_ok=True)
    pred_path = out / "baseline_predictions.csv"
    pd.DataFrame({"y_true": yte.to_numpy(), "y_pred": pred}).to_csv(pred_path, index=False)
    manifest = {
        "run_id": "baseline-regression",
        "problem": PROBLEM,
        "question": QUESTION,
        "input_hash": sha256_file(DATA_PATH),
        "python": sys.version,
        "packages": {"numpy": np.__version__, "pandas": pd.__version__},
        "seed": SEED,
        "model": MODEL,
        "parameters": {"alpha": 1.0, "test_size": 0.2},
        "command": "python 05_python/templates/baseline_regression.py",
        "outputs": [str(pred_path), str(out / "run_manifest.json")],
        "status": "RUN_COMPLETE",
        "notes": json.dumps({"metrics": metrics}, ensure_ascii=False),
        "platform": platform.platform(),
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
