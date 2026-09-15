"""V0.9-B executable tool adapters.

Only explicitly bound tabular E-type templates execute numerical code.
Unsupported models fail closed with INPUT_BLOCKED instead of fabricating data.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from .template_adapter import InputBlocked, execute_tabular_template


def _audit_tool(**kwargs: Any) -> dict[str, Any]:
    run_dir = Path(kwargs["run_dir"])
    return {
        "execution_mode": "audit",
        "message": "No numerical adapter is registered for this model yet.",
        "task_id": kwargs.get("task_id"),
        "model_id": kwargs.get("model_id"),
        "inputs": kwargs.get("inputs", []),
        "parameters": kwargs.get("parameters", {}),
        "run_dir": str(run_dir),
    }


def _template_tool(**kwargs: Any) -> dict[str, Any]:
    result = execute_tabular_template(
        repo_root=Path(kwargs["repo_root"]),
        project_dir=Path(kwargs["project_dir"]),
        run_dir=Path(kwargs["run_dir"]),
        model_id=str(kwargs["model_id"]),
        binding=dict(kwargs.get("binding") or kwargs.get("parameters") or {}),
    )
    return {
        "execution_mode": "numerical_template",
        "outputs": result.outputs,
        "metrics": result.metrics,
        "artifacts": result.artifacts,
    }


def register_default_tools(registry) -> None:
    from .tool_registry import ToolSpec
    numerical = {
        "python.baseline_regression": "linear_regression",
        "python.model_compare": "tree_ensemble_regression",
        "python.classification_cv": "logistic_classification",
    }
    all_names = {
        "python.baseline_regression": "baseline regression execution",
        "python.model_compare": "model comparison execution",
        "python.classification_cv": "classification cross-validation execution",
        "python.time_series_cv": "time-series cross-validation execution",
        "python.optimization": "optimization execution",
        "python.graph_shortest_path": "network shortest-path execution",
        "python.monte_carlo": "Monte Carlo execution",
        "python.sensitivity": "sensitivity analysis execution",
        "python.trajectory_reconstruction": "trajectory reconstruction execution",
    }
    for name, purpose in all_names.items():
        if name in numerical:
            registry.register(ToolSpec(name=name, purpose=purpose, handler=_template_tool, input_names=["task_id", "model_id", "project_dir", "run_dir", "binding"], output_names=["ResultBundle"]))
        else:
            registry.register(ToolSpec(name=name, purpose=purpose, handler=_audit_tool, input_names=["task_id", "model_id", "run_dir"], output_names=["ResultBundle"]))
