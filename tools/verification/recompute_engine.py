"""V0.9-I independent recomputation of auditable numerical evidence.

This layer never trusts a reported metric merely because it exists in a
ResultBundle.  When raw evidence is available, it recomputes the metric with
an independent implementation and compares the result within an explicit
tolerance.  Missing evidence remains NOT_RUN.
"""
from __future__ import annotations

import math
from typing import Any


def _finite(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def _metric(result: dict[str, Any], *names: str) -> Any:
    metrics = result.get("metrics") or {}
    for name in names:
        if name in metrics:
            return metrics[name]
    return None


def _output(result: dict[str, Any], *names: str) -> Any:
    for item in result.get("outputs", []):
        if isinstance(item, dict) and item.get("name") in names:
            return item.get("value")
    return None


def _close(a: float, b: float, atol: float = 1e-8, rtol: float = 1e-6) -> bool:
    return math.isclose(float(a), float(b), abs_tol=atol, rel_tol=rtol)


def _check(cid: str, category: str, status: str, evidence: str, metric: Any = None, threshold: Any = None) -> dict[str, Any]:
    out = {"check_id": cid, "category": category, "status": status, "evidence": evidence}
    if metric is not None:
        out["metric"] = metric
    if threshold is not None:
        out["threshold"] = threshold
    return out


def recompute_regression(result: dict[str, Any]) -> list[dict[str, Any]]:
    y_true = _output(result, "y_true", "actual", "target_true")
    y_pred = _output(result, "y_pred", "predicted", "target_pred")
    checks: list[dict[str, Any]] = []
    if not isinstance(y_true, list) or not isinstance(y_pred, list) or len(y_true) != len(y_pred) or not y_true:
        return [_check("V-I01", "numerical", "NOT_RUN", "Raw y_true/y_pred evidence is unavailable or length-mismatched")]
    try:
        yt = [float(x) for x in y_true]
        yp = [float(x) for x in y_pred]
        if not all(math.isfinite(x) for x in yt + yp):
            return [_check("V-I01", "numerical", "FAIL", "Raw regression evidence contains non-finite values")]
        n = len(yt)
        mae = sum(abs(a - b) for a, b in zip(yt, yp)) / n
        rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(yt, yp)) / n)
        mean_y = sum(yt) / n
        sst = sum((a - mean_y) ** 2 for a in yt)
        r2 = 1.0 - sum((a - b) ** 2 for a, b in zip(yt, yp)) / sst if sst > 0 else None
        for cid, label, calc, reported in [
            ("V-I02", "MAE", mae, _metric(result, "MAE", "mae")),
            ("V-I03", "RMSE", rmse, _metric(result, "RMSE", "rmse")),
            ("V-I04", "R²", r2, _metric(result, "R2", "r2")),
        ]:
            if reported is None or calc is None:
                checks.append(_check(cid, "statistical", "NOT_RUN", f"{label}: recomputation available but reported value is absent", calc))
            elif not _finite(reported):
                checks.append(_check(cid, "numerical", "FAIL", f"Reported {label} is non-finite", reported))
            elif _close(calc, float(reported)):
                checks.append(_check(cid, "statistical", "PASS", f"Independent {label} recomputation matches ResultBundle", calc, {"atol":1e-8,"rtol":1e-6}))
            else:
                checks.append(_check(cid, "statistical", "FAIL", f"Independent {label} recomputation does not match ResultBundle", {"reported":reported,"recomputed":calc}))
        return checks
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        return [_check("V-I01", "numerical", "FAIL", f"Regression recomputation failed: {type(exc).__name__}: {exc}")]


def recompute_classification(result: dict[str, Any]) -> list[dict[str, Any]]:
    y_true = _output(result, "y_true", "actual", "target_true")
    y_pred = _output(result, "y_pred", "predicted", "target_pred")
    if not isinstance(y_true, list) or not isinstance(y_pred, list) or len(y_true) != len(y_pred) or not y_true:
        return [_check("V-I10", "numerical", "NOT_RUN", "Raw classification labels are unavailable or length-mismatched")]
    correct = sum(a == b for a, b in zip(y_true, y_pred))
    accuracy = correct / len(y_true)
    reported = _metric(result, "accuracy", "Accuracy")
    if reported is None:
        return [_check("V-I11", "statistical", "NOT_RUN", "Accuracy can be recomputed but reported accuracy is absent", accuracy)]
    if not _finite(reported):
        return [_check("V-I11", "numerical", "FAIL", "Reported accuracy is non-finite", reported)]
    return [_check("V-I11", "statistical", "PASS" if _close(accuracy, float(reported)) else "FAIL", "Independent accuracy recomputation comparison", {"reported":reported,"recomputed":accuracy})]


def recompute(model_id: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    if model_id in {"linear_regression", "tree_ensemble_regression"}:
        return recompute_regression(result)
    if model_id in {"logistic_classification", "tree_ensemble_classification"}:
        return recompute_classification(result)
    return [_check("V-I99", "other", "NOT_RUN", f"No independent recomputation adapter for {model_id}")]
