"""V1.0-P deterministic Claim Evidence Index builder."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import json

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"

def _load(p: Path):
    try:
        x=json.loads(p.read_text(encoding="utf-8"))
        return x if isinstance(x,dict) else None
    except (OSError,ValueError,TypeError):
        return None

def _find(root: Path,name: str):
    for p in (root/name, root/"paper"/name, root/"reference"/name):
        if p.is_file(): return p
    return None

def _as_list(v):
    return [str(x) for x in (v or [])]

def build_claim_evidence_index(root: str|Path):
    root=Path(root)
    pe_path=_find(root,"paper-evidence.json")
    if pe_path is None:
        return {"artifact_type":"ClaimEvidenceIndex","schema_version":"1.0-P","status":"DRAFT","claims":[],"gate_decision":NOT_RUN,"violations":["paper-evidence.json missing"]}
    pe=_load(pe_path)
    if pe is None:
        return {"artifact_type":"ClaimEvidenceIndex","schema_version":"1.0-P","status":"DRAFT","claims":[],"gate_decision":FAIL,"violations":["invalid paper-evidence.json"]}
    claims=[]
    violations=[]
    for c in pe.get("claims",[]) or []:
        cid=str(c.get("claim_id","")).strip()
        stmt=str(c.get("statement","")).strip()
        if not cid or not stmt:
            violations.append("claim_id or statement missing"); continue
        refs={
          "paper_evidence":[str(pe_path.relative_to(root))],
          "result":_as_list(c.get("result_refs")),
          "verification":_as_list(c.get("verification_refs")),
          "presentation":_as_list(c.get("figure_refs"))+_as_list(c.get("table_refs"))+_as_list(c.get("equation_refs")),
          "unified_execution_evidence":_as_list(c.get("unified_execution_evidence_refs"))
        }
        if not refs["unified_execution_evidence"]:
            violations.append(f"{cid}: missing unified execution evidence")
        claims.append({"claim_id":cid,"statement":stmt,"refs":refs})
    decision=FAIL if violations else (PASS if claims else NOT_RUN)
    out={"artifact_type":"ClaimEvidenceIndex","schema_version":"1.0-P",
         "status":"VALIDATED" if decision==PASS else "DRAFT","run_id":root.name,
         "claims":claims,"gate_decision":decision,"violations":violations}
    (root/"claim-evidence-index.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    return out

def evaluate_claim_evidence_index(root: str|Path):
    root=Path(root); p=root/"claim-evidence-index.json"
    if not p.is_file(): build_claim_evidence_index(root)
    if not p.is_file(): return {"artifact_type":"ClaimEvidenceIndexGateReport","schema_version":"1.0-P","gate_decision":NOT_RUN,"violations":["index missing"]}
    d=_load(p)
    if d is None: return {"artifact_type":"ClaimEvidenceIndexGateReport","schema_version":"1.0-P","gate_decision":FAIL,"violations":["invalid index"]}
    violations=list(d.get("violations",[]))
    for c in d.get("claims",[]):
        refs=c.get("refs",{})
        if not refs.get("unified_execution_evidence"): violations.append(f'{c.get("claim_id")}: no UE ref')
        if not refs.get("result"): violations.append(f'{c.get("claim_id")}: no result ref')
        if not refs.get("verification"): violations.append(f'{c.get("claim_id")}: no verification ref')
    decision=FAIL if violations else (PASS if d.get("claims") else NOT_RUN)
    return {"artifact_type":"ClaimEvidenceIndexGateReport","schema_version":"1.0-P","gate_decision":decision,"violations":violations}
