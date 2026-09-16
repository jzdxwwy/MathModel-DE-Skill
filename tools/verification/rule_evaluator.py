"""V0.9-H schema-oriented mathematical acceptance evaluator.

The evaluator is conservative: it validates supplied evidence and simple
mathematical invariants, but never invents missing evidence.
"""
from __future__ import annotations
from typing import Any, Iterable
import math


def check(check_id: str, category: str, status: str, evidence: str, metric: Any = None, threshold: Any = None, artifact_ref: str | None = None) -> dict[str, Any]:
    out = {"check_id": check_id, "category": category, "status": status, "evidence": evidence}
    if metric is not None: out["metric"] = metric
    if threshold is not None: out["threshold"] = threshold
    if artifact_ref: out["artifact_ref"] = artifact_ref
    return out


def metric(metrics: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in metrics:
            return metrics[name]
    return None


def finite_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def _outputs(result: dict[str, Any]) -> dict[str, Any]:
    return {str(x.get("name")): x.get("value") for x in result.get("outputs", []) if isinstance(x, dict) and "name" in x}


def evaluate_model(model_id: str, result: dict[str, Any], binding: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    binding = binding or {}
    metrics = result.get("metrics") or {}
    outputs = _outputs(result)
    checks: list[dict[str, Any]] = []

    if model_id in {"linear_regression", "tree_ensemble_regression"}:
        for cid, names, label in [
            ("V-H01", ("R2", "r2"), "R²"),
            ("V-H02", ("MAE", "mae"), "MAE"),
            ("V-H03", ("RMSE", "rmse"), "RMSE"),
        ]:
            value = metric(metrics, *names)
            if value is None:
                checks.append(check(cid, "statistical", "NOT_RUN", f"{label} evidence is absent"))
            elif not finite_number(value):
                checks.append(check(cid, "numerical", "FAIL", f"{label} is not finite", value))
            else:
                checks.append(check(cid, "statistical", "PASS", f"{label} is finite and traceable in ResultBundle", value))
        r2 = metric(metrics, "R2", "r2")
        if r2 is not None and finite_number(r2) and not (-1.0 <= float(r2) <= 1.0):
            checks.append(check("V-H04", "statistical", "FAIL", "R² is outside its mathematical range [-1, 1]", r2, [-1.0, 1.0]))
        else:
            checks.append(check("V-H04", "statistical", "PASS" if r2 is not None else "NOT_RUN", "R² range check" if r2 is not None else "R² range cannot be checked without R²"))
        checks.append(check("V-H05", "statistical", "PASS" if binding.get("validation") or binding.get("cv") else "NOT_RUN", "Validation/CV binding is explicit" if binding.get("validation") or binding.get("cv") else "No explicit validation/CV evidence"))
        checks.append(check("V-H06", "data", "PASS" if binding.get("leakage_check") else "NOT_RUN", "Leakage check is explicitly bound" if binding.get("leakage_check") else "No explicit leakage-check evidence"))

    elif model_id in {"logistic_classification", "tree_ensemble_classification"}:
        for cid, names, label in [("V-H10", ("accuracy", "Accuracy"), "accuracy"), ("V-H11", ("F1", "f1", "macro_F1", "weighted_F1"), "F1")]:
            value = metric(metrics, *names)
            if value is None: checks.append(check(cid, "statistical", "NOT_RUN", f"{label} evidence is absent"))
            elif not finite_number(value): checks.append(check(cid, "numerical", "FAIL", f"{label} is not finite", value))
            elif not 0 <= float(value) <= 1: checks.append(check(cid, "statistical", "FAIL", f"{label} is outside [0, 1]", value, [0, 1]))
            else: checks.append(check(cid, "statistical", "PASS", f"{label} is finite and within [0, 1]", value, [0, 1]))
        checks.append(check("V-H12", "statistical", "PASS" if binding.get("cv") else "NOT_RUN", "Cross-validation is explicitly bound" if binding.get("cv") else "No explicit cross-validation evidence"))
        checks.append(check("V-H13", "data", "PASS" if binding.get("class_distribution") else "NOT_RUN", "Class distribution evidence is bound" if binding.get("class_distribution") else "Class distribution evidence absent"))

    elif model_id == "time_series_baseline":
        checks.append(check("V-H20", "data", "PASS" if binding.get("chronological_split") else "NOT_RUN", "Chronological split is explicitly bound" if binding.get("chronological_split") else "No chronological split evidence"))
        checks.append(check("V-H21", "data", "PASS" if binding.get("future_leakage_check") else "NOT_RUN", "Future-leakage check is explicitly bound" if binding.get("future_leakage_check") else "No future-leakage evidence"))
        checks.append(check("V-H22", "robustness", "PASS" if binding.get("test_horizon") is not None else "NOT_RUN", "Forecast horizon is explicit" if binding.get("test_horizon") is not None else "Forecast horizon absent"))

    elif model_id == "optimization":
        feasibility = metric(metrics, "constraint_violation", "feasible", "feasibility")
        if feasibility is None: checks.append(check("V-H30", "model", "NOT_RUN", "Constraint feasibility evidence absent"))
        elif isinstance(feasibility, bool): checks.append(check("V-H30", "model", "PASS" if feasibility else "FAIL", "Feasibility flag supplied", feasibility))
        elif finite_number(feasibility): checks.append(check("V-H30", "model", "PASS" if float(feasibility) <= 0 else "FAIL", "Constraint violation value supplied", feasibility, 0))
        else: checks.append(check("V-H30", "numerical", "FAIL", "Constraint feasibility evidence is not finite", feasibility))
        objective = metric(metrics, "objective", "objective_value", "optimal_value")
        checks.append(check("V-H31", "numerical", "PASS" if finite_number(objective) else "FAIL" if objective is not None else "NOT_RUN", "Objective value is finite" if objective is not None else "Objective value absent", objective))
        checks.append(check("V-H32", "model", "PASS" if binding.get("constraints") else "NOT_RUN", "Constraints are explicitly bound" if binding.get("constraints") else "Constraint definitions absent"))
        checks.append(check("V-H33", "sensitivity", "PASS" if binding.get("optimality_evidence") else "NOT_RUN", "Optimality evidence is bound" if binding.get("optimality_evidence") else "No optimality/stability evidence"))

    elif model_id == "shortest_path":
        path = outputs.get("path")
        distance = metric(metrics, "distance") or outputs.get("distance")
        checks.append(check("V-H40", "model", "PASS" if isinstance(path, list) and len(path) >= 2 else "NOT_RUN", "Path sequence is present" if path else "Path sequence absent"))
        checks.append(check("V-H41", "numerical", "PASS" if finite_number(distance) else "NOT_RUN", "Path distance is finite" if distance is not None else "Path distance absent", distance))
        checks.append(check("V-H42", "model", "PASS" if binding.get("edge_legality_check") else "NOT_RUN", "Edge legality is explicitly bound" if binding.get("edge_legality_check") else "No edge-legality evidence"))
        checks.append(check("V-H43", "numerical", "PASS" if binding.get("weight_consistency_check") else "NOT_RUN", "Path-weight consistency is explicitly bound" if binding.get("weight_consistency_check") else "No path-weight consistency evidence"))

    elif model_id in {"monte_carlo", "sensitivity"}:
        n = metric(metrics, "n", "repetitions")
        ci = metric(metrics, "ci95", "CI95")
        checks.append(check("V-H50", "robustness", "PASS" if finite_number(n) and float(n) >= 2 else "FAIL" if n is not None else "NOT_RUN", "Repetition count is valid" if n is not None else "Repetition count absent", n, 2))
        checks.append(check("V-H51", "robustness", "PASS" if ci is not None else "NOT_RUN", "Confidence interval evidence present" if ci is not None else "Confidence interval absent"))
        checks.append(check("V-H52", "provenance", "PASS" if binding.get("seed") is not None else "NOT_RUN", "Random seed is explicit" if binding.get("seed") is not None else "Random seed absent"))

    else:
        checks.append(check("V-H99", "other", "NOT_RUN", f"No V0.9-H acceptance profile registered for {model_id}"))

    return checks


def gate(checks: Iterable[dict[str, Any]]) -> str:
    statuses = [x.get("status") for x in checks]
    if "FAIL" in statuses: return "FAIL"
    if any(x in {"WARN", "NOT_RUN"} for x in statuses): return "PASS_WITH_WARNINGS"
    return "PASS"
