import json
from tools.verification.claim_numeric_trace import evaluate_claim_numeric_trace
def w(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d),encoding="utf-8")
def base(tmp):
 w(tmp/"paper-evidence.json",{"claims":[{"claim_id":"C1","statement":"RMSE=1.2","observations":[{"observation_id":"O1","value":1.2,"unit":"","result_ref":"output:rmse"}]}]})
 w(tmp/"claim-evidence-index.json",{"claims":[{"claim_id":"C1","refs":{"result":["output:rmse"]}}]})
 w(tmp/"reference/execution/result-bundle.json",{"status":"FROZEN","run_id":"R1","outputs":[{"name":"rmse","value":1.2,"unit":""}]})
def test_r_match(tmp_path):
 base(tmp_path); assert evaluate_claim_numeric_trace(tmp_path)["gate_decision"]=="PASS"
def test_r_mismatch(tmp_path):
 base(tmp_path);p=tmp_path/"reference/execution/result-bundle.json";d=json.loads(p.read_text());d["outputs"][0]["value"]=1.3;w(p,d);assert evaluate_claim_numeric_trace(tmp_path)["gate_decision"]=="FAIL"
def test_r_does_not_parse_statement(tmp_path):
 base(tmp_path);p=tmp_path/"paper-evidence.json";d=json.loads(p.read_text());d["claims"][0]["observations"]=[];w(p,d);assert evaluate_claim_numeric_trace(tmp_path)["gate_decision"]=="FAIL"
