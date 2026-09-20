"""V1.0-O structural claim-level lineage builder and closure gate."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import json

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"

def _load(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, TypeError):
        return None

def _find(root: Path, name: str) -> Path | None:
    for p in (root / name, root / "paper" / name, root / "reference" / name):
        if p.is_file():
            return p
    return None

def build_claim_lineage(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    pe_path = _find(root, "paper-evidence.json")
    if pe_path is None:
        return {"artifact_type":"ClaimLineage","schema_version":"1.0-O","status":"DRAFT",
                "claims":[],"gate_decision":NOT_RUN,"violations":["paper-evidence.json missing"]}
    pe = _load(pe_path)
    if pe is None:
        return {"artifact_type":"ClaimLineage","schema_version":"1.0-O","status":"DRAFT",
                "claims":[],"gate_decision":FAIL,"violations":["invalid paper-evidence.json"]}

    claims: list[dict[str, Any]] = []
    violations: list[str] = []
    for c in pe.get("claims", []):
        cid = str(c.get("claim_id", ""))
        if not cid:
            violations.append("claim missing claim_id")
            continue
        nodes = [
            {"node_id":f"claim:{cid}","node_type":"CLAIM","ref":cid},
            {"node_id":f"paper-evidence:{cid}","node_type":"PAPER_EVIDENCE",
             "ref":str(pe_path.relative_to(root))}
        ]
        edges = [{"from":f"claim:{cid}","to":f"paper-evidence:{cid}","relation":"supported_by"}]

        for field, typ, relation in (
            ("result_refs","RESULT","derived_from"),
            ("verification_refs","VERIFICATION","verified_by"),
            ("figure_refs","PRESENTATION","presented_as"),
            ("table_refs","PRESENTATION","presented_as"),
            ("equation_refs","PRESENTATION","presented_as"),
        ):
            for ref in c.get(field, []) or []:
                ref = str(ref)
                nid = f"{typ.lower()}:{ref}"
                nodes.append({"node_id":nid,"node_type":typ,"ref":ref})
                edges.append({"from":f"claim:{cid}","to":nid,"relation":relation})

        ue_refs = c.get("unified_execution_evidence_refs", []) or []
        if not ue_refs:
            violations.append(f"{cid}: missing unified_execution_evidence_refs")
        for ref in ue_refs:
            ref = str(ref)
            nid = f"unified:{ref}"
            nodes.append({"node_id":nid,"node_type":"UNIFIED_EXECUTION_EVIDENCE","ref":ref})
            edges.append({"from":f"claim:{cid}","to":nid,"relation":"execution_evidence"})

        claims.append({
            "claim_id":cid,"statement":str(c.get("statement","")),"nodes":nodes,"edges":edges,
            "observations":c.get("observations",[]) or [],
            "figure_refs":c.get("figure_refs",[]) or [],
            "table_refs":c.get("table_refs",[]) or [],
            "equation_refs":c.get("equation_refs",[]) or []
        })

    decision = FAIL if violations else (PASS if claims else NOT_RUN)
    out = {"artifact_type":"ClaimLineage","schema_version":"1.0-O",
           "status":"VALIDATED" if decision == PASS else "DRAFT","run_id":root.name,
           "claims":claims,"gate_decision":decision,"violations":violations}
    (root / "claim-lineage.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return out

def evaluate_claim_lineage_gate(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    p = root / "claim-lineage.json"
    if not p.is_file():
        build_claim_lineage(root)
    if not p.is_file():
        return {"artifact_type":"ClaimLineageGateReport","schema_version":"1.0-O",
                "gate_decision":NOT_RUN,"violations":["claim-lineage.json missing"]}
    data = _load(p)
    if data is None:
        return {"artifact_type":"ClaimLineageGateReport","schema_version":"1.0-O",
                "gate_decision":FAIL,"violations":["invalid claim-lineage.json"]}

    violations = list(data.get("violations", []))
    for c in data.get("claims", []):
        cid = c.get("claim_id")
        if not c.get("statement"):
            violations.append(f"{cid}: empty statement")
        if not c.get("nodes") or not c.get("edges"):
            violations.append(f"{cid}: lineage graph incomplete")
        node_ids = {n.get("node_id") for n in c.get("nodes", [])}
        for e in c.get("edges", []):
            if e.get("from") not in node_ids or e.get("to") not in node_ids:
                violations.append(f"{cid}: dangling lineage edge")

    decision = FAIL if violations else (PASS if data.get("claims") else NOT_RUN)
    return {"artifact_type":"ClaimLineageGateReport","schema_version":"1.0-O",
            "gate_decision":decision,"violations":violations}
