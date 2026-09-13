"""Minimal, reproducible regression baseline for CUMCM E-type problems.

Usage: adapt DATA_PATH, TARGET, FEATURES and run locally.
The script reports MAE/RMSE/R2 and saves predictions plus a manifest.
"""
from pathlib import Path
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
FEATURES = []  # empty => use all columns except target
SEED = 20260913


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
    pd.DataFrame({"y_true": yte.to_numpy(), "y_pred": pred}).to_csv(out / "baseline_predictions.csv", index=False)
    manifest = {"template": "baseline_regression", "seed": SEED, "target": TARGET, "features": features, "metrics": metrics, "python": sys.version, "platform": platform.platform(), "status": "RUN_COMPLETE"}
    (out / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
