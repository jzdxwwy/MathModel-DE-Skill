"""V1.0-K fixed module entrypoint executor."""
from __future__ import annotations
import hashlib,json,subprocess,uuid
from pathlib import Path
from typing import Any,Callable
def _sha256(p:Path)->str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
def _canon(v:Any)->str: return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),default=str)
class VenvToolExecutor:
 def __init__(self,*,tool_resolver:Callable[[str],str]): self.tool_resolver=tool_resolver
 def execute(self,contract:dict[str,Any],*,project_dir:str|Path,output_dir:str|Path)->dict[str,Any]:
  if contract.get("artifact_type")!="VenvToolExecutionContract" or contract.get("schema_version")!="1.0-K": raise ValueError("invalid V1.0-K contract")
  if contract.get("policy")!={"allow_network":False,"allow_shell":False,"isolation_required":True}: raise PermissionError("V1.0-K policy violation")
  interpreter=Path(str(contract["interpreter"])).resolve()
  if not interpreter.is_file(): raise FileNotFoundError("venv interpreter missing")
  root=Path(project_dir).resolve(); out=Path(output_dir).resolve(); out.mkdir(parents=True,exist_ok=True)
  for item in contract.get("input_hashes",[]):
   p=root/item["path"]
   if not p.is_file() or _sha256(p)!=item["sha256"]: raise ValueError(f"input hash mismatch: {item['path']}")
  module=self.tool_resolver(contract["tool"])
  if not module or module.startswith("-") or any(x in module for x in [" ",";","|","&"]): raise ValueError("invalid host-resolved module")
  payload=(root/contract["payload_path"]).resolve()
  if root not in payload.parents or not payload.is_file(): raise ValueError("invalid payload path")
  isolation_id="venv-"+uuid.uuid4().hex
  proc=subprocess.run([str(interpreter),"-m",module,"--tool",contract["tool"],"--payload",str(payload),"--output",str(out)],shell=False,cwd=str(root),capture_output=True,text=True,check=False)
  log={"run_id":contract["run_id"],"isolation_id":isolation_id,"adapter_id":contract["adapter_id"],"tool":contract["tool"],"interpreter":str(interpreter),"input_hashes":contract.get("input_hashes",[]),"lock_hash":contract["lock_hash"],"environment_fingerprint":contract["environment_fingerprint"],"returncode":proc.returncode,"stdout_tail":proc.stdout[-4000:],"stderr_tail":proc.stderr[-4000:]}
  lp=out/"execution-log.json"; lp.write_text(json.dumps(log,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
  rp=out/"result-bundle.json"; status="EXECUTED" if proc.returncode==0 and rp.is_file() else "FAILED"
  evidence={"artifact_type":"VenvToolExecutionEvidence","schema_version":"1.0-K","run_id":contract["run_id"],"status":status,"adapter_id":contract["adapter_id"],"tool":contract["tool"],"interpreter":str(interpreter),"isolation_id":isolation_id,"input_hashes":contract.get("input_hashes",[]),"lock_hash":contract["lock_hash"],"environment_fingerprint":contract["environment_fingerprint"],"result_bundle_sha256":_sha256(rp) if rp.is_file() else "0"*64,"execution_log_sha256":_sha256(lp)}
  evidence["fingerprint"]=hashlib.sha256(_canon(evidence).encode()).hexdigest()
  (out/"venv-tool-execution-evidence.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
  return evidence
