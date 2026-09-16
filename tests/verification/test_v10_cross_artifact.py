from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.verification.cross_artifact_consistency import evaluate_cross_artifact_consistency


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path, *, mismatch: bool = False) -> Path:
    root = tmp_path
    run = root / "runs" / "r1"
    run.mkdir(parents=True)
    _write_json(run / "result-bundle.json", {"run_id": "r1", "status": "VALIDATED"})
    _write_json(run / "verification-report.json", {"run_id": "r1", "gate_decision": "PASS"})
    _write_json(run / "paper-evidence.json", {"artifact_type": "PaperEvidence", "claims": [{"claim_id": "C1", "figure_refs": ["F1"]}]})
    _write_json(run / "paper-manifest.json", {"artifact_type": "PaperManifest", "sections": [{"section_id": "S1", "title": "x", "claim_refs": ["C1"], "figure_refs": ["F1"]}]})
    _write_json(root / "artifacts" / "presentation-data-manifest.json", {"items": [{"evidence_id": "F1", "kind": "figure", "bindings": [{"source_ref": "x", "result_ref": "r1.value"}]}]})
    _write_json(run / "presentation-render-manifest.json", {"evidence_ids": ["F1"]})
    payload = root / "paper.pdf"
    payload.write_bytes(b"paper")
    _write_json(run / "submission-manifest.json", {"run_id": "r1", "artifacts": [{"kind": "paper", "path": "paper.pdf", "sha256": _sha(payload) if not mismatch else "0" * 64}]})
    return root


def test_cross_artifact_complete_pass(tmp_path):
    report = evaluate_cross_artifact_consistency(_fixture(tmp_path), "r1")
    assert report["gate_decision"] == "PASS"


def test_cross_artifact_hash_mismatch_fails(tmp_path):
    report = evaluate_cross_artifact_consistency(_fixture(tmp_path, mismatch=True), "r1")
    assert report["gate_decision"] == "FAIL"
    assert any(c["check_id"] == "B07" for c in report["checks"])


def test_cross_artifact_missing_claim_fails(tmp_path):
    root = _fixture(tmp_path)
    path = root / "runs" / "r1" / "paper-manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["sections"][0]["claim_refs"] = ["C404"]
    path.write_text(json.dumps(data), encoding="utf-8")
    report = evaluate_cross_artifact_consistency(root, "r1")
    assert report["gate_decision"] == "FAIL"
