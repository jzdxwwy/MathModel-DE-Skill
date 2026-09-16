"""V0.9-K Evidence Lineage Gate for PaperEvidence.

A claim may enter the paper pipeline only when its evidence references include
an independently verifiable result, a verification report, and an upstream
input/data lineage reference. Missing lineage is a hard block for material
claims.
"""
from __future__ import annotations

from typing import Any


def _has_kind(lineage: dict[str, Any], kind: str) -> bool:
    return any(isinstance(n, dict) and n.get("kind") == kind for n in lineage.get("nodes", []))


def _has_ref(lineage: dict[str, Any], ref: str) -> bool:
    return any(isinstance(n, dict) and n.get("ref") == ref for n in lineage.get("nodes", []))


def gate_paper_evidence(
    paper_evidence: dict[str, Any],
    verification: dict[str, Any],
    result: dict[str, Any],
    lineage: dict[str, Any],
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    verification_ok = verification.get("gate_decision") == "PASS"
    result_ok = result.get("status") in {"VALIDATED", "FROZEN"}
    lineage_ok = _has_kind(lineage, "run") and _has_kind(lineage, "result") and _has_kind(lineage, "verification") and (_has_kind(lineage, "input") or _has_kind(lineage, "data"))
    checks.append({"check_id": "V-K01", "status": "PASS" if verification_ok else "FAIL", "evidence": f"Verification gate={verification.get('gate_decision')}"})
    checks.append({"check_id": "V-K02", "status": "PASS" if result_ok else "FAIL", "evidence": f"ResultBundle status={result.get('status')}"})
    checks.append({"check_id": "V-K03", "status": "PASS" if lineage_ok else "FAIL", "evidence": "Lineage contains upstream input/data, run, result and verification nodes"})

    claims = paper_evidence.get("claims") or []
    if not claims:
        checks.append({"check_id": "V-K04", "status": "FAIL", "evidence": "PaperEvidence contains no claims"})
    for claim in claims:
        cid = str(claim.get("claim_id", "unknown"))
        refs = [str(x) for x in claim.get("evidence_refs", [])]
        has_verification_ref = any("verification" in x.lower() or "verification-report" in x.lower() for x in refs)
        has_result_ref = any("result" in x.lower() or "result-bundle" in x.lower() for x in refs)
        has_upstream_ref = any(_has_ref(lineage, x) for x in refs)
        status = "PASS" if has_verification_ref and has_result_ref and has_upstream_ref else "FAIL"
        checks.append({"check_id": f"V-K05:{cid}", "status": status, "evidence": "Claim references verification, result, and an explicit lineage node"})

    decision = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "PASS"
    return {
        "artifact_type": "PaperEvidenceGateReport",
        "schema_version": "0.9-K",
        "gate_decision": decision,
        "checks": checks,
        "paper_evidence_status": "FROZEN" if decision == "PASS" else "DRAFT",
    }
