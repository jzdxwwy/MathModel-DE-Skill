from pathlib import Path
import hashlib,json,sys,venv
from tools.runtime.venv_tool_executor import VenvToolExecutor
def test_fixed_entrypoint_executes_registered_tool(tmp_path:Path):
 target=tmp_path/"venv"; venv.EnvBuilder(with_pip=False).create(str(target)); py=target/("Scripts/python.exe" if sys.platform.startswith("win") else "bin/python")
 payload=tmp_path/"payload.json"; payload.write_text(json.dumps({"run_id":"k-test","model_id":"echo","outputs":[{"name":"x","value":3,"unit":"u"}]}),encoding="utf-8")
 contract={"artifact_type":"VenvToolExecutionContract","schema_version":"1.0-K","run_id":"k-test","adapter_id":"python-venv-test","tool":"echo","interpreter":str(py),"input_hashes":[{"path":"payload.json","sha256":hashlib.sha256(payload.read_bytes()).hexdigest()}],"lock_hash":"a"*64,"environment_fingerprint":"b"*64,"payload_path":"payload.json","policy":{"allow_network":False,"allow_shell":False,"isolation_required":True}}
 result=VenvToolExecutor(tool_resolver=lambda _: "tools.runtime.venv_tool_entrypoint").execute(contract,project_dir=tmp_path,output_dir=tmp_path/"run")
 assert result["status"]=="EXECUTED"
