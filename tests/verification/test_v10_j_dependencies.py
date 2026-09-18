from pathlib import Path
import hashlib, json, sys, venv
from tools.runtime.dependency_installer import install_locked_dependencies
from tools.runtime.environment_inventory import collect_inventory
from tools.verification.dependency_materialization_gate import evaluate_dependency_materialization_gate, persist_dependency_evidence

def _lock(packages):
    body={"artifact_type":"DependencyLockManifest","schema_version":"1.0-G","lock_id":"lock-test","adapter_id":"python-venv-test","python":{"implementation":"CPython","version":__import__("platform").python_version()},"packages":packages,"tools":[],"source_files":[]}
    body["fingerprint"]=hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return body

def test_inventory_gate_matches_lock_for_empty_env(tmp_path:Path):
    target=tmp_path/"venv"; venv.EnvBuilder(with_pip=False).create(str(target))
    py=target/("Scripts/python.exe" if sys.platform.startswith("win") else "bin/python")
    inv=collect_inventory(str(py))
    lock=_lock([])
    run=tmp_path/"run"; run.mkdir()
    (run/"environment-inventory.json").write_text(json.dumps(inv),encoding="utf-8")
    evidence={"artifact_type":"DependencyMaterializationEvidence","schema_version":"1.0-J","materialization_id":"j-test","adapter_id":"python-venv-test","status":"INSTALLED","lock_hash":lock["fingerprint"],"interpreter":str(py),"inventory_hash":inv["fingerprint"],"installed_packages":[],"policy":{"allow_network":False,"allow_shell":False,"require_hashes":False},"fingerprint":"0"*64}
    persist_dependency_evidence(evidence,run)
    (run/"lock.json").write_text(json.dumps(lock),encoding="utf-8")
    assert evaluate_dependency_materialization_gate(run,lock_path=run/"lock.json")["gate_decision"]=="PASS"

def test_installer_blocks_missing_wheelhouse(tmp_path:Path):
    target=tmp_path/"venv"; venv.EnvBuilder(with_pip=False).create(str(target))
    py=target/("Scripts/python.exe" if sys.platform.startswith("win") else "bin/python")
    contract={"artifact_type":"DependencyMaterializationContract","schema_version":"1.0-J","materialization_id":"j-test-2","adapter_id":"python-venv-test","venv_dir":str(target),"interpreter":str(py),"lock_hash":"a"*64,"packages":[{"name":"numpy","version":"1.0"}],"policy":{"allow_network":False,"allow_shell":False,"require_hashes":False}}
    result=install_locked_dependencies(contract,output_dir=tmp_path/"run")
    assert result["status"]=="FAILED"
    assert "wheelhouse" in result["reason"]
