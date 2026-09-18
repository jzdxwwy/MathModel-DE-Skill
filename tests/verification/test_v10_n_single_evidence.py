import json
from pathlib import Path
from tools.verification.paper_evidence_closure import evaluate_paper_evidence_closure
from tools.verification.submission_evidence_closure import evaluate_submission_evidence_closure

def _ue():
    return {"artifact_type":"UnifiedExecutionEvidence","schema_version":"1.0-M",
            "execution_status":"SUCCESS","run_id":"r","tool_ref":"demo"}

def test_paper_canonical_ref_pass(tmp_path):
    (tmp_path/"unified-execution-evidence.json").write_text(json.dumps(_ue()),encoding="utf-8")
    pe={"claims":[{"claim_id":"c1","unified_execution_evidence_refs":["execution/unified-execution-evidence.json"]}]}
    (tmp_path/"paper-evidence.json").write_text(json.dumps(pe),encoding="utf-8")
    r=evaluate_paper_evidence_closure(tmp_path)
    assert r["gate_decision"]=="PASS"

def test_paper_legacy_ref_fail(tmp_path):
    (tmp_path/"unified-execution-evidence.json").write_text(json.dumps(_ue()),encoding="utf-8")
    pe={"claims":[{"claim_id":"c1","unified_execution_evidence_refs":["execution-evidence.json"]}]}
    (tmp_path/"paper-evidence.json").write_text(json.dumps(pe),encoding="utf-8")
    r=evaluate_paper_evidence_closure(tmp_path)
    assert r["gate_decision"]=="FAIL"

def test_submission_legacy_reference_fail(tmp_path):
    (tmp_path/"unified-execution-evidence.json").write_text(json.dumps(_ue()),encoding="utf-8")
    sm={"execution_evidence_ref":"execution-evidence.json"}
    (tmp_path/"submission-manifest.json").write_text(json.dumps(sm),encoding="utf-8")
    r=evaluate_submission_evidence_closure(tmp_path)
    assert r["gate_decision"]=="FAIL"
