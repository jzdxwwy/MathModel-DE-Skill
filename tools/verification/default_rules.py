"""V0.9-G default verification rule registry."""
from __future__ import annotations
from .domain_verifier import verify_domain
from .rule_registry import VerificationRuleRegistry, VerificationRuleSet


def build_default_registry() -> VerificationRuleRegistry:
    registry = VerificationRuleRegistry()
    registry.register(VerificationRuleSet(
        rule_id="regression-v1",
        model_ids=("linear_regression", "tree_ensemble_regression"),
        version="1.0",
        handler=verify_domain,
    ))
    registry.register(VerificationRuleSet(
        rule_id="classification-v1",
        model_ids=("logistic_classification", "tree_ensemble_classification"),
        version="1.0",
        handler=verify_domain,
    ))
    registry.register(VerificationRuleSet(
        rule_id="time-series-v1",
        model_ids=("time_series_baseline",),
        version="1.0",
        handler=verify_domain,
    ))
    registry.register(VerificationRuleSet(
        rule_id="optimization-v1",
        model_ids=("optimization",),
        version="1.0",
        handler=verify_domain,
    ))
    registry.register(VerificationRuleSet(
        rule_id="network-v1",
        model_ids=("shortest_path",),
        version="1.0",
        handler=verify_domain,
    ))
    registry.register(VerificationRuleSet(
        rule_id="stochastic-v1",
        model_ids=("monte_carlo", "sensitivity"),
        version="1.0",
        handler=verify_domain,
    ))
    registry.register(VerificationRuleSet(
        rule_id="mechanism-v1",
        model_ids=("mechanism_simulation", "trajectory_reconstruction"),
        version="1.0",
        handler=verify_domain,
    ))
    return registry
