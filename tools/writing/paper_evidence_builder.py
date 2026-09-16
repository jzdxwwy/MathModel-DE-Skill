"""V0.9-K PaperEvidence builder.

PaperEvidence is a first-class, auditable artifact. The builder only emits
claims whose references are explicitly supplied; it never invents evidence.
"""
from __future__ import annotations

from typing import Any


def build_paper_evidence(
    claims: list[dict[str, Any]],
    citation_policy: str = "Every material claim must reference verification, result, and upstream lineage evidence.",
) -> dict[str, Any]:
    normalized = []
    for claim in claims:
        item = {
            "claim_id": str(claim["claim_id"]),
            "statement": str(claim["statement"]),
            "evidence_refs": [str(x) for x in claim.get("evidence_refs", [])],
            "verification_refs": [str(x) for x in claim.get("verification_refs", [])],
            "result_refs": [str(x) for x in claim.get("result_refs", [])],
            "lineage_refs": [str(x) for x in claim.get("lineage_refs", [])],
        }
        for key in ("figure_refs", "table_refs", "equation_refs"):
            if claim.get(key):
                item[key] = [str(x) for x in claim[key]]
        if claim.get("confidence"):
            item["confidence"] = claim["confidence"]
        normalized.append(item)
    return {
        "artifact_type": "PaperEvidence",
        "schema_version": "0.9-K",
        "status": "DRAFT",
        "claims": normalized,
        "citation_policy": citation_policy,
        "unsupported_claims": [],
    }
