"""Classification baseline with stratified cross-validation for E problems."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DATA_PATH = Path("data/input.csv")
TARGET = "target"
FEATURES = []
SEED = 20260913
N_SPLITS = 5


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
    X = df[features]
    y = df[TARGET]
    num_cols = X.select_dtypes(include=np.number).columns.tolist()
    cat_cols = [c for c in X.columns if c not in num_cols]
    pre = ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), num_cols),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), cat_cols),
    ])
    pipe = Pipeline([("pre", pre), ("model", LogisticRegression(max_iter=2000, random_state=SEED))])
    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
    scoring = {"accuracy": "accuracy", "f1_macro": "f1_macro", "roc_auc": "roc_auc"}
    scores = cross_validate(pipe, X, y, cv=cv, scoring=scoring, error_score="raise")
    result = pd.DataFrame({
        "fold": np.arange(1, N_SPLITS + 1),
        "accuracy": scores["test_accuracy"],
        "f1_macro": scores["test_f1_macro"],
        "roc_auc": scores["test_roc_auc"],
    })
    out = Path("results"); out.mkdir(exist_ok=True)
    result.to_csv(out / "classification_cv.csv", index=False)
    manifest = {
        "run_id": "classification-cv",
        "problem": "DE-template",
        "question": "Q1",
        "input_hash": sha256_file(DATA_PATH),
        "python": sys.version,
        "packages": {"numpy": np.__version__, "pandas": pd.__version__},
        "seed": SEED,
        "model": "LogisticRegression",
        "parameters": {"n_splits": N_SPLITS, "stratified": True},
        "command": "python 05_python/templates/classification_cv.py",
        "outputs": ["results/classification_cv.csv"],
        "status": "RUN_COMPLETE",
        "notes": "For repeated observations per subject/site, replace StratifiedKFold with a grouped split to prevent leakage.",
        "mean_metrics": {c: float(result[c].mean()) for c in ["accuracy", "f1_macro", "roc_auc"]},
    }
    (out / "classification_cv_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
