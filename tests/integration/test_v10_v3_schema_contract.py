"""V1.0-V3 schema contract regression for the canonical publication fixture."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from tests.integration.test_v10_v2_final_gate_fixture import build_fixture


def _schema(repo_root: Path, name: str) -> dict:
    return json.loads((repo_root / "artifacts" / "schemas" / name).read_text(encoding="utf-8"))


def test_v10_v3_fixture_source_artifacts_match_schemas(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    run = build_fixture(tmp_path)

    pairs = [
        ("model-spec.json", "model-spec.schema.json"),
        ("reference/execution/result-bundle.json", "result-bundle.schema.json"),
        ("reference/execution/unified-execution-evidence.json", "unified-execution-evidence.schema.json"),
        ("paper-evidence.json", "paper-evidence.schema.json"),
        ("presentation-data-manifest.json", "presentation-data-manifest.schema.json"),
        ("presentation-render-manifest.json", "presentation-render-manifest.schema.json"),
        ("paper-manifest.json", "paper-manifest.schema.json"),
        ("submission-manifest.json", "submission-manifest.schema.json"),
    ]

    for rel, schema_name in pairs:
        instance = json.loads((run / rel).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(_schema(repo_root, schema_name)).validate(instance)


def test_v10_v3_generated_claim_and_audit_artifacts_match_schemas(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    run = build_fixture(tmp_path)

    from tools.verification.final_submission_gate import evaluate_final_submission_gate

    evaluate_final_submission_gate(
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

    generated = [
        ("claim-evidence-index.json", "claim-evidence-index.schema.json"),
        ("claim-entity-closure.json", "claim-entity-closure.schema.json"),
        ("claim-numeric-trace.json", "claim-numeric-trace.schema.json"),
        ("claim-model-trace.json", "claim-model-trace.schema.json"),
        ("model-execution-binding.json", "model-execution-binding.schema.json"),
        ("paper-consistency-audit.json", "paper-consistency-audit.schema.json"),
    ]
    for rel, schema_name in generated:
        path = run / rel
        assert path.is_file(), rel
        instance = json.loads(path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(_schema(repo_root, schema_name)).validate(instance)


def test_v10_v3_final_gate_report_matches_schema(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    run = build_fixture(tmp_path)

    from tools.verification.final_submission_gate import evaluate_final_submission_gate

    report = evaluate_final_submission_gate(
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

    jsonschema.Draft202012Validator(
        _schema(repo_root, "final-submission-gate.schema.json")
    ).validate(report)
