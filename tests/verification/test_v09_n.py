from pathlib import Path

from tools.verification.presentation_materializer import materialize_presentation
from tools.verification.rendered_consistency import verify_presentation_consistency


def _manifest():
    return {
        "artifact_type": "PresentationDataManifest",
        "schema_version": "0.9-M",
        "items": [
            {
                "evidence_id": "T1",
                "kind": "table",
                "run_id": "run-1",
                "render_ref": "table-1",
                "bindings": [
                    {"source_ref": "result", "result_ref": "metrics.rmse", "path": "metrics.rmse", "value": 1.25, "tolerance": 1e-8}
                ],
            },
            {
                "evidence_id": "E1",
                "kind": "equation",
                "run_id": "run-1",
                "render_ref": "eq-1",
                "bindings": [
                    {"source_ref": "model", "result_ref": "model_id", "path": "model_id", "value": "linear_regression", "normalized_expression": "y = a + b x"}
                ],
            },
        ],
    }


def _result():
    return {"run_id": "run-1", "model_id": "linear_regression", "metrics": {"rmse": 1.25}}


def test_v09_n_materializes_and_hashes(tmp_path: Path):
    rendered = materialize_presentation(tmp_path, _manifest(), _result())
    assert rendered["gate_decision"] == "PASS"
    assert len(rendered["items"]) == 2
    assert all(len(x["payload_sha256"]) == 64 for x in rendered["items"])
    assert (tmp_path / "runs" / "run-1" / "presentation-render-manifest.json").exists()


def test_v09_n_filters_other_runs(tmp_path: Path):
    manifest = _manifest()
    manifest["items"].append({
        "evidence_id": "OTHER",
        "kind": "table",
        "run_id": "run-2",
        "bindings": [{"source_ref": "result", "result_ref": "metrics.rmse", "path": "metrics.rmse", "value": 9.0}],
    })
    rendered = materialize_presentation(tmp_path, manifest, _result())
    assert rendered["gate_decision"] == "PASS"
    assert {x["evidence_id"] for x in rendered["items"]} == {"T1", "E1"}


def test_v09_n_consistency_failure_blocks_render(tmp_path: Path):
    manifest = _manifest()
    manifest["items"][0]["bindings"][0]["value"] = 2.0
    report = verify_presentation_consistency(manifest, _result())
    assert report["gate_decision"] == "FAIL"
