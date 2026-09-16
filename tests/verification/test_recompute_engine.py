from tools.verification.recompute_engine import recompute


def test_regression_recompute_matches_reported_metrics():
    result = {
        "model_id": "linear_regression",
        "outputs": [
            {"name": "y_true", "value": [1, 2, 3, 4], "unit": ""},
            {"name": "y_pred", "value": [1, 2, 2, 4], "unit": ""},
        ],
        "metrics": {"MAE": 0.25, "RMSE": 0.5, "R2": 0.8},
    }
    checks = recompute("linear_regression", result)
    assert all(x["status"] == "PASS" for x in checks)


def test_regression_mismatch_fails():
    result = {
        "model_id": "linear_regression",
        "outputs": [
            {"name": "y_true", "value": [1, 2, 3, 4], "unit": ""},
            {"name": "y_pred", "value": [1, 2, 2, 4], "unit": ""},
        ],
        "metrics": {"MAE": 0.5, "RMSE": 0.5, "R2": 0.8},
    }
    checks = recompute("linear_regression", result)
    assert any(x["status"] == "FAIL" for x in checks)


def test_missing_raw_evidence_is_not_run():
    result = {"model_id": "linear_regression", "metrics": {"MAE": 0.25}}
    checks = recompute("linear_regression", result)
    assert checks[0]["status"] == "NOT_RUN"


def test_classification_accuracy_recompute():
    result = {
        "model_id": "logistic_classification",
        "outputs": [
            {"name": "y_true", "value": [0, 1, 1, 0], "unit": ""},
            {"name": "y_pred", "value": [0, 1, 0, 0], "unit": ""},
        ],
        "metrics": {"accuracy": 0.75},
    }
    checks = recompute("logistic_classification", result)
    assert checks[0]["status"] == "PASS"
