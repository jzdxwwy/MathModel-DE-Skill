from pathlib import Path
import json

from tools.verification.reproducibility_gate import compare_result_bundles, evaluate_reproducibility_gate


def _bundle(value=1.0):
    return {
        "artifact_type": "ResultBundle", "schema_version": "0.9", "status": "FROZEN",
        "run_id": "run-a", "model_id": "baseline_regression",
        "outputs": [{"name": "prediction", "value": value, "unit": "unit"}],
        "metrics": {"rmse": value},
        "provenance": {"input_refs": ["data.csv"], "code_ref": "code/model.py"}
    }


def test_compare_equal_bundles():
    assert compare_result_bundles(_bundle(), _bundle()) == []


def test_compare_detects_numeric_mismatch():
    mismatches = compare_result_bundles(_bundle(1.0), _bundle(1.1))
    assert mismatches
    assert any(x["kind"] == "output_value" for x in mismatches)


def test_gate_without_rebuild_is_not_run(tmp_path: Path):
    run = tmp_path / "run-a"
    run.mkdir()
    (run / "result-bundle.json").write_text(json.dumps(_bundle()), encoding="utf-8")
    report = evaluate_reproducibility_gate(run)
    assert report["gate_decision"] == "NOT_RUN"


def test_gate_with_rebuild_passes(tmp_path: Path):
    run = tmp_path / "run-a"
    rebuild = tmp_path / "run-b"
    run.mkdir(); rebuild.mkdir()
    (run / "result-bundle.json").write_text(json.dumps(_bundle()), encoding="utf-8")
    (rebuild / "result-bundle.json").write_text(json.dumps(_bundle()), encoding="utf-8")
    report = evaluate_reproducibility_gate(run, rebuild_dir=rebuild)
    assert report["gate_decision"] == "PASS"
