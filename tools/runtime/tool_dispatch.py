"""V0.8 provider-neutral dispatch planning; execution remains V0.9."""
from __future__ import annotations
from typing import Any


def build_dispatch(model_plan: dict[str, Any]) -> dict[str, Any]:
    dispatches=[]
    for tm in model_plan.get("task_models", []):
        selected=tm["selection"]["model_id"]
        candidate=next(c for c in tm["candidates"] if c["model_id"]==selected)
        dispatches.append({"task_id":tm["task_id"],"model_id":selected,"tool":candidate.get("tool") or _tool_from_model(candidate),"inputs":["DataProfile","ProblemMap"],"outputs":["RunManifest","ResultBundle"],"status":"PLANNED"})
    return {"artifact_type":"ToolDispatchPlan","schema_version":"0.8","status":"VALIDATED","dispatches":dispatches}


def _tool_from_model(candidate: dict[str, Any]) -> str:
    # Catalog normally supplies this field; this fallback is deliberately closed.
    allowed={"linear_regression":"python.baseline_regression","tree_ensemble_regression":"python.model_compare","logistic_classification":"python.classification_cv","tree_ensemble_classification":"python.classification_cv","time_series_baseline":"python.time_series_cv","clustering":"python.model_compare","pca":"python.model_compare","optimization":"python.optimization","shortest_path":"python.graph_shortest_path","monte_carlo":"python.monte_carlo","sensitivity":"python.sensitivity","mechanism_simulation":"python.trajectory_reconstruction"}
    return allowed[candidate["model_id"]]
