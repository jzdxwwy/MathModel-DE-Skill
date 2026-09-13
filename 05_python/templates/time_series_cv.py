"""Rolling-origin validation template for time-series E problems."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.linear_model import Ridge

DATA_PATH = Path("data/input.csv")
TIME_COL = "time"
TARGET = "target"
FEATURES = []
SEED = 20260913
TEST_HORIZON = 1
MIN_TRAIN = 10


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    df = pd.read_csv(DATA_PATH).sort_values(TIME_COL).reset_index(drop=True)
    features = FEATURES or [c for c in df.columns if c not in (TIME_COL, TARGET)]
    X = df[features].apply(pd.to_numeric, errors="coerce").ffill().fillna(0)
    y = pd.to_numeric(df[TARGET], errors="coerce")
    rows = []
    for end in range(MIN_TRAIN, len(df) - TEST_HORIZON + 1):
        tr = slice(0, end)
        te = slice(end, end + TEST_HORIZON)
        model = Ridge(alpha=1.0)
        model.fit(X.iloc[tr], y.iloc[tr])
        pred = model.predict(X.iloc[te])
        rows.append({"origin": end, "MAE": mean_absolute_error(y.iloc[te], pred), "RMSE": np.sqrt(mean_squared_error(y.iloc[te], pred))})
    if not rows:
        raise ValueError("Not enough observations for rolling validation")
    result = pd.DataFrame(rows)
    out = Path("results"); out.mkdir(exist_ok=True)
    result_path = out / "time_series_cv.csv"
    result.to_csv(result_path, index=False)
    manifest = {
        "run_id": "time-series-cv",
        "problem": "DE-template",
        "question": "Q1",
        "input_hash": sha256_file(DATA_PATH),
        "python": sys.version,
        "seed": SEED,
        "model": "Ridge-rolling-origin",
        "parameters": {"alpha": 1.0, "test_horizon": TEST_HORIZON, "min_train": MIN_TRAIN},
        "command": "python 05_python/templates/time_series_cv.py",
        "outputs": [str(result_path), str(out / "time_series_manifest.json")],
        "status": "RUN_COMPLETE",
        "notes": json.dumps({"n_folds": len(result), "mean_MAE": float(result.MAE.mean()), "mean_RMSE": float(result.RMSE.mean())}, ensure_ascii=False),
    }
    (out / "time_series_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
