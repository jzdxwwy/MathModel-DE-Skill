import json
from pathlib import Path
from tools.verification.execution_evidence_unifier import unify
from tools.verification.evidence_unification_gate import evaluate_evidence_unification_gate
from tools.verification.reproducibility_closure import evaluate_reproducibility_closure
def test_unify_and_gate(tmp_path:Path):
 (tmp_path/"result-bundle.json").write_text(json.dumps({"artifact_type":"ResultBundle","status":"VALIDATED","model_id":"m","outputs":[{"name":"x","value":1,"unit":"u"}],"metrics":{}}))
 (tmp_path/"execution-log.json").write_text("{}")
 (tmp_path/"venv-tool-execution-evidence.json").write_text(json.dumps({"status":"EXECUTED","run_id":"r","adapter_id":"a","tool":"m","interpreter":"python","isolation_id":"i","input_hashes":[],"lock_hash":"a"*64,"environment_fingerprint":"b"*64}))
 unify(tmp_path)
 assert evaluate_evidence_unification_gate(tmp_path)["gate_decision"]=="PASS"
def test_reproducibility_closure(tmp_path:Path):
 a=tmp_path/"a";b=tmp_path/"b";a.mkdir();b.mkdir()
 bundle={"artifact_type":"ResultBundle","status":"VALIDATED","model_id":"m","outputs":[{"name":"x","value":1.0,"unit":"u"}],"metrics":{"rmse":2}}
 for p in (a,b):(p/"result-bundle.json").write_text(json.dumps(bundle))
 assert evaluate_reproducibility_closure(a,b)["gate_decision"]=="PASS"
