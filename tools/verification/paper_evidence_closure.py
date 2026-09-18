"""V1.0-N: enforce UnifiedExecutionEvidence as the sole execution source for paper artifacts."""
from __future__ import annotations
import json
from pathlib import Path

PASS,FAIL,NOT_RUN="PASS","FAIL","NOT_RUN"

def _read(p):
    try:
        v=json.loads(p.read_text(encoding="utf-8"))
        return v if isinstance(v,dict) else None
    except Exception:
        return None

def _canonical_execution_dir(root:Path)->Path:
    p=root/"reference"/"execution"
    return p if p.is_dir() else root

def evaluate_paper_evidence_closure(run_dir:str|Path)->dict:
    root=Path(run_dir)
    execution=_canonical_execution_dir(root)
    ue=_read(execution/"unified-execution-evidence.json")
    pe=_read(root/"paper-evidence.json") or _read(root/"paper"/"paper-evidence.json")
    if ue is None or pe is None:
        return {"artifact_type":"SubmissionEvidenceClosure","schema_version":"1.0-N",
                "gate_decision":NOT_RUN,"checked_refs":[],"violations":[{"reason":"canonical execution evidence or paper evidence missing"}]}
    violations=[]; checked=[]
    ue_ref="execution/unified-execution-evidence.json"
    checked.append(ue_ref)
    claims=pe.get("claims",[]) if isinstance(pe.get("claims",[]),list) else []
    for claim in claims:
        refs=claim.get("unified_execution_evidence_refs",[])
        if not refs:
            violations.append({"claim_id":claim.get("claim_id"),"reason":"missing unified execution evidence reference"})
            continue
        for ref in refs:
            if ref!=ue_ref and not ref.endswith("unified-execution-evidence.json"):
                violations.append({"claim_id":claim.get("claim_id"),"reason":"non-canonical execution evidence reference","ref":ref})
    return {"artifact_type":"SubmissionEvidenceClosure","schema_version":"1.0-N",
            "gate_decision":FAIL if violations else PASS,"checked_refs":checked,"violations":violations}
