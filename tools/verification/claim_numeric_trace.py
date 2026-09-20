"""V1.0-R deterministic numeric trace: Claim observation -> ResultBundle value."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import json, math, re

PASS, FAIL, NOT_RUN = "PASS","FAIL","NOT_RUN"
_NUM_RE=re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")

def _load(p: Path):
    try:
        x=json.loads(p.read_text(encoding="utf-8")); return x if isinstance(x,dict) else None
    except (OSError,ValueError,TypeError): return None

def _find(root: Path,name: str):
    for p in (root/name,root/"paper"/name,root/"reference"/name,root/"reference"/"execution"/name):
        if p.is_file(): return p
    return None

def _num(v):
    if isinstance(v,bool): return None
    if isinstance(v,(int,float)) and math.isfinite(float(v)): return float(v)
    if isinstance(v,str):
        m=_NUM_RE.fullmatch(v.strip().replace(",",""))
        if m:
            try:return float(m.group(0))
            except ValueError:return None
    return None

def _compare(a,b,atol=1e-8,rtol=1e-6):
    if a is None or b is None:return "NOT_NUMERIC"
    return "MATCH" if abs(a-b)<=atol+rtol*abs(b) else "MISMATCH"

def _resolve_numeric_ref(ref,result):
    r=str(ref).strip()
    if r.startswith("output:"):
        n=r[7:]; hits=[o for o in result.get("outputs",[]) or [] if str(o.get("name"))==n]
        if len(hits)==1:return hits[0].get("value"),r
    if r.startswith("metric:"):
        n=r[7:]; metrics=result.get("metrics") or {}
        if n in metrics:return metrics[n],r
    return None,r

def evaluate_claim_numeric_trace(root: str|Path, *, atol=1e-8, rtol=1e-6):
    root=Path(root)
    pe_path=_find(root,"paper-evidence.json"); idx_path=_find(root,"claim-evidence-index.json"); rb_path=_find(root,"result-bundle.json")
    if not all((pe_path,idx_path,rb_path)):
        return {"artifact_type":"ClaimNumericTrace","schema_version":"1.0-R","status":"DRAFT","run_id":root.name,"claims":[],"gate_decision":NOT_RUN,"violations":["required artifact missing"]}
    pe,idx,rb=_load(pe_path),_load(idx_path),_load(rb_path)
    if not all((pe,idx,rb)):
        return {"artifact_type":"ClaimNumericTrace","schema_version":"1.0-R","status":"DRAFT","run_id":root.name,"claims":[],"gate_decision":FAIL,"violations":["invalid JSON"]}
    ib={str(c.get("claim_id")):c for c in idx.get("claims",[])}; pb={str(c.get("claim_id")):c for c in pe.get("claims",[])}
    violations=[]; claims=[]
    for cid,pc in pb.items():
        ic=ib.get(cid)
        if ic is None: violations.append(f"{cid}: missing ClaimEvidenceIndex"); continue
        refs=ic.get("refs",{}).get("result",[]) or []
        obs=pc.get("observations",[]) or []
        trace=[] 
        if not obs: claims.append({"claim_id":cid,"observations":[],"trace_status":"OPEN"}); violations.append(f"{cid}: no numeric observations"); continue
        for i,o in enumerate(obs):
            # Only explicit numeric observation fields are accepted; never parse free-form statement text.
            claim_val=o.get("value",o.get("numeric_value"))
            if claim_val is None and isinstance(o.get("claim_value"),(int,float)): claim_val=o["claim_value"]
            ref=o.get("result_ref") or (refs[i] if i<len(refs) else None)
            result_val,rref=_resolve_numeric_ref(ref,rb) if ref else (None,"")
            unit=str(o.get("unit",""))
            result_unit=""
            if ref and str(ref).startswith("output:"):
                n=str(ref)[7:]; hits=[x for x in rb.get("outputs",[]) or [] if str(x.get("name"))==n]
                if len(hits)==1: result_unit=str(hits[0].get("unit",""))
            cmp=_compare(_num(claim_val),_num(result_val),atol,rtol) if result_val is not None else "MISSING"
            if unit and result_unit and unit!=result_unit: cmp="MISMATCH"
            if cmp!="MATCH": violations.append(f"{cid}: numeric observation mismatch for {rref or '<missing>'}")
            trace.append({"observation_id":str(o.get("observation_id",f"{cid}:obs:{i+1}")),"claim_value":claim_val,"result_value":result_val,"unit":unit,"result_ref":rref,"source_path":"ResultBundle","comparison":cmp,"tolerance":{"atol":atol,"rtol":rtol}})
        claims.append({"claim_id":cid,"observations":trace,"trace_status":"CLOSED" if trace and all(x["comparison"]=="MATCH" for x in trace) else "OPEN"})
    decision=FAIL if violations or any(c["trace_status"]!="CLOSED" for c in claims) else (PASS if claims else NOT_RUN)
    out={"artifact_type":"ClaimNumericTrace","schema_version":"1.0-R","status":"VALIDATED" if decision==PASS else "DRAFT","run_id":root.name,"claims":claims,"gate_decision":decision,"violations":violations}
    (root/"claim-numeric-trace.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    return out
