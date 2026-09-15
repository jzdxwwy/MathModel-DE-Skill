"""Offline V0.8 dispatch contract tests. Not executed in this environment."""
from tools.runtime.tool_dispatch import build_dispatch


def test_dispatch_is_closed_and_planned_only():
    plan={"task_models":[{"task_id":"Q1","candidates":[{"model_id":"linear_regression","name":"线性回归","fit_rationale":"baseline","score":80}],"selection":{"model_id":"linear_regression","reason":"baseline"}}]}
    result=build_dispatch(plan)
    assert result["artifact_type"]=="ToolDispatchPlan"
    assert result["dispatches"][0]["status"]=="PLANNED"
    assert result["dispatches"][0]["tool"]=="python.baseline_regression"
