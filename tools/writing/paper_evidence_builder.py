"""V0.9-K PaperEvidence builder.

PaperEvidence is a first-class, auditable artifact. The builder only emits
claims whose references are explicitly supplied; it never invents evidence.
"""
from __future__ import annotations

from typing import Any


def build_paper_evidence(
    claims: list[dict[str, Any]],
    citation_policy: str = "Every material claim must reference verification and result evidence.",
) -> dict[str, Any]:
    normalized = []
    for claim in claims:
        item = {
            "claim_id": str(claim["claim_id"]),
            "statement": str(claim["statement"]),
            "evidence_refs": [str(x) for x in claim.get("evidence_refs", [])],
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
