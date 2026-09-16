"""V0.9-N deterministic PaperManifest builder.

PaperManifest maps paper sections to already materialized PaperEvidence and
presentation artifacts. It does not generate prose and does not invent refs.
"""
from __future__ import annotations

from typing import Any


def build_paper_manifest(sections: list[dict[str, Any]], paper_id: str = "paper") -> dict[str, Any]:
    normalized = []
    for section in sections:
        normalized.append({
            "section_id": str(section["section_id"]),
            "title": str(section["title"]),
            "claim_refs": [str(x) for x in section.get("claim_refs", [])],
            **({"figure_refs": [str(x) for x in section["figure_refs"]]} if section.get("figure_refs") else {}),
            **({"table_refs": [str(x) for x in section["table_refs"]]} if section.get("table_refs") else {}),
            **({"equation_refs": [str(x) for x in section["equation_refs"]]} if section.get("equation_refs") else {}),
            **({"render_refs": [str(x) for x in section["render_refs"]]} if section.get("render_refs") else {}),
        })
    return {
        "artifact_type": "PaperManifest",
        "schema_version": "0.9-N",
        "paper_id": paper_id,
        "sections": normalized,
    }
