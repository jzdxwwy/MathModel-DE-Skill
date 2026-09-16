from pathlib import Path
import json

from tools.verification.final_submission_gate import evaluate_final_submission_gate, persist_final_submission_gate


def _write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_v10_passes_complete_evidence(tmp_path: Path):
    run = tmp_path / "run-1"
    _write(run / "result-bundle.json", {"status": "VALIDATED"})
    _write(run / "verification-report.json", {"gate_decision": "PASS"})
    _write(run / "presentation-render-manifest.json", {"gate_decision": "PASS"})
    _write(run / "submission-manifest.json", {"gate_decision": "PASS"})
    (run / "paper.pdf").write_bytes(b"pdf")
    report = evaluate_final_submission_gate(run, required_artifacts=["paper.pdf"], require_paper=True)
    assert report["gate_decision"] == "PASS"
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
    report = evaluate_final_submission_gate(run, require_paper=False)
    assert report["gate_decision"] == "NOT_RUN"
    assert "F2_VERIFICATION" in report["not_run_checks"]
