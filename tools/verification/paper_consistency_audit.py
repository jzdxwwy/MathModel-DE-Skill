"""V1.0-U structured paper/presentation consistency audit.

Audits only declared structured bindings. It does not OCR or inspect PDF/Word
pixels and never infers values from prose.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,json,math,re

PASS,FAIL,NOT_RUN="PASS","FAIL","NOT_RUN"

def _load(p):
    try:
        x=json.loads(p.read_text(encoding="utf-8")); return x if isinstance(x,dict) else None
    except Exception:return None

def _find(root,names):
    for n in names:
        for p in (root/n,root/"artifacts"/n,root/"paper"/n,root/"reference"/n,
                  root/"reference"/"paper"/n,root/"reference"/"execution"/n,
                  root/"reference"/"verification"/n):
            if p.is_file(): return p
    return None

def _sha_expr(s):
    return hashlib.sha256(" ".join(str(s).split()).encode("utf-8")).hexdigest()

def _num(v):
    if isinstance(v,bool): return None
    if isinstance(v,(int,float)) and math.isfinite(float(v)): return float(v)
    if isinstance(v,str):
        s=v.strip().replace(",","")
        try:
            if re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?",s): return float(s)
        except Exception: pass
    return None

def _get(obj,path):
    cur=obj
    for part in str(path).split("."):
        if isinstance(cur,dict) and part in cur: cur=cur[part]
        elif isinstance(cur,list) and part.isdigit() and int(part)<len(cur): cur=cur[int(part)]
        else: raise KeyError(path)
    return cur

def _result_value(rb,ref):
    r=str(ref)
    if r.startswith("output:"):
        n=r[7:]; hits=[x for x in rb.get("outputs",[]) or [] if isinstance(x,dict) and str(x.get("name"))==n]
        return hits[0].get("value") if len(hits)==1 else None
    if r.startswith("metric:"):
        return (rb.get("metrics") or {}).get(r[7:])
    try:return _get(rb,r)
    except KeyError:return None

def _eq_value(a,b,tol):
    na,nb=_num(a),_num(b)
    if na is not None and nb is not None:return abs(na-nb)<=tol+1e-9*max(1,abs(na),abs(nb))
    return a==b

def evaluate_paper_consistency_audit(root):
    root=Path(root)
    pe_p=_find(root,["paper-evidence.json"]); pm_p=_find(root,["paper-manifest.json"])
    pd_p=_find(root,["presentation-data-manifest.json"]); rb_p=_find(root,["result-bundle.json"])
    ms_p=_find(root,["model-spec.json","model-specs.json"])
    if not all((pe_p,pm_p,pd_p,rb_p)):
        missing=[n for n,p in (("paper-evidence.json",pe_p),("paper-manifest.json",pm_p),("presentation-data-manifest.json",pd_p),("result-bundle.json",rb_p)) if p is None]
        out={"artifact_type":"PaperConsistencyAudit","schema_version":"1.0-U","status":"DRAFT","run_id":root.name,"checks":[],"gate_decision":NOT_RUN,"violations":["missing: "+", ".join(missing)]}
        (root/"paper-consistency-audit.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8"); return out
    pe,pm,pd,rb,ms=map(_load,(pe_p,pm_p,pd_p,rb_p,ms_p))
    if not all((pe,pm,pd,rb)):
        return {"artifact_type":"PaperConsistencyAudit","schema_version":"1.0-U","status":"DRAFT","run_id":root.name,"checks":[],"gate_decision":FAIL,"violations":["invalid JSON"]}
    checks=[]; violations=[]
    claims={str(x.get("claim_id")):x for x in pe.get("claims",[]) or []}
    sections=pm.get("sections",[]) or []
    pitems={str(x.get("evidence_id")):x for x in pd.get("items",[]) or []}
    # U01: PaperManifest claims must resolve and every material claim must be represented.
    referenced={str(r) for s in sections for r in s.get("claim_refs",[]) or []}
    for cid in referenced:
        ok=cid in claims; checks.append({"check_id":f"U01:{cid}","kind":"claim","status":PASS if ok else FAIL,"message":"section claim_ref resolves" if ok else "section claim_ref unresolved","claim_id":cid})
        if not ok: violations.append(f"unresolved claim {cid}")
    for cid in claims:
        ok=cid in referenced; checks.append({"check_id":f"U01C:{cid}","kind":"claim","status":PASS if ok else FAIL,"message":"claim is represented in PaperManifest" if ok else "claim is absent from PaperManifest","claim_id":cid})
        if not ok: violations.append(f"unrepresented claim {cid}")
    # U02: figure/table/equation refs resolve to PresentationDataManifest and kind matches.
    for s in sections:
        for kind,field in (("figure","figure_refs"),("table","table_refs"),("equation","equation_refs")):
            for ref in s.get(field,[]) or []:
                eid=str(ref); item=pitems.get(eid); ok=bool(item and item.get("kind")==kind)
                checks.append({"check_id":f"U02:{s.get('section_id')}:{kind}:{eid}","kind":kind,"status":PASS if ok else FAIL,"message":"presentation reference resolves with matching kind" if ok else "presentation reference unresolved or kind mismatch","evidence_id":eid})
                if not ok: violations.append(f"{kind} ref {eid} unresolved or kind mismatch")
    # U03: every presentation binding resolves to the ResultBundle and declared value matches.
    for eid,item in pitems.items():
        for i,b in enumerate(item.get("bindings",[]) or []):
            ref=b.get("result_ref"); actual=_result_value(rb,ref) if ref else None
            expected=b.get("value")
            ok=bool(ref) and actual is not None
            if ok and expected is not None: ok=_eq_value(actual,expected,float(b.get("tolerance",1e-8)))
            checks.append({"check_id":f"U03:{eid}:{i}","kind":str(item.get("kind","figure")),"status":PASS if ok else FAIL,"message":"presentation binding resolves and declared value matches ResultBundle" if ok else "presentation binding unresolved or value mismatch","evidence_id":eid,"source_ref":str(b.get("source_ref","")),"result_ref":str(ref or ""),"expected":expected,"actual":actual,"tolerance":float(b.get("tolerance",1e-8))})
            if not ok: violations.append(f"presentation binding {eid}:{i} mismatch/unresolved")
    # U04: equation presentation hashes, when declared, must agree; if model_refs exist, resolve ModelSpec equations conservatively.
    if ms:
        equations=ms.get("equations",[]) or []
        for eid,item in pitems.items():
            if item.get("kind")!="equation": continue
            for i,b in enumerate(item.get("bindings",[]) or []):
                expr=b.get("normalized_expression"); eh=b.get("expression_hash")
                if expr is not None and eh:
                    ok=_sha_expr(expr)==str(eh); checks.append({"check_id":f"U04H:{eid}:{i}","kind":"equation","status":PASS if ok else FAIL,"message":"equation expression hash matches" if ok else "equation expression hash mismatch","evidence_id":eid})
                    if not ok: violations.append(f"equation hash mismatch {eid}:{i}")
            for ref in item.get("model_refs",[]) or []:
                ok=False
                if str(ref).startswith("equation:"):
                    try: ok=0<=int(str(ref).split(":",1)[1])<len(equations)
                    except ValueError: ok=False
                checks.append({"check_id":f"U04M:{eid}:{ref}","kind":"equation","status":PASS if ok else FAIL,"message":"ModelSpec equation reference resolves" if ok else "ModelSpec equation reference unresolved","evidence_id":eid})
                if not ok: violations.append(f"unresolved ModelSpec equation {ref}")
    else:
        checks.append({"check_id":"U04M:MODEL_SPEC","kind":"equation","status":NOT_RUN,"message":"ModelSpec unavailable; equation-to-model check not run"})
    # U05: every presentation item is referenced by a paper section.
    section_refs={str(r) for s in sections for field in ("figure_refs","table_refs","equation_refs") for r in s.get(field,[]) or []}
    for eid,item in pitems.items():
        ok=eid in section_refs; checks.append({"check_id":f"U05:{eid}","kind":str(item.get("kind","figure")),"status":PASS if ok else FAIL,"message":"presentation item is referenced by PaperManifest" if ok else "presentation item is orphaned","evidence_id":eid})
        if not ok: violations.append(f"orphan presentation item {eid}")
    decision=FAIL if violations or any(c["status"]==FAIL for c in checks) else (NOT_RUN if any(c["status"]==NOT_RUN for c in checks) else PASS)
    out={"artifact_type":"PaperConsistencyAudit","schema_version":"1.0-U","status":"VALIDATED" if decision==PASS else "DRAFT","run_id":root.name,"checks":checks,"gate_decision":decision,"violations":violations}
    (root/"paper-consistency-audit.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    return out
