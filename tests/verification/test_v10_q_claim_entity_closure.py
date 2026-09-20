import json, hashlib
from pathlib import Path
from tools.verification.claim_entity_closure import evaluate_claim_entity_closure

def _write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False),encoding="utf-8")

def _base(tmp_path):
    _write(tmp_path/"paper-evidence.json",{"artifact_type":"PaperEvidence","schema_version":"0.9-K","status":"FROZEN","claims":[{
      "claim_id":"C1","statement":"RMSE=1.2","result_refs":["output:rmse"],"verification_refs":["check:V1"],
      "lineage_refs":["claim-lineage.json"],"unified_execution_evidence_refs":["reference/execution/unified-execution-evidence.json"]}]})
    _write(tmp_path/"claim-evidence-index.json",{"artifact_type":"ClaimEvidenceIndex","schema_version":"1.0-P","status":"VALIDATED","claims":[{
      "claim_id":"C1","statement":"RMSE=1.2","refs":{"result":["output:rmse"],"verification":["check:V1"],
      "unified_execution_evidence":["reference/execution/unified-execution-evidence.json"]}}]})
    _write(tmp_path/"reference/execution/result-bundle.json",{"artifact_type":"ResultBundle","schema_version":"1.0","status":"FROZEN","run_id":"R1","model_id":"M1",
      "outputs":[{"name":"rmse","value":1.2,"unit":""}],"provenance":{"input_refs":[],"code_ref":"tool"}})
    _write(tmp_path/"reference/verification/verification-report.json",{"artifact_type":"VerificationReport","schema_version":"1.0","status":"FROZEN","run_id":"R1",
      "checks":[{"check_id":"V1","category":"numerical","status":"PASS","evidence":"ok","artifact_ref":"result-bundle.json"}],"gate_decision":"PASS"})
    rb=tmp_path/"reference/execution/result-bundle.json"
    h=hashlib.sha256(rb.read_bytes()).hexdigest()
    _write(tmp_path/"reference/execution/unified-execution-evidence.json",{"artifact_type":"UnifiedExecutionEvidence","schema_version":"1.0-L","execution_id":"E1","run_id":"R1",
      "execution_status":"SUCCESS","adapter_id":"a","isolation_id":"i","tool_ref":"tool","interpreter":"python","input_hashes":[],
      "lock_hash":"0"*64,"environment_fingerprint":"1"*64,"execution_log_hash":"2"*64,"result_bundle_hash":h,
      "source_evidence":["venv-tool-execution-evidence.json"]})
def test_q_closure_pass(tmp_path):
    _base(tmp_path); assert evaluate_claim_entity_closure(tmp_path)["gate_decision"]=="PASS"
def test_q_unresolved_result_fails(tmp_path):
    _base(tmp_path)
    p=tmp_path/"claim-evidence-index.json"; d=json.loads(p.read_text()); d["claims"][0]["refs"]["result"]=["output:not_here"]; _write(p,d)
    assert evaluate_claim_entity_closure(tmp_path)["gate_decision"]=="FAIL"
def test_q_bad_verification_fails(tmp_path):
    _base(tmp_path)
    p=tmp_path/"reference/verification/verification-report.json"; d=json.loads(p.read_text()); d["checks"][0]["status"]="FAIL"; d["gate_decision"]="FAIL"; _write(p,d)
    assert evaluate_claim_entity_closure(tmp_path)["gate_decision"]=="FAIL"
