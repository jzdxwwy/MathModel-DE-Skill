import json
from tools.verification.claim_evidence_index import build_claim_evidence_index, evaluate_claim_evidence_index

def _write(root, claims):
    (root/"paper-evidence.json").write_text(json.dumps({"artifact_type":"PaperEvidence","claims":claims}),encoding="utf-8")

def test_index_requires_result_and_verification_and_ue(tmp_path):
    _write(tmp_path,[{"claim_id":"c1","statement":"x=1","result_refs":["r1"],"verification_refs":["v1"],"unified_execution_evidence_refs":["u1"]}])
    build_claim_evidence_index(tmp_path)
    assert evaluate_claim_evidence_index(tmp_path)["gate_decision"]=="PASS"

def test_index_missing_ue_fails(tmp_path):
    _write(tmp_path,[{"claim_id":"c1","statement":"x=1","result_refs":["r1"],"verification_refs":["v1"]}])
    build_claim_evidence_index(tmp_path)
    assert evaluate_claim_evidence_index(tmp_path)["gate_decision"]=="FAIL"

def test_index_missing_result_fails(tmp_path):
    _write(tmp_path,[{"claim_id":"c1","statement":"x=1","verification_refs":["v1"],"unified_execution_evidence_refs":["u1"]}])
    build_claim_evidence_index(tmp_path)
    assert evaluate_claim_evidence_index(tmp_path)["gate_decision"]=="FAIL"
