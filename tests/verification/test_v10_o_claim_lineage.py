import json
from pathlib import Path
from tools.verification.claim_lineage import build_claim_lineage, evaluate_claim_lineage_gate
from tools.verification.evidence_conflict import evaluate_evidence_conflicts

def _write(root: Path, claims):
    (root / "paper-evidence.json").write_text(
        json.dumps({"artifact_type":"PaperEvidence","schema_version":"0.9-K","status":"FROZEN","claims":claims}),
        encoding="utf-8")

def _claim(**extra):
    c={"claim_id":"c1","statement":"x=1","evidence_refs":["e1"],
       "verification_refs":["v1"],"result_refs":["r1"],"lineage_refs":["l1"]}
    c.update(extra)
    return c

def test_claim_lineage_requires_canonical_execution_evidence(tmp_path):
    _write(tmp_path, [_claim()])
    build_claim_lineage(tmp_path)
    assert evaluate_claim_lineage_gate(tmp_path)["gate_decision"] == "FAIL"

def test_claim_lineage_passes_with_unified_execution_evidence(tmp_path):
    _write(tmp_path, [_claim(unified_execution_evidence_refs=["execution/unified-execution-evidence.json"])])
    build_claim_lineage(tmp_path)
    assert evaluate_claim_lineage_gate(tmp_path)["gate_decision"] == "PASS"

def test_numeric_conflict_fails_closed(tmp_path):
    data={"artifact_type":"ClaimLineage","schema_version":"1.0-O","status":"VALIDATED",
          "claims":[{"claim_id":"c1","statement":"x","nodes":[{"node_id":"c1","node_type":"CLAIM","ref":"c1"}],
                     "edges":[],
                     "observations":[
                       {"observation_id":"a","source_ref":"r1","comparison_type":"numeric","value":10,"unit":"m","atol":0,"rtol":0},
                       {"observation_id":"b","source_ref":"r2","comparison_type":"numeric","value":10.1,"unit":"m","atol":0,"rtol":0}]}]}
    (tmp_path/"claim-lineage.json").write_text(json.dumps(data),encoding="utf-8")
    assert evaluate_evidence_conflicts(tmp_path)["gate_decision"] == "FAIL"

def test_numeric_within_tolerance_passes(tmp_path):
    data={"artifact_type":"ClaimLineage","schema_version":"1.0-O","status":"VALIDATED",
          "claims":[{"claim_id":"c1","statement":"x","nodes":[{"node_id":"c1","node_type":"CLAIM","ref":"c1"}],
                     "edges":[],
                     "observations":[
                       {"observation_id":"a","source_ref":"r1","comparison_type":"numeric","value":10,"unit":"m","atol":0.2,"rtol":0},
                       {"observation_id":"b","source_ref":"r2","comparison_type":"numeric","value":10.1,"unit":"m","atol":0.2,"rtol":0}]}]}
    (tmp_path/"claim-lineage.json").write_text(json.dumps(data),encoding="utf-8")
    assert evaluate_evidence_conflicts(tmp_path)["gate_decision"] == "PASS"

def test_unit_mismatch_fails_closed(tmp_path):
    data={"artifact_type":"ClaimLineage","schema_version":"1.0-O","status":"VALIDATED",
          "claims":[{"claim_id":"c1","statement":"x","nodes":[{"node_id":"c1","node_type":"CLAIM","ref":"c1"}],
                     "edges":[],
                     "observations":[
                       {"observation_id":"a","source_ref":"r1","comparison_type":"numeric","value":10,"unit":"m","atol":0,"rtol":0},
                       {"observation_id":"b","source_ref":"r2","comparison_type":"numeric","value":1000,"unit":"mm","atol":0,"rtol":0}]}]}
    (tmp_path/"claim-lineage.json").write_text(json.dumps(data),encoding="utf-8")
    assert evaluate_evidence_conflicts(tmp_path)["gate_decision"] == "FAIL"
