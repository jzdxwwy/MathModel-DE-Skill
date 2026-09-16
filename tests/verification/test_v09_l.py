"""V0.9-L tests for figure/table/equation evidence binding."""
from tools.verification.presentation_evidence import verify_presentation_evidence


def _base():
    lineage = {
        "nodes": [
            {"id": "input:data.csv", "kind": "input", "ref": "data.csv"},
            {"id": "run:r1", "kind": "run", "ref": "runs/r1/run-manifest.json"},
            {"id": "result:r1", "kind": "result", "ref": "runs/r1/result-bundle.json"},
            {"id": "verification:r1", "kind": "verification", "ref": "runs/r1/verification-report.json"},
        ]
    }
    result = {"status": "VALIDATED"}
    verification = {"gate_decision": "PASS"}
    return lineage, result, verification


def test_complete_presentation_binding_passes():
    lineage, result, verification = _base()
    presentation = {
        "artifact_type": "PaperPresentationEvidence",
        "schema_version": "0.9-L",
        "figures": [{"evidence_id": "fig-1", "source_refs": ["data.csv"], "result_refs": ["runs/r1/result-bundle.json"], "verification_refs": ["runs/r1/verification-report.json"], "lineage_refs": ["input:data.csv"]}],
        "tables": [],
        "equations": [],
    }
    report = verify_presentation_evidence(presentation, lineage, result, verification)
    assert report["gate_decision"] == "PASS"


def test_missing_lineage_reference_fails():
    lineage, result, verification = _base()
    presentation = {
        "artifact_type": "PaperPresentationEvidence",
        "schema_version": "0.9-L",
        "figures": [{"evidence_id": "fig-1", "source_refs": ["data.csv"], "result_refs": ["runs/r1/result-bundle.json"], "verification_refs": ["runs/r1/verification-report.json"], "lineage_refs": ["input:missing"]}],
        "tables": [],
        "equations": [],
    }
    report = verify_presentation_evidence(presentation, lineage, result, verification)
    assert report["gate_decision"] == "FAIL"
