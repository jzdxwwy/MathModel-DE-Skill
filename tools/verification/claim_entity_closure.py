"""V1.0-Q Claim -> Result -> Verification -> UnifiedExecutionEvidence entity closure."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"

def _load(p: Path) -> dict[str, Any] | None:
    try:
        x=json.loads(p.read_text(encoding="utf-8"))
        return x if isinstance(x,dict) else None
    except (OSError, ValueError, TypeError):
        return None

def _find(root: Path, name: str) -> Path | None:
    candidates=(root/name, root/"paper"/name, root/"reference"/name,
                root/"reference"/"verification"/name, root/"reference"/"execution"/name)
    for p in candidates:
        if p.is_file(): return p
    return None

def _sha256(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def _resolve_result(ref: str, result: dict[str,Any], result_path: Path) -> dict[str,Any]:
    r=str(ref).strip()
    outputs=result.get("outputs") or []
    metrics=result.get("metrics") or {}
    artifacts=result.get("artifacts") or []
    # Explicit refs are preferred. Bare names are accepted only when unique.
    if r.startswith("output:"):
        name=r[7:]
        hits=[o for o in outputs if str(o.get("name"))==name]
        return {"ref":r,"resolved":len(hits)==1,"kind":"output",
                **({"name":name,"value":hits[0].get("value"),"unit":hits[0].get("unit",""),
                    "source_ref":hits[0].get("source_ref","")} if len(hits)==1 else {})}
    if r.startswith("metric:"):
        name=r[7:]
        ok=name in metrics
        return {"ref":r,"resolved":ok,"kind":"metric",**({"name":name,"value":metrics[name]} if ok else {})}
    if r.startswith("artifact:"):
        path=r[9:]
        hits=[a for a in artifacts if str(a.get("path"))==path]
        return {"ref":r,"resolved":len(hits)==1,"kind":"artifact",**({"name":path,"source_ref":path} if len(hits)==1 else {})}
    if r in {str(result_path), result_path.name, "result-bundle.json"}:
        return {"ref":r,"resolved":True,"kind":"result_bundle"}
    hits=[o for o in outputs if str(o.get("name"))==r]
    if len(hits)==1:
        return {"ref":r,"resolved":True,"kind":"output","name":r,
                "value":hits[0].get("value"),"unit":hits[0].get("unit",""),
                "source_ref":hits[0].get("source_ref","")}
    return {"ref":r,"resolved":False,"kind":"unknown"}

def _resolve_verification(ref: str, verification: dict[str,Any]) -> dict[str,Any]:
    r=str(ref).strip()
    checks=verification.get("checks") or []
    if r in {"verification-report.json"}:
        return {"ref":r,"resolved":True,"status":verification.get("gate_decision",""),"check_id":""}
    # Accept check_id or explicit check:<id>; a check must be PASS.
    cid=r[6:] if r.startswith("check:") else r
    hits=[c for c in checks if str(c.get("check_id"))==cid]
    if len(hits)!=1:
        return {"ref":r,"resolved":False,"status":"MISSING","check_id":cid}
    c=hits[0]
    return {"ref":r,"resolved":c.get("status")=="PASS","status":str(c.get("status","")),
            "check_id":cid,"artifact_ref":str(c.get("artifact_ref",""))}

def evaluate_claim_entity_closure(root: str|Path) -> dict[str,Any]:
    root=Path(root)
    idx=_find(root,"claim-evidence-index.json")
    pe_path=_find(root,"paper-evidence.json")
    result_path=_find(root,"result-bundle.json")
    ver_path=_find(root,"verification-report.json")
    ue_path=_find(root,"unified-execution-evidence.json")
    if not all((idx,pe_path,result_path,ver_path,ue_path)):
        missing=[n for n,p in (("claim-evidence-index.json",idx),("paper-evidence.json",pe_path),
          ("result-bundle.json",result_path),("verification-report.json",ver_path),
          ("unified-execution-evidence.json",ue_path)) if p is None]
        return {"artifact_type":"ClaimEntityClosure","schema_version":"1.0-Q","status":"DRAFT",
                "run_id":root.name,"claims":[],"gate_decision":NOT_RUN,"violations":["missing: "+", ".join(missing)]}
    index=_load(idx); pe=_load(pe_path); result=_load(result_path); ver=_load(ver_path); ue=_load(ue_path)
    if not all((index,pe,result,ver,ue)):
        return {"artifact_type":"ClaimEntityClosure","schema_version":"1.0-Q","status":"DRAFT",
                "run_id":root.name,"claims":[],"gate_decision":FAIL,"violations":["one or more closure artifacts invalid JSON"]}
    violations=[]
    if result.get("status") not in {"VALIDATED","FROZEN"}: violations.append("ResultBundle is not VALIDATED/FROZEN")
    if ver.get("gate_decision")=="FAIL": violations.append("VerificationReport gate_decision=FAIL")
    if ue.get("execution_status")!="SUCCESS": violations.append("UnifiedExecutionEvidence execution_status is not SUCCESS")
    if str(ue.get("run_id")) != str(result.get("run_id")): violations.append("UnifiedExecutionEvidence run_id != ResultBundle run_id")
    actual_hash=_sha256(result_path)
    if ue.get("result_bundle_hash") != actual_hash: violations.append("UnifiedExecutionEvidence result_bundle_hash != actual ResultBundle SHA256")
    claims=[]
    index_by={str(c.get("claim_id")):c for c in index.get("claims",[])}
    paper_by={str(c.get("claim_id")):c for c in pe.get("claims",[])}
    for cid, ic in index_by.items():
        pc=paper_by.get(cid)
        if pc is None:
            violations.append(f"{cid}: missing PaperEvidence claim")
            continue
        rb=[]
        for ref in ic.get("refs",{}).get("result",[]):
            b=_resolve_result(ref,result,result_path); rb.append(b)
            if not b["resolved"]: violations.append(f"{cid}: unresolved result ref {ref}")
        vb=[]
        for ref in ic.get("refs",{}).get("verification",[]):
            b=_resolve_verification(ref,ver); vb.append(b)
            if not b["resolved"]: violations.append(f"{cid}: unresolved/non-PASS verification ref {ref}")
        urefs=[str(x) for x in ic.get("refs",{}).get("unified_execution_evidence",[])]
        uok=bool(urefs) and all((u==str(ue_path) or u==ue_path.name or u.endswith("unified-execution-evidence.json")) for u in urefs)
        run_match=str(ue.get("run_id"))==str(result.get("run_id"))
        hash_match=ue.get("result_bundle_hash")==actual_hash
        if not uok: violations.append(f"{cid}: UnifiedExecutionEvidence ref does not resolve to canonical UE")
        if not run_match: violations.append(f"{cid}: execution run mismatch")
        if not hash_match: violations.append(f"{cid}: execution result hash mismatch")
        closed=bool(rb) and all(x["resolved"] for x in rb) and bool(vb) and all(x["resolved"] for x in vb) and uok and run_match and hash_match
        claims.append({"claim_id":cid,"result_bindings":rb,"verification_bindings":vb,
                       "execution_binding":{"refs":urefs,"resolved":uok,"run_match":run_match,"result_hash_match":hash_match},
                       "closure":"CLOSED" if closed else "OPEN"})
    decision=FAIL if violations or any(c["closure"]!="CLOSED" for c in claims) else (PASS if claims else NOT_RUN)
    out={"artifact_type":"ClaimEntityClosure","schema_version":"1.0-Q",
         "status":"VALIDATED" if decision==PASS else "DRAFT","run_id":root.name,
         "claims":claims,"gate_decision":decision,"violations":violations}
    (root/"claim-entity-closure.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    return out
