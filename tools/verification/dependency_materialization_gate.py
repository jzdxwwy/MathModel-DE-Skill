"""V1.0-J gate for locked dependency installation and observed inventory."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any

def _canonical(v:Any)->str:
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),default=str)

def _hash(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def _inventory_matches(lock:dict[str,Any], inventory:dict[str,Any])->list[str]:
    observed={str(x["name"]).lower():str(x["version"]) for x in inventory.get("packages",[])}
    reasons=[]
    for p in lock.get("packages",[]):
        name=str(p["name"]).lower(); expected=str(p["version"])
        if observed.get(name)!=expected: reasons.append(f"{p['name']} expected {expected}, observed {observed.get(name)}")
    return reasons

def evaluate_dependency_materialization_gate(run_dir:str|Path, *, lock_path:str|Path|None=None)->dict[str,Any]:
    root=Path(run_dir)
    ep=root/"dependency-materialization-evidence.json"
    ip=root/"environment-inventory.json"
    if not ep.is_file() or not ip.is_file():
        return {"artifact_type":"DependencyMaterializationGateReport","schema_version":"1.0-J","gate_decision":"NOT_RUN","reasons":["missing dependency evidence or environment inventory"]}
    if lock_path is None:
        for candidate in (root/"dependency-lock.json", root/"artifacts"/"dependency-lock.json", root/"lock.json"):
            if candidate.is_file():
                lock_path = candidate
                break
        if lock_path is None:
            return {"artifact_type":"DependencyMaterializationGateReport","schema_version":"1.0-J","gate_decision":"NOT_RUN","reasons":["missing DependencyLockManifest for authoritative comparison"]}
    try:
        evidence=json.loads(ep.read_text(encoding="utf-8")); inventory=json.loads(ip.read_text(encoding="utf-8"))
        lock=json.loads(Path(lock_path).read_text(encoding="utf-8")) if lock_path else None
    except Exception as exc:
        return {"artifact_type":"DependencyMaterializationGateReport","schema_version":"1.0-J","gate_decision":"FAIL","reasons":[f"invalid evidence/inventory/lock: {exc}"]}
    reasons=[]
    if evidence.get("status")!="INSTALLED": reasons.append("dependency status is not INSTALLED")
    if not lock:
        reasons.append("DependencyLockManifest could not be loaded")
    if evidence.get("lock_hash") and lock:
        body=dict(lock); expected=body.pop("fingerprint",None)
        actual=hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
        if expected!=evidence["lock_hash"] or actual!=evidence["lock_hash"]: reasons.append("dependency lock hash mismatch")
    if evidence.get("inventory_hash")!=inventory.get("fingerprint"): reasons.append("inventory fingerprint mismatch")
    reasons.extend(_inventory_matches(lock,inventory) if lock else [])
    if evidence.get("interpreter")!=inventory.get("interpreter"): reasons.append("interpreter mismatch")
    decision="FAIL" if reasons else "PASS"
    return {"artifact_type":"DependencyMaterializationGateReport","schema_version":"1.0-J","gate_decision":decision,"reasons":reasons}

def persist_dependency_evidence(evidence:dict[str,Any],run_dir:str|Path)->Path:
    root=Path(run_dir); root.mkdir(parents=True,exist_ok=True)
    p=root/"dependency-materialization-evidence.json"
    p.write_text(json.dumps(evidence,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    return p
