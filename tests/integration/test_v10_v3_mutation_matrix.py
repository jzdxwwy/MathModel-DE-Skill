"""V1.0-V3 mutation regression matrix.

These tests verify that publication-core evidence is fail-closed when a
canonical artifact is intentionally modified.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.verification.final_submission_gate import evaluate_final_submission_gate
from tests.integration.test_v10_v2_final_gate_fixture import build_fixture, write_json


def _gate(run: Path) -> dict:
    return evaluate_final_submission_gate(
        run,
        require_reproducibility=False,
        require_environment_closure=False,
        require_clean_room_execution=False,
        require_execution_replay=False,
        require_host_materialization=False,
        require_dependency_materialization=False,
        require_venv_tool_execution=False,
        require_unified_reproducibility=False,
    )


def _decision(report: dict, check_id: str) -> str:
    return next(x["decision"] for x in report["checks"] if x["check_id"] == check_id)


def test_v10_v3_mutate_result_value_fails(tmp_path: Path):
    run = build_fixture(tmp_path)
    _gate(run)
    path = run / "reference" / "execution" / "result-bundle.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["outputs"][0]["value"] = 9.9
    write_json(path, obj)
    report = _gate(run)
    assert report["gate_decision"] == "FAIL"
    assert _decision(report, "F22_MODEL_EXECUTION_BINDING") == "FAIL"


def test_v10_v3_mutate_execution_hash_fails(tmp_path: Path):
    run = build_fixture(tmp_path)
    _gate(run)
    path = run / "reference" / "execution" / "unified-execution-evidence.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["result_bundle_hash"] = "e" * 64
    write_json(path, obj)
    report = _gate(run)
    assert report["gate_decision"] == "FAIL"
    assert _decision(report, "F22_MODEL_EXECUTION_BINDING") == "FAIL"


def test_v10_v3_mutate_presentation_value_fails(tmp_path: Path):
    run = build_fixture(tmp_path)
    _gate(run)
    path = run / "presentation-data-manifest.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["items"][0]["bindings"][0]["value"] = 9.9
    write_json(path, obj)
    report = _gate(run)
    assert report["gate_decision"] == "FAIL"
    assert _decision(report, "F23_PAPER_CONSISTENCY_AUDIT") == "FAIL"


def test_v10_v3_mutate_model_identity_fails(tmp_path: Path):
    run = build_fixture(tmp_path)
    _gate(run)
    path = run / "model-spec.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["model_id"] = "model.smoke.other"
    write_json(path, obj)
    report = _gate(run)
    assert report["gate_decision"] == "FAIL"
    assert _decision(report, "F21_CLAIM_MODEL_TRACE") == "FAIL"


def test_v10_v3_mutate_submission_hash_fails(tmp_path: Path):
    run = build_fixture(tmp_path)
    _gate(run)
    path = run / "submission-manifest.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["artifacts"][0]["sha256"] = "f" * 64
    write_json(path, obj)
    report = _gate(run)
    assert report["gate_decision"] == "FAIL"
    assert _decision(report, "F6_CROSS_ARTIFACT") == "FAIL"
