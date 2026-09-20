"""V1.0-V core integration smoke test.

This test exercises the newly consolidated evidence chain without requiring an
external clean-room host:
ResultBundle -> PaperEvidence/ClaimEvidenceIndex -> ModelTrace ->
ModelExecutionBinding -> Presentation/PaperConsistency.

It deliberately does not claim that the full Final Submission Gate is
publish-ready; external execution/rebuild evidence remains a separate concern.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema

from tools.runtime.result_bundle_builder import build_result_bundle
from tools.verification.claim_model_trace import evaluate_claim_model_trace
from tools.verification.model_execution_binding import evaluate_model_execution_binding
from tools.verification.paper_consistency_audit import evaluate_paper_consistency_audit


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _schema(root: Path, name: str) -> dict:
    return json.loads((root / "artifacts" / "schemas" / name).read_text(encoding="utf-8"))


def test_v10_v_core_chain(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    run = tmp_path / "runs" / "v10-v-smoke"
    execution = run / "reference" / "execution"
    execution.mkdir(parents=True)

    model = {
        "artifact_type": "ModelSpec",
        "schema_version": "1.0",
        "status": "FROZEN",
        "model_id": "model.regression.smoke",
        "task_id": "task.smoke",
        "objective": "predict y",
        "variables": [
            {"symbol": "x", "role": "input", "meaning": "input"},
            {"symbol": "y", "role": "target", "meaning": "target"},
        ],
        "parameters": [
            {"symbol": "a", "meaning": "slope", "value": 2.0, "source": "fit"}
        ],
        "equations": ["y = a*x"],
        "assumptions": ["linear relation"],
        "validation_plan": ["independent recomputation"],
    }
    _write(run / "model-spec.json", model)

    result = build_result_bundle(
        run_id=run.name,
        model_id=model["model_id"],
        tool_ref="tools.python.smoke",
        result={"outputs": [{"name": "slope", "value": 2.0, "unit": "1"}]},
        input_refs=["input.csv#sha256:test"],
    )
    result_path = execution / "result-bundle.json"
    _write(result_path, result)

    ue = {
        "artifact_type": "UnifiedExecutionEvidence",
        "schema_version": "1.0-L",
        "execution_id": "exec-smoke",
        "run_id": run.name,
        "execution_status": "SUCCESS",
        "adapter_id": "HOST-TEST",
        "isolation_id": "test-isolation",
        "tool_ref": "tools.python.smoke",
        "interpreter": "python-test",
        "input_hashes": ["input.csv#sha256:test"],
        "lock_hash": "a" * 64,
        "environment_fingerprint": "b" * 64,
        "execution_log_hash": "c" * 64,
        "result_bundle_hash": _sha(result_path),
        "source_evidence": ["test"],
        "observed_at": "2026-01-01T00:00:00Z",
        "canonical_fingerprint": "d" * 64,
    }
    _write(execution / "unified-execution-evidence.json", ue)

    verification_dir = run / "reference" / "verification"
    _write(
        verification_dir / "verification-report.json",
        {
            "artifact_type": "VerificationReport",
            "gate_decision": "PASS",
            "checks": [{"check_id": "V", "status": "PASS"}],
        },
    )

    _write(
        run / "paper-evidence.json",
        {
            "artifact_type": "PaperEvidence",
            "schema_version": "0.9-K",
            "status": "FROZEN",
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "slope is 2.0",
                    "evidence_refs": ["result:slope"],
                    "verification_refs": ["check:V"],
                    "result_refs": ["output:slope"],
                    "lineage_refs": ["lineage:C1"],
                    "unified_execution_evidence_refs": ["reference/execution/unified-execution-evidence.json"],
                    "observations": [
                        {
                            "observation_id": "O1",
                            "source_ref": "output:slope",
                            "comparison_type": "numeric",
                            "value": 2.0,
                            "unit": "1",
                        }
                    ],
                    "equation_refs": ["EQ1"],
                    "equation_observations": [
                        {
                            "expression": "y = a*x",
                            "model_ref": "equation:0",
                        }
                    ],
                    "parameter_observations": [
                        {"symbol": "a", "value": 2.0, "unit": "1"}
                    ],
                }
            ],
        },
    )

    _write(
        run / "claim-evidence-index.json",
        {
            "artifact_type": "ClaimEvidenceIndex",
            "schema_version": "1.0-P",
            "status": "FROZEN",
            "run_id": run.name,
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "slope is 2.0",
                    "refs": {
                        "paper_evidence": ["paper-evidence.json"],
                        "result": ["output:slope"],
                        "verification": ["check:V"],
                        "presentation": ["FIG1", "EQ1"],
                        "unified_execution_evidence": [
                            "reference/execution/unified-execution-evidence.json"
                        ],
                    },
                }
            ],
        },
    )

    _write(
        run / "presentation-data-manifest.json",
        {
            "artifact_type": "PresentationDataManifest",
            "schema_version": "0.9-M",
            "items": [
                {
                    "evidence_id": "FIG1",
                    "kind": "figure",
                    "bindings": [
                        {
                            "source_ref": "output:slope",
                            "result_ref": "output:slope",
                            "value": 2.0,
                            "tolerance": 1e-8,
                        }
                    ],
                },
                {
                    "evidence_id": "EQ1",
                    "kind": "equation",
                    "bindings": [
                        {
                            "source_ref": "ModelSpec.equations[0]",
                            "result_ref": "output:slope",
                            "value": 2.0,
                            "tolerance": 1e-8,
                            "normalized_expression": "y = a*x",
                            "expression_hash": hashlib.sha256(b"y = a*x").hexdigest(),
                        }
                    ],
                    "model_refs": ["equation:0"],
                },
            ],
        },
    )
    _write(
        run / "paper-manifest.json",
        {
            "artifact_type": "PaperManifest",
            "schema_version": "0.9-N",
            "sections": [
                {
                    "section_id": "S1",
                    "title": "Model",
                    "claim_refs": ["C1"],
                    "figure_refs": ["FIG1"],
                    "equation_refs": ["EQ1"],
                }
            ],
        },
    )

    rb_schema = _schema(repo_root, "result-bundle.schema.json")
    jsonschema.Draft202012Validator(rb_schema).validate(result)

    sm = evaluate_claim_model_trace(run)
    assert sm["gate_decision"] == "PASS"
    jsonschema.Draft202012Validator(_schema(repo_root, "claim-model-trace.schema.json")).validate(sm)

    mt = evaluate_model_execution_binding(run)
    assert mt["gate_decision"] == "PASS"
    jsonschema.Draft202012Validator(_schema(repo_root, "model-execution-binding.schema.json")).validate(mt)

    pu = evaluate_paper_consistency_audit(run)
    assert pu["gate_decision"] == "PASS"
    jsonschema.Draft202012Validator(_schema(repo_root, "paper-consistency-audit.schema.json")).validate(pu)

    # Fail-closed regression: changing the persisted result invalidates the
    # execution binding and the presentation claim.
    result["outputs"][0]["value"] = 2.5
    _write(result_path, result)
    assert evaluate_model_execution_binding(run)["gate_decision"] == "FAIL"
    assert evaluate_paper_consistency_audit(run)["gate_decision"] == "FAIL"
