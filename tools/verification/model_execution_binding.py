"""V1.0-T: bind ModelSpec identity to the executed ResultBundle and UE."""
from __future__ import annotations
from pathlib import Path
import hashlib,json

PASS,FAIL,NOT_RUN="PASS","FAIL","NOT_RUN"

def _load(p):
    try:
        x=json.loads(p.read_text(encoding="utf-8")); return x if isinstance(x,dict) else None
    except Exception:return None

def _sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def _find(root,names):
    for n in names:
        for p in (root/n,root/"reference"/"execution"/n,root/"reference"/"modeling"/n,root/"modeling"/n):
            if p.is_file():return p
    return None

def evaluate_model_execution_binding(root):
    root=Path(root)
    rbp=_find(root,["result-bundle.json"]); uep=_find(root,["unified-execution-evidence.json"]); msp=_find(root,["model-spec.json","model-specs.json"])
    if not all((rbp,uep,msp)):
        missing=[n for n,p in (("result-bundle.json",rbp),("unified-execution-evidence.json",uep),("model-spec.json",msp)) if p is None]
        return {"artifact_type":"ModelExecutionBinding","schema_version":"1.0-T","status":"DRAFT","run_id":root.name,"model_id":"","model_spec_ref":str(msp or ""),"model_spec_hash":"","result_bundle_ref":str(rbp or ""),"result_bundle_hash":"","unified_execution_evidence_ref":str(uep or ""),"binding_status":"OPEN","gate_decision":NOT_RUN,"violations":["missing: "+", ".join(missing)]}
    rb,ue,ms=_load(rbp),_load(uep),_load(msp)
    if not all((rb,ue,ms)):
        return {"artifact_type":"ModelExecutionBinding","schema_version":"1.0-T","status":"DRAFT","run_id":root.name,"model_id":"","model_spec_ref":str(msp),"model_spec_hash":"","result_bundle_ref":str(rbp),"result_bundle_hash":"","unified_execution_evidence_ref":str(uep),"binding_status":"FAIL","gate_decision":FAIL,"violations":["invalid JSON"]}
    violations=[]
    mid=str(ms.get("model_id",""))
    if not mid or str(rb.get("model_id",""))!=mid: violations.append("ResultBundle.model_id != ModelSpec.model_id")
    if str(rb.get("run_id",""))!=str(ue.get("run_id","")): violations.append("ResultBundle.run_id != UE.run_id")
    actual_rb_hash=_sha(rbp)
    if str(ue.get("result_bundle_hash",""))!=actual_rb_hash: violations.append("UE.result_bundle_hash != actual ResultBundle hash")
    if str(ue.get("execution_status",""))!="SUCCESS": violations.append("UE execution_status != SUCCESS")
    if str(ue.get("tool_ref",""))=="" or str(rb.get("provenance",{}).get("code_ref",""))=="":
        violations.append("execution/tool provenance incomplete")
    out={"artifact_type":"ModelExecutionBinding","schema_version":"1.0-T","status":"VALIDATED" if not violations else "DRAFT",
         "run_id":str(rb.get("run_id")),"model_id":mid,"model_spec_ref":str(msp),
         "model_spec_hash":_sha(msp),"result_bundle_ref":str(rbp),"result_bundle_hash":actual_rb_hash,
         "unified_execution_evidence_ref":str(uep),"equation_refs":[f"equation:{i}" for i,_ in enumerate(ms.get("equations",[]) or [])],
         "parameter_symbols":[str(p.get("symbol")) for p in ms.get("parameters",[]) or []],
         "binding_status":"BOUND" if not violations else "FAIL","gate_decision":PASS if not violations else FAIL,"violations":violations}
    (root/"model-execution-binding.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    return out
