"""V0.9-C mathematical input contracts for non-tabular templates."""
from __future__ import annotations
from typing import Any

class ContractBlocked(RuntimeError):
    pass

CONTRACTS: dict[str, dict[str, Any]] = {
    "time_series_baseline": {"kind": "tabular_time_series", "required": ["data_path", "time_col", "target"], "optional": ["features", "test_horizon", "min_train", "seed"]},
    "shortest_path": {"kind": "edge_list", "required": ["data_path", "source", "target"], "optional": ["directed"], "columns": ["u", "v", "weight"]},
    "mechanism_simulation": {"kind": "event_stream", "required": ["data_path", "entity_col", "time_col", "node_col"], "optional": ["max_gap_minutes", "sep"]},
    "optimization": {"kind": "explicit_objective_spec", "required": ["objective_expression", "variables", "bounds"], "optional": ["inequality_constraints", "initial_point", "seed"]},
    "sensitivity": {"kind": "explicit_objective_spec", "required": ["objective_expression", "base", "grid"], "optional": ["relative_grid", "seed"]},
    "monte_carlo": {"kind": "explicit_event_expression", "required": ["event_expression", "variables", "distributions", "n", "seed"], "optional": ["confidence_level"]},
}

def validate_binding(model_id: str, binding: dict[str, Any]) -> None:
    contract = CONTRACTS.get(model_id)
    if contract is None:
        raise ContractBlocked(f"no V0.9-C contract for model: {model_id}")
    missing = [k for k in contract["required"] if k not in binding or binding[k] in (None, "", [])]
    if missing:
        raise ContractBlocked(f"missing required bindings for {model_id}: {missing}")
    if model_id == "shortest_path" and binding.get("directed") not in (None, True, False):
        raise ContractBlocked("directed must be boolean")
    if model_id == "mechanism_simulation" and binding.get("max_gap_minutes") is not None and float(binding["max_gap_minutes"]) < 0:
        raise ContractBlocked("max_gap_minutes must be non-negative")
    if model_id == "monte_carlo" and int(binding["n"]) <= 0:
        raise ContractBlocked("n must be positive")
