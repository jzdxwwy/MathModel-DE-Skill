import json
from tools.verification.claim_model_trace import evaluate_claim_model_trace
def w(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d),encoding="utf-8")
def base(tmp):
 w(tmp/"paper-evidence.json",{"claims":[{"claim_id":"C1","model_id":"M1","equation_observations":[{"expression":"y = a x + b","model_ref":"equation:0"}],"parameter_observations":[{"symbol":"a","value":2.0,"unit":""}]}]})
 w(tmp/"claim-evidence-index.json",{"claims":[{"claim_id":"C1","model_id":"M1"}]})
 w(tmp/"reference/modeling/model-spec.json",{"artifact_type":"ModelSpec","model_id":"M1","equations":["y = a x + b"],"parameters":[{"symbol":"a","meaning":"slope","value":2.0,"source":"fit"}]})
def test_s_pass(tmp_path):
 base(tmp_path); assert evaluate_claim_model_trace(tmp_path)["gate_decision"]=="PASS"
def test_s_equation_mismatch(tmp_path):
 base(tmp_path);p=tmp_path/"paper-evidence.json";d=json.loads(p.read_text());d["claims"][0]["equation_observations"][0]["expression"]="y = a*x - b";w(p,d);assert evaluate_claim_model_trace(tmp_path)["gate_decision"]=="FAIL"
def test_s_parameter_mismatch(tmp_path):
 base(tmp_path);p=tmp_path/"paper-evidence.json";d=json.loads(p.read_text());d["claims"][0]["parameter_observations"][0]["value"]=2.1;w(p,d);assert evaluate_claim_model_trace(tmp_path)["gate_decision"]=="FAIL"
