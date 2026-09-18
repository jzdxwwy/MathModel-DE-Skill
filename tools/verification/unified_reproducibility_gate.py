"""V1.0-M reproducibility closure over result and execution identity."""
from __future__ import annotations
import json
from pathlib import Path
from .reproducibility_gate import compare_result_bundles

PASS,FAIL,NOT_RUN="PASS","FAIL","NOT_RUN"

def _load(p:Path):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return None

def evaluate_unified_reproducibility_gate(reference_dir:str|Path,rebuild_dir:str|Path)->dict:
    ref=Path(reference_dir); reb=Path(rebuild_dir)
    ru=_load(ref/"unified-execution-evidence.json"); bu=_load(reb/"unified-execution-evidence.json")
    rr=_load(ref/"result-bundle.json"); br=_load(reb/"result-bundle.json")
    failures=[]
    if not ru or not bu: return {"artifact_type":"UnifiedReproducibilityGateReport","schema_version":"1.0-M","gate_decision":NOT_RUN,"reason":"canonical execution evidence missing"}
    if not rr or not br: return {"artifact_type":"UnifiedReproducibilityGateReport","schema_version":"1.0-M","gate_decision":NOT_RUN,"reason":"ResultBundle missing"}
    for field in ("tool_ref","lock_hash","environment_fingerprint"):
        if ru.get(field)!=bu.get(field): failures.append(field)
    if ru.get("execution_status")!="SUCCESS" or bu.get("execution_status")!="SUCCESS": failures.append("execution_status")
    if ru.get("input_hashes")!=bu.get("input_hashes"): failures.append("input_hashes")
    mismatches=compare_result_bundles(rr,br)
    if mismatches: failures.append("result_bundle")
    return {
      "artifact_type":"UnifiedReproducibilityGateReport","schema_version":"1.0-M",
      "reference_run_id":ru.get("run_id"),"rebuild_run_id":bu.get("run_id"),
      "identity_mismatches":sorted(set(failures)),"result_mismatches":mismatches,
      "gate_decision":FAIL if failures else PASS
    }
