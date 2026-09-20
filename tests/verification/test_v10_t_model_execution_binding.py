import json,hashlib
from tools.verification.model_execution_binding import evaluate_model_execution_binding
def w(p,d): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d),encoding="utf-8")
def base(t):
 w(t/"reference/modeling/model-spec.json",{"artifact_type":"ModelSpec","model_id":"M1","equations":["y=a*x"],"parameters":[]})
 w(t/"reference/execution/result-bundle.json",{"artifact_type":"ResultBundle","schema_version":"1.0-M","status":"VALIDATED","run_id":"R1","model_id":"M1","outputs":[],"provenance":{"input_refs":[],"code_ref":"tool:m1"}})
 rb= t/"reference/execution/result-bundle.json"; h=hashlib.sha256(rb.read_bytes()).hexdigest()
 w(t/"reference/execution/unified-execution-evidence.json",{"artifact_type":"UnifiedExecutionEvidence","schema_version":"1.0-L","execution_id":"E1","run_id":"R1","execution_status":"SUCCESS","adapter_id":"A","isolation_id":"I","tool_ref":"tool:m1","interpreter":"python","input_hashes":[],"lock_hash":"0"*64,"environment_fingerprint":"1"*64,"execution_log_hash":"2"*64,"result_bundle_hash":h,"source_evidence":[]})
def test_t_pass(tmp_path): base(tmp_path); assert evaluate_model_execution_binding(tmp_path)["gate_decision"]=="PASS"
def test_t_model_mismatch(tmp_path):
 base(tmp_path);p=tmp_path/"reference/execution/result-bundle.json";d=json.loads(p.read_text());d["model_id"]="M2";w(p,d);assert evaluate_model_execution_binding(tmp_path)["gate_decision"]=="FAIL"
