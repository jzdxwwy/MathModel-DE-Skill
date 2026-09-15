"""V0.9-D deterministic binding resolver.

Binding is derived from authoritative DataProfile facts plus validated semantic
roles. LLM proposals are treated only as optional hints; they may be used when
they reference real assets/columns, but cannot invent data.
"""
from __future__ import annotations
from typing import Any


TABULAR = {"csv", "tsv", "txt", "xlsx", "xls"}
REGRESSION = {"linear_regression", "tree_ensemble_regression"}
CLASSIFICATION = {"logistic_classification", "tree_ensemble_classification"}


def _assets(profile: dict[str, Any]) -> list[dict[str, Any]]:
    return [a for a in profile.get("assets", []) if isinstance(a, dict)]


def _schema(asset: dict[str, Any]) -> list[dict[str, Any]]:
    return [c for c in asset.get("schema", []) if isinstance(c, dict) and c.get("name")]


def _find_asset(profile: dict[str, Any], proposal: dict[str, Any] | None = None) -> dict[str, Any] | None:
    proposal = proposal or {}
    requested = proposal.get("data_path")
    assets = _assets(profile)
    if requested:
        for a in assets:
            if requested in {a.get("path_or_ref"), a.get("asset_id")}:
                return a
    tabular = [a for a in assets if str(a.get("format", "")).lower().lstrip(".") in TABULAR]
    return tabular[0] if len(tabular) == 1 else None


def _column(asset: dict[str, Any], name: str | None) -> dict[str, Any] | None:
    if not name:
        return None
    return next((c for c in _schema(asset) if c.get("name") == name), None)


def _role_columns(asset: dict[str, Any], roles: set[str]) -> list[str]:
    return [str(c["name"]) for c in _schema(asset) if str(c.get("role", "")).lower() in roles]


def _features(asset: dict[str, Any], target: str) -> list[str]:
    numeric = {"int", "integer", "float", "double", "number", "numeric"}
    return [str(c["name"]) for c in _schema(asset)
            if c.get("name") != target and str(c.get("dtype", "")).lower() in numeric]


def resolve_binding(model_id: str, task: dict[str, Any], profile: dict[str, Any], proposal: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a validated binding or a fail-closed BLOCKED record."""
    proposal = proposal or {}
    asset = _find_asset(profile, proposal)
    if model_id in REGRESSION | CLASSIFICATION | {"time_series_baseline"}:
        if asset is None:
            return {"binding_status": "BLOCKED", "reason": "no unique tabular asset can be selected deterministically"}
        cols = _schema(asset)
        names = {str(c["name"]) for c in cols}
        target = proposal.get("target")
        if target and target not in names:
            return {"binding_status": "BLOCKED", "reason": f"proposed target column not found: {target}"}
        if not target:
            targets = _role_columns(asset, {"target", "response", "label", "dependent"})
            target = targets[0] if len(targets) == 1 else None
        if not target:
            return {"binding_status": "BLOCKED", "reason": "target column is ambiguous or missing semantic role"}
        feats = proposal.get("features")
        if feats is None:
            feats = _features(asset, target)
        if not isinstance(feats, list) or not feats:
            return {"binding_status": "BLOCKED", "reason": "no predictor columns can be bound"}
        missing = [x for x in feats if x not in names]
        if missing:
            return {"binding_status": "BLOCKED", "reason": f"feature columns not found: {missing}"}
        binding = {"data_path": asset.get("path_or_ref"), "target": target, "features": feats,
                   "binding_status": "AUTO_BOUND" if not proposal.get("target") else "PROPOSAL_VALIDATED",
                   "binding_source": "DataProfile.schema.role" if not proposal.get("target") else "LLM_proposal_validated_against_DataProfile"}
        if "seed" in proposal: binding["seed"] = proposal["seed"]
        if model_id == "time_series_baseline":
            time_cols = _role_columns(asset, {"time", "timestamp", "datetime"})
            if len(time_cols) != 1:
                return {"binding_status": "BLOCKED", "reason": "time column is ambiguous or missing semantic role"}
            binding["time_col"] = time_cols[0]
            for k in ("test_horizon", "min_train"):
                if k in proposal: binding[k] = proposal[k]
        return binding

    if model_id == "shortest_path":
        if asset is None:
            return {"binding_status": "BLOCKED", "reason": "no unique tabular network asset"}
        names = {str(c["name"]) for c in _schema(asset)}
        required = {"u", "v", "weight"}
        if not required.issubset(names):
            return {"binding_status": "BLOCKED", "reason": "network asset must expose u, v, weight columns"}
        if proposal.get("source") is None or proposal.get("target") is None:
            return {"binding_status": "BLOCKED", "reason": "source/target nodes are problem-specific and not inferable from DataProfile alone"}
        return {"data_path": asset.get("path_or_ref"), "source": proposal["source"], "target": proposal["target"],
                "directed": bool(proposal.get("directed", False)), "binding_status": "PROPOSAL_VALIDATED"}

    return {"binding_status": "BLOCKED", "reason": f"model {model_id} requires explicit mathematical binding; automatic derivation is not yet safe"}
