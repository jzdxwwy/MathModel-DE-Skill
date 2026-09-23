"""V1.0-M canonicalizes K/G/H evidence into the execution directory."""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path

def _read(p):
    try:
        v=json.loads(p.read_text(encoding="utf-8"))
        return v if isinstance(v,dict) else None
    except Exception:
        return None

def _hash(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def _paths(root:Path):
    execution=root/"execution"
    candidates=[execution,root]
    return candidates

def unify(run_dir:str|Path)->dict:
    root=Path(run_dir)
    dirs=_paths(root)
    k=g=h=None
    source=[]
    for d in dirs:
        if not k: k=_read(d/"venv-tool-execution-evidence.json")
        if not g: g=_read(d/"execution-evidence.json")
        if not h: h=_read(d/"execution-replay-result.json")
    if k: source.append("venv-tool-execution-evidence.json")
    if g: source.append("execution-evidence.json")
    if h: source.append("execution-replay-result.json")
    src=k or g or h
    if not src: raise FileNotFoundError("no K/G/H execution evidence")
    execution=root/"execution"
    execution.mkdir(parents=True,exist_ok=True)
    rb=execution/"result-bundle.json"
    log=execution/"execution.log"
    legacy_log=root/"execution-log.json"
    if not rb.is_file(): rb=root/"result-bundle.json"
    if not log.is_file() and legacy_log.is_file(): log=legacy_log
    if not rb.is_file() or not log.is_file(): raise FileNotFoundError("ResultBundle or execution log missing")
    status="SUCCESS" if src.get("status") in {"EXECUTED","SUCCESS"} else src.get("status","FAILED")
    e={"artifact_type":"UnifiedExecutionEvidence","schema_version":"1.0-M","execution_id":str(src.get("execution_id") or src.get("run_id")),"run_id":str(src.get("run_id")),"execution_status":status,"adapter_id":str(src.get("adapter_id")),"isolation_id":str(src.get("isolation_id") or "unknown"),"tool_ref":str(src.get("tool") or src.get("tool_ref")),"interpreter":str(src.get("interpreter") or "unknown"),"input_hashes":src.get("input_hashes",[]),"lock_hash":str(src.get("lock_hash")),"environment_fingerprint":str(src.get("environment_fingerprint")),"execution_log_hash":_hash(log),"result_bundle_hash":_hash(rb),"source_evidence":source,"observed_at":datetime.now(timezone.utc).isoformat()}
    e["canonical_fingerprint"]=hashlib.sha256(json.dumps(e,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    (execution/"unified-execution-evidence.json").write_text(json.dumps(e,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    return e
