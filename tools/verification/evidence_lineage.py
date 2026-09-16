"""V0.9-J/L deterministic evidence lineage builder.

Builds a graph connecting inputs, data, models, runs, results, verification,
paper evidence and presentation objects. It records provenance and never
infers unsupported relationships.
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


def build_lineage(run_manifest: dict[str, Any], result: dict[str, Any], verification: dict[str, Any] | None = None, dispatch: dict[str, Any] | None = None, paper_evidence: dict[str, Any] | None = None, presentation: dict[str, Any] | None = None) -> dict[str, Any]:
    run_id = str(run_manifest.get("run_id") or result.get("run_id") or "unknown")
    model_id = str(result.get("model_id") or run_manifest.get("model") or "unknown")
    nodes = [_node(f"run:{run_id}", "run", f"runs/{run_id}/run-manifest.json"), _node(f"result:{run_id}", "result", f"runs/{run_id}/result-bundle.json"), _node(f"model:{model_id}", "model", label=model_id)]
    edges = [_edge(f"model:{model_id}", f"result:{run_id}", "computed_by")]

    for ref in run_manifest.get("inputs", []) or run_manifest.get("input_refs", []) or []:
        if isinstance(ref, str):
            node_id = f"input:{ref}"
            nodes.append(_node(node_id, "input", ref))
            edges.append(_edge(node_id, f"run:{run_id}", "derived_from"))
    for ref in result.get("provenance", {}).get("input_refs", []):
        if isinstance(ref, str):
            node_id = f"input:{ref}"
            if not any(n["id"] == node_id for n in nodes):
                nodes.append(_node(node_id, "input", ref))
            edges.append(_edge(node_id, f"result:{run_id}", "derived_from"))

    if verification:
        vid = f"verification:{run_id}"
        nodes.append(_node(vid, "verification", f"runs/{run_id}/verification-report.json"))
        edges.append(_edge(f"result:{run_id}", vid, "verified_by"))

    if paper_evidence:
        for claim in paper_evidence.get("claims", []) or []:
            cid = str(claim.get("claim_id", "unknown"))
            pid = f"paper_evidence:{cid}"
            nodes.append(_node(pid, "paper_evidence", label=cid))
            edges.append(_edge(f"verification:{run_id}", pid, "cited_by"))
            for ref in claim.get("lineage_refs", []) or []:
                edges.append(_edge(str(ref), pid, "derived_from", str(ref)))

    if presentation:
        for family, kind in (("figures", "figure"), ("tables", "table"), ("equations", "equation")):
            for item in presentation.get(family, []) or []:
                eid = str(item.get("evidence_id", "unknown"))
                pid = f"{kind}:{eid}"
                nodes.append(_node(pid, kind, item.get("render_ref"), item.get("description")))
                for ref in item.get("lineage_refs", []) or []:
                    edges.append(_edge(str(ref), pid, "visualized_as", str(ref)))
                for ref in item.get("result_refs", []) or []:
                    edges.append(_edge(str(ref), pid, "visualized_as", str(ref)))

    return {"artifact_type": "EvidenceLineage", "schema_version": "0.9-L", "nodes": nodes, "edges": edges}
