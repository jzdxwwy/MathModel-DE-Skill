from pathlib import Path

from tools.submission.submission_manifest import build_submission_manifest
from tools.writing.paper_manifest_builder import build_paper_manifest
from tools.verification.presentation_materializer import materialize_presentation


def _result():
    return {"run_id": "run-1", "model_id": "linear_regression", "metrics": {"rmse": 1.25}}


def _presentation_manifest():
    return {
        "artifact_type": "PresentationDataManifest",
        "schema_version": "0.9-M",
        "items": [{
            "evidence_id": "T1",
            "kind": "table",
            "run_id": "run-1",
            "render_ref": "table-1",
            "bindings": [{
                "source_ref": "result",
                "result_ref": "metrics.rmse",
                "path": "metrics.rmse",
                "value": 1.25,
            }],
        }],
    }


def test_v09_n_payload_carries_source_and_result_hashes(tmp_path: Path):
    rendered = materialize_presentation(tmp_path, _presentation_manifest(), _result())
    assert rendered["gate_decision"] == "PASS"
    item = rendered["items"][0]
    assert len(item["payload_sha256"]) == 64
    assert item["payload_sha256"] == item["render_input_sha256"]
    payload = tmp_path / item["payload_ref"]
    text = payload.read_text(encoding="utf-8")
    assert "source_manifest_sha256" in text
    assert "result_sha256" in text


def test_v09_n_paper_manifest_is_reference_only():
    manifest = build_paper_manifest([
        {"section_id": "S1", "title": "模型建立", "claim_refs": ["C1"], "figure_refs": ["F1"]}
    ], paper_id="P1")
    assert manifest["artifact_type"] == "PaperManifest"
    assert manifest["sections"][0]["claim_refs"] == ["C1"]
    assert manifest["sections"][0]["figure_refs"] == ["F1"]


def test_v09_n_submission_manifest_hashes_existing_files(tmp_path: Path):
    result_path = tmp_path / "runs" / "run-1" / "result-bundle.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text('{"run_id":"run-1"}\n', encoding="utf-8")
    manifest = build_submission_manifest(
        tmp_path,
        "run-1",
        [("result_bundle", result_path)],
        git_commit="abc123",
        gate_decision="PASS",
    )
    assert manifest["gate_decision"] == "PASS"
    assert len(manifest["artifacts"]) == 1
    assert len(manifest["artifacts"][0]["sha256"]) == 64


def test_v09_n_submission_manifest_fails_on_missing_artifact(tmp_path: Path):
    manifest = build_submission_manifest(
        tmp_path,
        "run-1",
        [("paper", tmp_path / "missing.docx")],
        gate_decision="PASS",
    )
    assert manifest["gate_decision"] == "FAIL"
    assert manifest["missing_artifacts"]
