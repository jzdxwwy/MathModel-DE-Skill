"""V1.0-K gate for registered-tool execution inside Python venv."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
def _hash(p:Path)->str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
def evaluate_venv_tool_execution_gate(run_dir:str|Path)->dict:
 root=Path(run_dir); ep=root/"venv-tool-execution-evidence.json"; rp=root/"result-bundle.json"; lp=root/"execution-log.json"
 if not ep.is_file() or not rp.is_file() or not lp.is_file(): return {"artifact_type":"VenvToolExecutionGateReport","schema_version":"1.0-K","gate_decision":"NOT_RUN","reasons":["missing V1.0-K execution evidence/result/log"]}
 try: e=json.loads(ep.read_text(encoding="utf-8")); r=json.loads(rp.read_text(encoding="utf-8"))
 except Exception as exc: return {"artifact_type":"VenvToolExecutionGateReport","schema_version":"1.0-K","gate_decision":"FAIL","reasons":[f"invalid evidence/result: {exc}"]}
 reasons=[]
 if e.get("status")!="EXECUTED": reasons.append("execution status is not EXECUTED")
 if r.get("status") not in {"VALIDATED","FROZEN"}: reasons.append("ResultBundle is not VALIDATED/FROZEN")
 if e.get("result_bundle_sha256")!=_hash(rp): reasons.append("result bundle hash mismatch")
 if e.get("execution_log_sha256")!=_hash(lp): reasons.append("execution log hash mismatch")
 if not e.get("lock_hash") or not e.get("environment_fingerprint"): reasons.append("lock/environment evidence missing")
 return {"artifact_type":"VenvToolExecutionGateReport","schema_version":"1.0-K","gate_decision":"FAIL" if reasons else "PASS","reasons":reasons}
