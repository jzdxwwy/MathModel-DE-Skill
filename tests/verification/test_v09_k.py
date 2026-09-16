from tools.verification.paper_evidence_builder import build_paper_evidence
from tools.verification.paper_evidence_gate import gate_paper_evidence


def _lineage():
    return {
        "nodes": [
            {"id": "input:a.csv", "kind": "input", "ref": "a.csv"},
            {"id": "run:r1", "kind": "run", "ref": "runs/r1/run-manifest.json"},
            {"id": "result:r1", "kind": "result", "ref": "runs/r1/result-bundle.json"},
            {"id": "verification:r1", "kind": "verification", "ref": "runs/r1/verification-report.json"},
        ],
        "edges": [],
    }


def test_paper_evidence_passes_with_explicit_lineage():
    pe = build_paper_evidence([{
        "claim_id": "C1",
        "statement": "模型误差为 0.12",
        "evidence_refs": ["runs/r1/result-bundle.json"],
        "verification_refs": ["runs/r1/verification-report.json"],
        "result_refs": ["runs/r1/result-bundle.json"],
        "lineage_refs": ["a.csv"],
    }])
    report = gate_paper_evidence(pe, {"gate_decision": "PASS"}, {"status": "VALIDATED"}, _lineage())
    assert report["gate_decision"] == "PASS"


def test_paper_evidence_blocks_missing_lineage():
    pe = build_paper_evidence([{
        "claim_id": "C1",
        "statement": "模型误差为 0.12",
        "evidence_refs": ["runs/r1/result-bundle.json"],
        "verification_refs": ["runs/r1/verification-report.json"],
        "result_refs": ["runs/r1/result-bundle.json"],
        "lineage_refs": ["missing-source"],
    }])
    report = gate_paper_evidence(pe, {"gate_decision": "PASS"}, {"status": "VALIDATED"}, _lineage())
    assert report["gate_decision"] == "FAIL"


def test_paper_evidence_blocks_unverified_result():
    pe = build_paper_evidence([{
        "claim_id": "C1",
        "statement": "模型误差为 0.12",
        "evidence_refs": ["runs/r1/result-bundle.json"],
        "verification_refs": ["runs/r1/verification-report.json"],
        "result_refs": ["runs/r1/result-bundle.json"],
        "lineage_refs": ["a.csv"],
    }])
    report = gate_paper_evidence(pe, {"gate_decision": "PASS_WITH_WARNINGS"}, {"status": "VALIDATED"}, _lineage())
    assert report["gate_decision"] == "FAIL"
