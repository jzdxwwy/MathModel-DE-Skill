"""Default V0.9 tool adapters.

These adapters are intentionally conservative: they provide executable
plumbing and deterministic audit output. Domain-specific numerical templates
are plugged in through ToolRegistry in later increments.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any


def _audit_tool(**kwargs: Any) -> dict[str, Any]:
    run_dir = Path(kwargs["run_dir"])
    return {
        "execution_mode": "adapter",
        "message": "Dispatch reached an executable tool boundary; numerical template execution is selected by the registered adapter.",
        "task_id": kwargs.get("task_id"),
        "model_id": kwargs.get("model_id"),
        "inputs": kwargs.get("inputs", []),
        "parameters": kwargs.get("parameters", {}),
        "run_dir": str(run_dir),
    }


def register_default_tools(registry) -> None:
    from .tool_registry import ToolSpec
    names = {
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
    for name, purpose in names.items():
        registry.register(ToolSpec(name=name, purpose=purpose, handler=_audit_tool, input_names=["task_id", "model_id", "run_dir"], output_names=["ResultBundle"]))
