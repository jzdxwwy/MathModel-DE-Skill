"""V1.0-N: close Paper/Presentation/Submission references to canonical evidence."""
from __future__ import annotations
import json
from pathlib import Path
PASS,FAIL,NOT_RUN="PASS","FAIL","NOT_RUN"

def _read(p):
    try:
        v=json.loads(p.read_text(encoding="utf-8"))
        return v if isinstance(v,dict) else None
    except Exception:return None

def _first(root,*names):
    for n in names:
        p=root/n
        if p.is_file(): return p
    return None

def evaluate_submission_evidence_closure(run_dir:str|Path)->dict:
    root=Path(run_dir)
    ue=_first(root/"reference"/"execution","unified-execution-evidence.json") or _first(root,"unified-execution-evidence.json")
    if ue is None: return {"artifact_type":"SubmissionEvidenceClosure","schema_version":"1.0-N","gate_decision":NOT_RUN,"checked_refs":[],"violations":[{"reason":"UnifiedExecutionEvidence missing"}]}
    ue_ref=str(ue.relative_to(root)).replace("\\","/")
    violations=[]; checked=[ue_ref]
    sources=[
      ("paper-evidence.json",_first(root,"paper-evidence.json") or _first(root/"paper","paper-evidence.json")),
      ("presentation-data-manifest.json",_first(root,"presentation-data-manifest.json") or _first(root/"presentation","presentation-data-manifest.json")),
      ("paper-manifest.json",_first(root,"paper-manifest.json") or _first(root/"paper","paper-manifest.json")),
      ("submission-manifest.json",_first(root,"submission-manifest.json"))
    ]
    for label,p in sources:
        if p is None: continue
        doc=_read(p)
        if doc is None:
            violations.append({"artifact":label,"reason":"invalid JSON"})
            continue
        checked.append(str(p.relative_to(root)).replace("\\","/"))
        text=json.dumps(doc,ensure_ascii=False)
        legacy=["execution-evidence.json","venv-tool-execution-evidence.json","execution-replay-result.json"]
        for old in legacy:
            if old in text:
                violations.append({"artifact":label,"reason":"legacy execution evidence referenced","ref":old})
        if "unified-execution-evidence" not in text:
            violations.append({"artifact":label,"reason":"canonical UnifiedExecutionEvidence reference missing"})
    return {"artifact_type":"SubmissionEvidenceClosure","schema_version":"1.0-N",
            "gate_decision":FAIL if violations else PASS,"checked_refs":checked,"violations":violations}
