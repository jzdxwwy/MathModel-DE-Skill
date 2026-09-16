"""V0.9-F model-family verification rules.

Rules are evidence-first: a missing metric/artifact is NOT_RUN, never PASS.
The engine is deterministic and does not alter numerical results.
"""
from __future__ import annotations
from typing import Any


def _check(i, cat, status, evidence, metric=None, threshold=None):
    x={"check_id":i,"category":cat,"status":status,"evidence":evidence}
    if metric is not None: x["metric"]=metric
    if threshold is not None: x["threshold"]=threshold
    return x


def _metric(metrics, *names):
    for n in names:
        if n in metrics: return metrics[n]
    return None


def verify_domain(model_id: str, result: dict[str, Any], binding: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    binding=binding or {}; metrics=result.get("metrics") or {}; outputs=result.get("outputs") or []
    checks=[]
    if model_id in {"linear_regression","tree_ensemble_regression"}:
        r2=_metric(metrics,"R2","r2"); mae=_metric(metrics,"MAE","mae"); rmse=_metric(metrics,"RMSE","rmse")
        checks.append(_check("V-F01","statistical","PASS" if r2 is not None else "NOT_RUN","R2 evidence present" if r2 is not None else "R2 is absent" ,r2))
        checks.append(_check("V-F02","statistical","PASS" if mae is not None and rmse is not None else "NOT_RUN","MAE and RMSE evidence present" if mae is not None and rmse is not None else "MAE/RMSE evidence incomplete"))
        checks.append(_check("V-F03","robustness","PASS" if binding.get("seed") is not None or any("seed" in str(x).lower() for x in outputs) else "NOT_RUN","Reproducibility seed evidence" if binding.get("seed") is not None else "No explicit seed evidence"))
    elif model_id in {"logistic_classification","tree_ensemble_classification"}:
        f1=_metric(metrics,"F1","f1","macro_F1","weighted_F1"); acc=_metric(metrics,"accuracy","Accuracy")
        checks.append(_check("V-F04","statistical","PASS" if acc is not None else "NOT_RUN","Accuracy evidence present" if acc is not None else "Accuracy is absent",acc))
        checks.append(_check("V-F05","statistical","PASS" if f1 is not None else "NOT_RUN","F1 evidence present" if f1 is not None else "F1 is absent",f1))
    elif model_id == "time_series_baseline":
        mae=_metric(metrics,"mean_MAE","MAE"); rmse=_metric(metrics,"mean_RMSE","RMSE")
        checks.append(_check("V-F06","statistical","PASS" if mae is not None and rmse is not None else "NOT_RUN","Rolling/temporal error metrics present" if mae is not None and rmse is not None else "Temporal validation evidence incomplete"))
        checks.append(_check("V-F07","robustness","PASS" if "test_horizon" in binding else "NOT_RUN","Forecast horizon explicitly bound" if "test_horizon" in binding else "Forecast horizon not explicitly bound"))
    elif model_id == "optimization":
        feasible=_metric(metrics,"constraint_violation","feasible","feasibility")
        checks.append(_check("V-F08","model","PASS" if feasible is not None else "NOT_RUN","Constraint feasibility evidence present" if feasible is not None else "Constraint feasibility evidence absent",feasible))
        checks.append(_check("V-F09","sensitivity","NOT_RUN","Optimality/sensitivity evidence requires additional runs"))
    elif model_id == "shortest_path":
        dist=_metric(metrics,"distance"); path=any(x.get("name")=="path" for x in outputs if isinstance(x,dict))
        checks.append(_check("V-F10","model","PASS" if path else "NOT_RUN","Path output present" if path else "Path output absent"))
        checks.append(_check("V-F11","numerical","PASS" if dist is not None or any(x.get("name")=="distance" for x in outputs if isinstance(x,dict)) else "NOT_RUN","Path distance evidence present" if dist is not None or any(x.get("name")=="distance" for x in outputs if isinstance(x,dict)) else "Path distance absent"))
    elif model_id in {"monte_carlo","sensitivity"}:
        checks.append(_check("V-F12","robustness","PASS" if any(k in metrics for k in ("ci95","CI95","n","repetitions")) else "NOT_RUN","Repeated-simulation evidence present" if any(k in metrics for k in ("ci95","CI95","n","repetitions")) else "Simulation repetition evidence absent"))
    elif model_id in {"mechanism_simulation","trajectory_reconstruction"}:
        checks.append(_check("V-F13","model","PASS" if outputs else "NOT_RUN","Mechanism outputs present" if outputs else "Mechanism outputs absent"))
        checks.append(_check("V-F14","robustness","NOT_RUN","Parameter/trajectory stability requires additional evidence"))
    else:
        checks.append(_check("V-F99","other","NOT_RUN","No domain-specific verification rule registered for this model family"))
    return checks
