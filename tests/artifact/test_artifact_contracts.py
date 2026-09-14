"""Smoke tests for core Artifact Contracts."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "artifacts" / "schemas"

SCHEMAS = {
    "ProblemSpec": "problem-spec.schema.json",
    "ProblemMap": "problem-map.schema.json",
    "DataProfile": "data-profile.schema.json",
    "ModelPlan": "model-plan.schema.json",
    "ModelSpec": "model-spec.schema.json",
    "ResultBundle": "result-bundle.schema.json",
    "VerificationReport": "verification-report.schema.json",
    "PaperEvidence": "paper-evidence.schema.json",
    "Traceability": "traceability.schema.json",
    "ModelComparison": "model-comparison.schema.json",
}


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / SCHEMAS[name]).read_text(encoding="utf-8"))


def validate(name: str, payload: dict) -> None:
    errors = list(Draft202012Validator(load_schema(name)).iter_errors(payload))
    assert not errors, "\n".join(error.message for error in errors)


def test_core_contracts_reject_empty_objects():
    for name in SCHEMAS:
        errors = list(Draft202012Validator(load_schema(name)).iter_errors({}))
        assert errors, f"{name} unexpectedly accepts an empty artifact"


def test_traceability_minimal_valid_payload():
    validate("Traceability", {
        "artifact_type": "Traceability",
        "schema_version": "1.0.0",
        "status": "DRAFT",
        "artifact_id": "TRACE-001",
        "lineage": [
            {"relation": "derived_from", "artifact_ref": "DataProfile:DP-001"}
        ],
    })


def test_model_comparison_requires_multiple_candidates():
    payload = {
        "artifact_type": "ModelComparison",
        "schema_version": "1.0.0",
        "status": "DRAFT",
        "task_id": "Q1",
        "candidates": [
            {"model_id": "M1", "name": "baseline", "method": "baseline", "evidence": []},
            {"model_id": "M2", "name": "candidate", "method": "candidate", "evidence": []},
        ],
        "decision": {"selected_model_id": "M2", "reason": "better validation evidence"},
    }
    validate("ModelComparison", payload)
