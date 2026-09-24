"""V1.0-L/M gate for canonical execution evidence."""
from __future__ import annotations
import hashlib,json
from pathlib import Path

def _read(p):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return None

def _hash(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def evaluate_evidence_unification_gate(run_dir:str|Path)->dict:
    root=Path(run_dir)
    canonical=root/"execution"/"unified-execution-evidence.json"
    legacy=root/"unified-execution-evidence.json"
    e=_read(canonical) or _read(legacy)
    if not e:
        return {"artifact_type":"EvidenceUnificationGateReport","schema_version":"1.0-L","gate_decision":"NOT_RUN","reasons":["unified evidence missing"]}

    execution=root/"execution"
    rb=execution/"result-bundle.json"
    log=execution/"execution.log"
    if not rb.is_file(): rb=root/"result-bundle.json"
    if not log.is_file(): log=root/"execution-log.json"

    reasons=[]
    if e.get("artifact_type")!="UnifiedExecutionEvidence": reasons.append("invalid unified evidence identity")
    if e.get("schema_version") not in {"1.0-M","1.0-L"}: reasons.append("invalid unified evidence schema")
    if e.get("execution_status")!="SUCCESS": reasons.append("execution not successful")
    if not rb.is_file() or e.get("result_bundle_hash")!=_hash(rb): reasons.append("result bundle hash mismatch")
    if not log.is_file() or e.get("execution_log_hash")!=_hash(log): reasons.append("execution log hash mismatch")
    for key in ("adapter_id","isolation_id","tool_ref","lock_hash","environment_fingerprint"):
        if not e.get(key): reasons.append(key+" missing")

    return {
        "artifact_type":"EvidenceUnificationGateReport",
        "schema_version":"1.0-L",
        "gate_decision":"FAIL" if reasons else "PASS",
        "reasons":reasons,
        "evidence_ref":str(canonical.relative_to(root)) if canonical.is_file() else "unified-execution-evidence.json"
    }
