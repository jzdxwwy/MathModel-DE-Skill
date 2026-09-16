"""V0.9-J evidence lineage builder.

Builds a deterministic graph connecting inputs, data, models, runs, results,
verification reports, figures and paper evidence. It records provenance; it
does not infer unsupported relationships.
"""
from __future__ import annotations

from typing import Any


def _node(node_id: str, kind: str, ref: str | None = None, label: str | None = None) -> dict[str, Any]:
    x = {"id": node_id, "kind": kind}
    if ref:
        x["ref"] = ref
    if label:
        x["label"] = label
    return x


def _edge(src: str, dst: str, relation: str, evidence_ref: str | None = None) -> dict[str, Any]:
    x = {"from": src, "to": dst, "relation": relation}
    if evidence_ref:
        x["evidence_ref"] = evidence_ref
    return x


def build_lineage(run_manifest: dict[str, Any], result: dict[str, Any], verification: dict[str, Any] | None = None, dispatch: dict[str, Any] | None = None) -> dict[str, Any]:
    run_id = str(run_manifest.get("run_id") or result.get("run_id") or "unknown")
    model_id = str(result.get("model_id") or run_manifest.get("model") or "unknown")
    nodes = [_node(f"run:{run_id}", "run", f"runs/{run_id}/run-manifest.json"), _node(f"result:{run_id}", "result", f"runs/{run_id}/result-bundle.json"), _node(f"model:{model_id}", "model", label=model_id)]
    edges = [_edge(f"model:{model_id}", f"result:{run_id}", "computed_by")]

    for ref in run_manifest.get("inputs", []) or run_manifest.get("input_refs", []) or []:
        if not isinstance(ref, str):
            continue
        node_id = f"input:{ref}"
        nodes.append(_node(node_id, "input", ref))
        edges.append(_edge(node_id, f"run:{run_id}", "derived_from"))

    for ref in result.get("provenance", {}).get("input_refs", []):
        if not isinstance(ref, str):
            continue
        node_id = f"input:{ref}"
        if not any(n["id"] == node_id for n in nodes):
            nodes.append(_node(node_id, "input", ref))
        edges.append(_edge(node_id, f"result:{run_id}", "derived_from"))

    if verification:
        vid = f"verification:{run_id}"
        nodes.append(_node(vid, "verification", f"runs/{run_id}/verification-report.json"))
        edges.append(_edge(f"result:{run_id}", vid, "verified_by"))

    return {"artifact_type": "EvidenceLineage", "schema_version": "0.9", "nodes": nodes, "edges": edges}
