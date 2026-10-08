from pathlib import Path
import json

from tools.verification.final_submission_gate import evaluate_final_submission_gate, persist_final_submission_gate


def _write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_v10_required_checks_pass_but_disabled_gates_keep_not_run(tmp_path: Path):
    """Required delivery/evidence checks may all PASS, yet the aggregate decision
    must stay NOT_RUN while any check is NOT_RUN (see
    ../../00_governance/V1_0_FINAL_SUBMISSION_GATE.md section 5).

    Disabling a gate is an explicit "not required" declaration; it is never a way
    to reach an overall PASS. This mirrors the V1.0-V integration fixture.
    """
    run = tmp_path / "run-1"
    _write(run / "result-bundle.json", {"status": "VALIDATED"})
    _write(run / "verification-report.json", {"gate_decision": "PASS"})
    _write(run / "presentation-render-manifest.json", {"gate_decision": "PASS"})
    _write(run / "submission-manifest.json", {"gate_decision": "PASS"})
    (run / "paper.pdf").write_bytes(b"pdf")
    report = evaluate_final_submission_gate(run, required_artifacts=["paper.pdf"], require_paper=True,
        require_cross_artifact_consistency=False, require_reproducibility=False,
        require_environment_closure=False, require_clean_room_execution=False,
        require_execution_replay=False, require_host_materialization=False,
        require_dependency_materialization=False, require_venv_tool_execution=False,
        require_unified_reproducibility=False, require_claim_lineage_conflict=False,
        require_claim_evidence_index=False, require_claim_entity_closure=False,
        require_claim_numeric_trace=False, require_claim_model_trace=False,
        require_model_execution_binding=False, require_paper_consistency_audit=False)
    by_id = {c["check_id"]: c["decision"] for c in report["checks"]}
    for check_id in (
        "F1_RESULT_BUNDLE",
        "F2_VERIFICATION",
        "F3_RENDER_MANIFEST",
        "F4_SUBMISSION_MANIFEST",
        "F5_PAPER_DELIVERABLE",
        "ARTIFACT:paper.pdf",
    ):
        assert by_id[check_id] == "PASS"
    assert report["blocking_failures"] == []
    assert report["gate_decision"] == "NOT_RUN"
    assert "F7_REPRODUCIBILITY" in report["not_run_checks"]
    persist_final_submission_gate(run, report)
    assert (run / "final-submission-gate.json").exists()


def test_v10_fails_missing_required_artifact(tmp_path: Path):
    run = tmp_path / "run-2"
    _write(run / "result-bundle.json", {"status": "VALIDATED"})
    _write(run / "verification-report.json", {"gate_decision": "PASS"})
    _write(run / "presentation-render-manifest.json", {"gate_decision": "PASS"})
    _write(run / "submission-manifest.json", {"gate_decision": "PASS"})
    report = evaluate_final_submission_gate(run, required_artifacts=["paper.pdf"], require_paper=False)
    assert report["gate_decision"] == "FAIL"
    assert "ARTIFACT:paper.pdf" in report["blocking_failures"]


def test_v10_does_not_promote_not_run(tmp_path: Path):
    run = tmp_path / "run-3"
    _write(run / "result-bundle.json", {"status": "VALIDATED"})
    _write(run / "submission-manifest.json", {"gate_decision": "PASS"})
    report = evaluate_final_submission_gate(run, require_paper=False,
        require_cross_artifact_consistency=False, require_reproducibility=False,
        require_environment_closure=False, require_clean_room_execution=False,
        require_execution_replay=False, require_host_materialization=False,
        require_dependency_materialization=False, require_venv_tool_execution=False,
        require_unified_reproducibility=False, require_claim_lineage_conflict=False,
        require_claim_evidence_index=False, require_claim_entity_closure=False,
        require_claim_numeric_trace=False, require_claim_model_trace=False,
        require_model_execution_binding=False, require_paper_consistency_audit=False)
    assert report["gate_decision"] == "NOT_RUN"
    assert "F2_VERIFICATION" in report["not_run_checks"]
