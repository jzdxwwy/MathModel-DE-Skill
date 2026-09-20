import json
from tools.verification.paper_consistency_audit import evaluate_paper_consistency_audit
def w(p,d): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d),encoding="utf-8")
def base(t):
 w(t/"paper-evidence.json",{"claims":[{"claim_id":"C1"}]})
 w(t/"paper-manifest.json",{"sections":[{"section_id":"S1","title":"Results","claim_refs":["C1"],"figure_refs":["F1"],"table_refs":[],"equation_refs":[]}]})
 w(t/"presentation-data-manifest.json",{"artifact_type":"PresentationDataManifest","schema_version":"0.9-M","items":[{"evidence_id":"F1","kind":"figure","bindings":[{"source_ref":"plot","result_ref":"output:y","value":10,"tolerance":1e-8}]}]})
 w(t/"result-bundle.json",{"artifact_type":"ResultBundle","run_id":"R1","model_id":"M1","outputs":[{"name":"y","value":10,"unit":"u"}],"provenance":{"input_refs":[],"code_ref":"tool"}})
def test_u_pass(tmp_path): base(tmp_path); assert evaluate_paper_consistency_audit(tmp_path)["gate_decision"]=="PASS"
def test_u_value_mismatch(tmp_path):
 base(tmp_path);p=tmp_path/"presentation-data-manifest.json";d=json.loads(p.read_text());d["items"][0]["bindings"][0]["value"]=11;w(p,d);assert evaluate_paper_consistency_audit(tmp_path)["gate_decision"]=="FAIL"
def test_u_orphan(tmp_path):
 base(tmp_path);p=tmp_path/"presentation-data-manifest.json";d=json.loads(p.read_text());d["items"].append({"evidence_id":"F2","kind":"figure","bindings":[{"source_ref":"plot2","result_ref":"output:y"}]});w(p,d);assert evaluate_paper_consistency_audit(tmp_path)["gate_decision"]=="FAIL"
