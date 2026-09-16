"""V0.9-I/J independent recomputation of auditable numerical evidence."""
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
    if metric is not None: out["metric"] = metric
    if threshold is not None: out["threshold"] = threshold
    return out

def recompute_regression(result: dict[str, Any]) -> list[dict[str, Any]]:
    y_true = _output(result, "y_true", "actual", "target_true")
    y_pred = _output(result, "y_pred", "predicted", "target_pred")
    if not isinstance(y_true, list) or not isinstance(y_pred, list) or len(y_true) != len(y_pred) or not y_true:
        return [_check("V-I01", "numerical", "NOT_RUN", "Raw y_true/y_pred evidence is unavailable or length-mismatched")]
    try:
        yt, yp = [float(x) for x in y_true], [float(x) for x in y_pred]
        if not all(math.isfinite(x) for x in yt + yp):
            return [_check("V-I01", "numerical", "FAIL", "Raw regression evidence contains non-finite values")]
        n = len(yt); mae = sum(abs(a-b) for a,b in zip(yt,yp))/n
        rmse = math.sqrt(sum((a-b)**2 for a,b in zip(yt,yp))/n)
        mean_y = sum(yt)/n; sst = sum((a-mean_y)**2 for a in yt)
        r2 = 1.0 - sum((a-b)**2 for a,b in zip(yt,yp))/sst if sst > 0 else None
        checks=[]
        for cid,label,calc,reported in [("V-I02","MAE",mae,_metric(result,"MAE","mae")),("V-I03","RMSE",rmse,_metric(result,"RMSE","rmse")),("V-I04","R²",r2,_metric(result,"R2","r2"))]:
            if reported is None or calc is None: checks.append(_check(cid,"statistical","NOT_RUN",f"{label}: recomputation available but reported value is absent",calc))
            elif not _finite(reported): checks.append(_check(cid,"numerical","FAIL",f"Reported {label} is non-finite",reported))
            elif _close(calc,float(reported)): checks.append(_check(cid,"statistical","PASS",f"Independent {label} recomputation matches ResultBundle",calc,{"atol":1e-8,"rtol":1e-6}))
            else: checks.append(_check(cid,"statistical","FAIL",f"Independent {label} recomputation does not match ResultBundle",{"reported":reported,"recomputed":calc}))
        return checks
    except (TypeError,ValueError,ZeroDivisionError) as exc:
        return [_check("V-I01","numerical","FAIL",f"Regression recomputation failed: {type(exc).__name__}: {exc}")]

def recompute_classification(result: dict[str, Any]) -> list[dict[str, Any]]:
    y_true,y_pred=_output(result,"y_true","actual","target_true"),_output(result,"y_pred","predicted","target_pred")
    if not isinstance(y_true,list) or not isinstance(y_pred,list) or len(y_true)!=len(y_pred) or not y_true:
        return [_check("V-I10","numerical","NOT_RUN","Raw classification labels are unavailable or length-mismatched")]
    accuracy=sum(a==b for a,b in zip(y_true,y_pred))/len(y_true); reported=_metric(result,"accuracy","Accuracy")
    if reported is None: return [_check("V-I11","statistical","NOT_RUN","Accuracy can be recomputed but reported accuracy is absent",accuracy)]
    if not _finite(reported): return [_check("V-I11","numerical","FAIL","Reported accuracy is non-finite",reported)]
    return [_check("V-I11","statistical","PASS" if _close(accuracy,float(reported)) else "FAIL","Independent accuracy recomputation comparison",{"reported":reported,"recomputed":accuracy})]

def recompute_optimization(result: dict[str, Any]) -> list[dict[str, Any]]:
    obj=_output(result,"objective_value","objective","f_x"); reported=_metric(result,"objective_value","objective","objective_value_reported")
    if obj is None and reported is None: return [_check("V-I20","model","NOT_RUN","No objective value evidence available")]
    if obj is None: return [_check("V-I20","model","NOT_RUN","Reported objective exists but independently evaluable objective evidence is absent")]
    if not _finite(obj): return [_check("V-I20","numerical","FAIL","Objective value is non-finite",obj)]
    if reported is not None and _finite(reported):
        return [_check("V-I21","model","PASS" if _close(float(obj),float(reported)) else "FAIL","Objective value consistency check",{"reported":reported,"recomputed":obj})]
    return [_check("V-I21","model","NOT_RUN","Objective evidence exists but no comparable reported objective metric")]

def recompute_shortest_path(result: dict[str, Any]) -> list[dict[str, Any]]:
    path=_output(result,"path"); distance=_output(result,"distance","path_distance")
    if not isinstance(path,list): return [_check("V-I30","model","NOT_RUN","Path edge/node sequence is unavailable")]
    edges=_output(result,"path_edges","edges")
    if not isinstance(edges,list): return [_check("V-I31","model","NOT_RUN","Path exists but edge weights are unavailable for independent summation")]
    weights=[]
    for e in edges:
        if isinstance(e,dict) and _finite(e.get("weight")): weights.append(float(e["weight"]))
        elif isinstance(e,(list,tuple)) and len(e)>=3 and _finite(e[2]): weights.append(float(e[2]))
        else: return [_check("V-I31","model","FAIL","Path edge has no finite weight")]
    total=sum(weights)
    if distance is None: return [_check("V-I32","numerical","NOT_RUN","Path distance can be independently summed but reported distance is absent",total)]
    return [_check("V-I32","numerical","PASS" if _close(total,float(distance)) else "FAIL","Independent path-weight sum comparison",{"reported":distance,"recomputed":total})]

def recompute_stochastic(result: dict[str, Any]) -> list[dict[str, Any]]:
    samples=_output(result,"samples","simulation_samples"); mean_reported=_metric(result,"mean","mean_estimate"); ci=_metric(result,"ci95","CI95")
    if not isinstance(samples,list) or not samples: return [_check("V-I40","statistical","NOT_RUN","Raw simulation samples are unavailable")]
    try:
        vals=[float(x) for x in samples]
        if not all(math.isfinite(x) for x in vals): return [_check("V-I40","numerical","FAIL","Simulation samples contain non-finite values")]
        mean=sum(vals)/len(vals); checks=[]
        if mean_reported is not None:
            checks.append(_check("V-I41","statistical","PASS" if _close(mean,float(mean_reported)) else "FAIL","Independent Monte Carlo mean comparison",{"reported":mean_reported,"recomputed":mean}))
        else: checks.append(_check("V-I41","statistical","NOT_RUN","Monte Carlo mean can be recomputed but reported mean is absent",mean))
        if isinstance(ci,(list,tuple)) and len(ci)==2 and all(_finite(x) for x in ci):
            se=math.sqrt(sum((x-mean)**2 for x in vals)/(len(vals)-1))/math.sqrt(len(vals)) if len(vals)>1 else None
            if se is None: checks.append(_check("V-I42","statistical","NOT_RUN","At least two samples are required for CI recomputation"))
            else:
                calc=(mean-1.96*se,mean+1.96*se)
                checks.append(_check("V-I42","statistical","PASS" if _close(calc[0],float(ci[0])) and _close(calc[1],float(ci[1])) else "FAIL","Independent 95% CI comparison",{"reported":list(ci),"recomputed":list(calc)}))
        else: checks.append(_check("V-I42","statistical","NOT_RUN","Reported CI95 is absent or not a two-value interval"))
        return checks
    except (TypeError,ValueError,ZeroDivisionError) as exc: return [_check("V-I40","numerical","FAIL",f"Stochastic recomputation failed: {type(exc).__name__}: {exc}")]

def recompute_sensitivity(result: dict[str, Any]) -> list[dict[str, Any]]:
    base=_output(result,"base_value","baseline"); perturbed=_output(result,"perturbed_values","responses"); reported=_output(result,"sensitivities","sensitivity")
    if not isinstance(perturbed,list) or not isinstance(reported,list): return [_check("V-I50","sensitivity","NOT_RUN","Sensitivity perturbation responses and reported sensitivities are unavailable")]
    if base is None: return [_check("V-I50","sensitivity","NOT_RUN","Baseline response is unavailable")]
    try:
        if len(perturbed)!=len(reported): return [_check("V-I51","sensitivity","FAIL","Sensitivity response and reported sensitivity lengths differ")]
        checks=[]
        for i,(response,sens) in enumerate(zip(perturbed,reported)):
            if not _finite(response) or not _finite(sens): return [_check("V-I51","sensitivity","FAIL",f"Sensitivity item {i} is non-finite")]
        return [_check("V-I51","sensitivity","PASS","Sensitivity evidence has aligned finite response arrays")]
    except TypeError: return [_check("V-I51","sensitivity","FAIL","Sensitivity evidence is not numerically structured")]

def recompute(model_id: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    if model_id in {"linear_regression","tree_ensemble_regression"}: return recompute_regression(result)
    if model_id in {"logistic_classification","tree_ensemble_classification"}: return recompute_classification(result)
    if model_id == "optimization": return recompute_optimization(result)
    if model_id == "shortest_path": return recompute_shortest_path(result)
    if model_id == "monte_carlo": return recompute_stochastic(result)
    if model_id == "sensitivity": return recompute_sensitivity(result)
    return [_check("V-I99","other","NOT_RUN",f"No independent recomputation adapter for {model_id}")]
