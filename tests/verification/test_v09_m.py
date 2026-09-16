from tools.verification.rendered_consistency import verify_presentation_consistency


def test_table_value_consistency_passes():
    manifest = {"artifact_type": "PresentationDataManifest", "schema_version": "0.9-M", "items": [{"evidence_id": "T1", "kind": "table", "bindings": [{"source_ref": "result.metric.rmse", "result_ref": "metrics.rmse", "path": "metrics.rmse", "value": 1.25}]}]}
    result = {"metrics": {"rmse": 1.25}}
    report = verify_presentation_consistency(manifest, result)
    assert report["gate_decision"] == "PASS"


def test_table_value_mismatch_fails():
    manifest = {"artifact_type": "PresentationDataManifest", "schema_version": "0.9-M", "items": [{"evidence_id": "T1", "kind": "table", "bindings": [{"source_ref": "result.metric.rmse", "result_ref": "metrics.rmse", "path": "metrics.rmse", "value": 1.25}]}]}
    result = {"metrics": {"rmse": 1.35}}
    report = verify_presentation_consistency(manifest, result)
    assert report["gate_decision"] == "FAIL"


def test_unresolved_binding_fails():
    manifest = {"artifact_type": "PresentationDataManifest", "schema_version": "0.9-M", "items": [{"evidence_id": "F1", "kind": "figure", "bindings": [{"source_ref": "figure.series", "result_ref": "outputs.series", "path": "outputs.missing"}]}]}
    result = {"outputs": {"series": [1, 2, 3]}}
    report = verify_presentation_consistency(manifest, result)
    assert report["gate_decision"] == "FAIL"
