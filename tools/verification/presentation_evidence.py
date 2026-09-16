"""V0.9-L presentation evidence binding and consistency checks.

Figures, tables and equations are treated as evidence-bearing objects. A
presentation object is publishable only when it points to explicit source,
result, verification and lineage references. This module checks references
and does not infer missing provenance.
"""
from __future__ import annotations

from typing import Any


def _refs_exist(refs: list[Any], available: set[str]) -> bool:
    return bool(refs) and all(str(ref) in available for ref in refs)


def _nodes(lineage: dict[str, Any]) -> set[str]:
    return {str(n.get("id")) for n in lineage.get("nodes", []) if isinstance(n, dict) and n.get("id")}


def _refs(lineage: dict[str, Any]) -> set[str]:
    return {str(n.get("ref")) for n in lineage.get("nodes", []) if isinstance(n, dict) and n.get("ref")}


def verify_presentation_evidence(presentation: dict[str, Any], lineage: dict[str, Any], result: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    node_ids, node_refs = _nodes(lineage), _refs(lineage)
    result_ref = any("result" in r.lower() or "result-bundle" in r.lower() for r in node_refs)
    verification_ref = any("verification" in r.lower() or "verification-report" in r.lower() for r in node_refs)
    source_ref = any(n.get("kind") in {"input", "data"} for n in lineage.get("nodes", []) if isinstance(n, dict))

    for family in ("figures", "tables", "equations"):
        for item in presentation.get(family, []) or []:
            eid = str(item.get("evidence_id", "unknown"))
            source_ok = bool(item.get("source_refs")) and (source_ref or _refs_exist(item.get("source_refs", []), node_refs) or _refs_exist(item.get("source_refs", []), node_ids))
            result_ok = bool(item.get("result_refs")) and (result_ref or _refs_exist(item.get("result_refs", []), node_refs) or _refs_exist(item.get("result_refs", []), node_ids))
            verification_ok = bool(item.get("verification_refs")) and (verification_ref or _refs_exist(item.get("verification_refs", []), node_refs) or _refs_exist(item.get("verification_refs", []), node_ids))
            lineage_ok = bool(item.get("lineage_refs")) and _refs_exist(item.get("lineage_refs", []), node_ids | node_refs)
            status = "PASS" if source_ok and result_ok and verification_ok and lineage_ok else "FAIL"
            checks.append({"check_id": f"V-L01:{family}:{eid}", "status": status, "evidence": f"{family[:-1].capitalize()} has source/result/verification/lineage bindings"})

    if verification.get("gate_decision") != "PASS":
        checks.append({"check_id": "V-L02", "status": "FAIL", "evidence": f"Verification gate={verification.get('gate_decision')}"})
    if result.get("status") not in {"VALIDATED", "FROZEN"}:
        checks.append({"check_id": "V-L03", "status": "FAIL", "evidence": f"ResultBundle status={result.get('status')}"})

    decision = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "PASS"
    return {"artifact_type": "PaperPresentationEvidenceGateReport", "schema_version": "0.9-L", "gate_decision": decision, "checks": checks}
