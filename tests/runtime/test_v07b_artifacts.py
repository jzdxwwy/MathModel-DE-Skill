"""Offline tests for V0.7-B structured Artifact generation."""
from __future__ import annotations

import json
from pathlib import Path

from tools.runtime.artifact_builder import (
    build_data_profile,
    build_problem_map,
    build_problem_spec,
    persist_artifact,
    validate_artifact,
)


ROOT = Path(__file__).resolve().parents[2]


def test_problem_spec_is_schema_valid():
    problem_input = {"problem": "A traffic planning problem.", "attachments": []}
    output = {
        "artifact_type": "ProblemSpec",
        "schema_version": "0.1",
        "status": "DRAFT",
        "problem_id": "p001",
        "source": {"title": "Traffic planning", "mode": "problem_solving"},
        "tasks": [{"task_id": "Q1", "statement": "Analyze traffic."}],
    }
    artifact, errors = build_problem_spec(ROOT, output, problem_input)
    assert errors == []
    assert artifact["status"] == "VALIDATED"


def test_problem_map_rejects_task_id_mismatch():
    spec = {
        "artifact_type": "ProblemSpec", "schema_version": "0.1", "status": "VALIDATED",
        "problem_id": "p001", "source": {"title": "x", "mode": "problem_solving"},
        "tasks": [{"task_id": "Q1", "statement": "x"}, {"task_id": "Q2", "statement": "y"}],
    }
    output = {
        "artifact_type": "ProblemMap", "schema_version": "0.1", "status": "DRAFT",
        "problem_id": "p001", "tasks": [{"task_id": "Q1", "objective": "x", "inputs": [], "outputs": []}],
    }
    _, errors = build_problem_map(ROOT, output, spec)
    assert any("task_id mismatch" in e for e in errors)


def test_data_profile_preserves_deterministic_asset_facts(tmp_path):
    deterministic = {
        "artifact_type": "DataProfile", "schema_version": "0.1", "status": "DRAFT",
        "assets": [{
            "asset_id": "asset_001", "path_or_ref": "traffic.csv", "format": ".csv",
            "size": {"rows": 100, "columns": 3, "bytes": 1234},
            "schema": [{"name": "time", "dtype": "string"}],
            "quality": {"missing": "0", "duplicates": "bounded", "anomalies": "not profiled"},
        }],
        "data_risks": [], "gate_decision": "PASS",
    }
    proposed = {
        "artifact_type": "DataProfile", "data_risks": ["possible leakage"],
        "assets": [{"asset_id": "asset_001", "size": {"rows": 999999}}],
    }
    artifact, errors = build_data_profile(ROOT, deterministic, proposed)
    assert errors == []
    assert artifact["assets"][0]["size"]["rows"] == 100
    assert "possible leakage" in artifact["data_risks"]
    assert artifact["gate_decision"] == "PASS_WITH_WARNINGS"


def test_persist_artifact(tmp_path):
    artifact = {"artifact_type": "ProblemSpec", "schema_version": "0.1", "status": "DRAFT"}
    path = persist_artifact(tmp_path, "problem-spec", artifact)
    assert json.loads(path.read_text(encoding="utf-8"))["artifact_type"] == "ProblemSpec"
