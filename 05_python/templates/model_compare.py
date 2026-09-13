"""Model comparison template for CUMCM E problems.

Compares Ridge, Random Forest and Gradient Boosting when available.
Uses one fixed hold-out split and reports MAE/RMSE/R2. Replace the toy
configuration with the actual contest data and feature set.
"""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DATA_PATH = Path("data/input.csv")
TARGET = "target"
FEATURES = []
SEED = 20260913
TEST_SIZE = 0.2


def sha256_file(path):
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
    X, y = df[features], pd.to_numeric(df[TARGET], errors="raise")
    num_cols = X.select_dtypes(include=np.number).columns.tolist()
    cat_cols = [c for c in X.columns if c not in num_cols]
    pre = ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")),
                          ("scale", StandardScaler())]), num_cols),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                          ("onehot", OneHotEncoder(handle_unknown="ignore"))]), cat_cols),
    ])
    models = {
        "Ridge": Ridge(alpha=1.0),
        "RandomForest": RandomForestRegressor(n_estimators=300, random_state=SEED, n_jobs=-1),
        "GradientBoosting": GradientBoostingRegressor(random_state=SEED),
    }
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=TEST_SIZE, random_state=SEED)
    rows = []
    out = Path("results"); out.mkdir(exist_ok=True)
    for name, estimator in models.items():
        pipe = Pipeline([("pre", pre), ("model", estimator)])
        pipe.fit(Xtr, ytr)
        pred = pipe.predict(Xte)
        rows.append({
            "model": name,
            "MAE": float(mean_absolute_error(yte, pred)),
            "RMSE": float(np.sqrt(mean_squared_error(yte, pred))),
            "R2": float(r2_score(yte, pred)),
        })
        pd.DataFrame({"y_true": yte.to_numpy(), "y_pred": pred}).to_csv(
            out / f"predictions_{name}.csv", index=False
        )
    result = pd.DataFrame(rows).sort_values("RMSE").reset_index(drop=True)
    result.to_csv(out / "model_comparison.csv", index=False)
    manifest = {
        "run_id": "model-comparison",
        "problem": "DE-template",
        "question": "Q1",
        "input_hash": sha256_file(DATA_PATH),
        "python": sys.version,
        "packages": {"numpy": np.__version__, "pandas": pd.__version__},
        "seed": SEED,
        "model": "Ridge+RandomForest+GradientBoosting",
        "parameters": {"test_size": TEST_SIZE, "ranking_metric": "RMSE"},
        "command": "python 05_python/templates/model_compare.py",
        "outputs": ["results/model_comparison.csv"],
        "status": "RUN_COMPLETE",
        "notes": "Model ranking is for candidate screening; final selection requires validation and problem-specific reasoning.",
    }
    (out / "model_comparison_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
