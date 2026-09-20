"""V1.0-V phase 2: complete publication-core Final Submission fixture.

The fixture exercises F1-F6 and F16-F23 on one canonical run topology.
Environment/rebuild gates F7-F15 are explicitly disabled because they require
external execution evidence. Disabled checks must remain NOT_RUN; they are
never converted to PASS.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.runtime.result_bundle_builder import build_result_bundle
from tools.verification.final_submission_gate import evaluate_final_submission_gate


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_fixture(tmp_path: Path) -> Path:
    run = tmp_path / "runs" / "v10-v2"
    execution = run / "reference" / "execution"
    verification = run / "reference" / "verification"
    execution.mkdir(parents=True)
    verification.mkdir(parents=True)

    model = {
        "artifact_type": "ModelSpec",
        "schema_version": "1.0",
        "status": "FROZEN",
        "model_id": "model.smoke.linear",
        "task_id": "task.smoke",
        "objective": "predict y",
        "variables": [
            {"symbol": "x", "role": "input", "meaning": "input"},
            {"symbol": "y", "role": "target", "meaning": "target"},
        ],
        "parameters": [{"symbol": "a", "meaning": "slope", "value": 2.0, "unit": "1"}],
        "equations": ["y = a*x"],
        "assumptions": ["linear relation"],
        "validation_plan": ["independent recomputation"],
    }
    write_json(run / "model-spec.json", model)

    result = build_result_bundle(
        run_id=run.name,
        model_id=model["model_id"],
        tool_ref="tools.python.smoke",
        result={"outputs": [{"name": "slope", "value": 2.0, "unit": "1", "source_ref": "fit"}]},
        input_refs=["input.csv#sha256:" + "1" * 64],
    )
    result_path = execution / "result-bundle.json"
    write_json(result_path, result)

    ue = {
        "artifact_type": "UnifiedExecutionEvidence",
        "schema_version": "1.0-L",
        "execution_id": "exec-v2",
        "run_id": run.name,
        "execution_status": "SUCCESS",
        "adapter_id": "HOST-TEST",
        "isolation_id": "test-isolation",
        "tool_ref": "tools.python.smoke",
        "interpreter": "python-test",
        "input_hashes": ["input.csv#sha256:" + "1" * 64],
        "lock_hash": "a" * 64,
        "environment_fingerprint": "b" * 64,
        "execution_log_hash": "c" * 64,
        "result_bundle_hash": sha(result_path),
        "source_evidence": ["integration-fixture"],
        "observed_at": "2026-01-01T00:00:00Z",
        "canonical_fingerprint": "d" * 64,
    }
    write_json(execution / "unified-execution-evidence.json", ue)
    (execution / "execution.log").write_text("integration fixture\n", encoding="utf-8")

    write_json(
        verification / "verification-report.json",
        {
            "artifact_type": "VerificationReport",
            "gate_decision": "PASS",
            "checks": [{"check_id": "V2_SMOKE", "status": "PASS", "artifact_ref": "result-bundle.json"}],
        },
    )

    paper_evidence = {
        "artifact_type": "PaperEvidence",
        "schema_version": "0.9-K",
        "status": "FROZEN",
        "claims": [{
            "claim_id": "C1",
            "statement": "模型斜率参数为 2.0。",
            "evidence_refs": ["output:slope"],
            "verification_refs": ["check:V2_SMOKE"],
            "result_refs": ["output:slope"],
            "lineage_refs": ["lineage:C1"],
            "unified_execution_evidence_refs": ["reference/execution/unified-execution-evidence.json"],
            "observations": [{
                "observation_id": "O1",
                "source_ref": "output:slope",
                "comparison_type": "numeric",
                "value": 2.0,
                "unit": "1",
                "atol": 1e-8,
                "rtol": 1e-6,
            }],
            "figure_refs": ["FIG1"],
            "table_refs": ["TAB1"],
            "equation_refs": ["EQ1"],
            "equation_observations": [{"expression": "y = a*x", "model_ref": "equation:0"}],
            "parameter_observations": [{"symbol": "a", "value": 2.0, "unit": "1"}],
            "confidence": "high",
        }],
    }
    write_json(run / "paper-evidence.json", paper_evidence)

    presentation = {
        "artifact_type": "PresentationDataManifest",
        "schema_version": "0.9-M",
        "items": [
            {"evidence_id": "FIG1", "kind": "figure", "render_ref": "render:FIG1",
             "bindings": [{"source_ref": "output:slope", "result_ref": "output:slope", "value": 2.0, "tolerance": 1e-8}]},
            {"evidence_id": "TAB1", "kind": "table", "render_ref": "render:TAB1",
             "bindings": [{"source_ref": "output:slope", "result_ref": "output:slope", "value": 2.0, "tolerance": 1e-8}]},
            {"evidence_id": "EQ1", "kind": "equation", "render_ref": "render:EQ1",
             "bindings": [{"source_ref": "ModelSpec.equations[0]", "result_ref": "output:slope",
                           "value": 2.0, "tolerance": 1e-8,
                           "normalized_expression": "y = a*x",
                           "expression_hash": hashlib.sha256(b"y = a*x").hexdigest()}],
             "model_refs": ["equation:0"]},
        ],
    }
    write_json(run / "presentation-data-manifest.json", presentation)

    paper_manifest = {
        "artifact_type": "PaperManifest",
        "schema_version": "0.9-N",
        "paper_id": "paper-v2",
        "sections": [{
            "section_id": "S1", "title": "模型与结果", "claim_refs": ["C1"],
            "figure_refs": ["FIG1"], "table_refs": ["TAB1"], "equation_refs": ["EQ1"],
            "render_refs": ["render:FIG1", "render:TAB1", "render:EQ1"],
        }],
    }
    write_json(run / "paper-manifest.json", paper_manifest)

    payload_dir = run / "presentation"
    payload_dir.mkdir()
    payloads = {}
    for eid in ("FIG1", "TAB1", "EQ1"):
        p = payload_dir / (eid.lower() + ".payload")
        p.write_text(eid + "\n", encoding="utf-8")
        payloads[eid] = p

    pd_path = run / "presentation-data-manifest.json"
    render = {
        "artifact_type": "PresentationRenderManifest",
        "schema_version": "0.9-N",
        "source_manifest_sha256": sha(pd_path),
        "result_run_id": run.name,
        "result_sha256": sha(result_path),
        "items": [{
            "evidence_id": eid, "kind": kind, "render_ref": "render:" + eid,
            "payload_ref": str(payloads[eid].relative_to(run)),
            "payload_sha256": sha(payloads[eid]),
            "render_input_sha256": sha(pd_path),
        } for eid, kind in (("FIG1", "figure"), ("TAB1", "table"), ("EQ1", "equation"))],
        "errors": [],
        "gate_decision": "PASS",
    }
    write_json(run / "presentation-render-manifest.json", render)

    # Submission manifest indexes only immutable source/render files. The final
    # gate-generated evidence files are intentionally not indexed here, so the
    # fixture can test gate generation without invalidating its own hash index.
    indexed = [
        ("result", execution / "result-bundle.json"),
        ("execution-evidence", execution / "unified-execution-evidence.json"),
        ("verification", verification / "verification-report.json"),
        ("paper-evidence", run / "paper-evidence.json"),
        ("paper-manifest", run / "paper-manifest.json"),
        ("presentation", run / "presentation-data-manifest.json"),
        ("render", run / "presentation-render-manifest.json"),
    ]
    submission = {
        "artifact_type": "SubmissionManifest",
        "schema_version": "0.9-N",
        "run_id": run.name,
        "problem_hash": None,
        "attachment_hashes": [],
        "git_commit": None,
        "environment": {"kind": "integration-fixture"},
        "artifacts": [{"kind": kind, "path": str(p.relative_to(run)), "sha256": sha(p)} for kind, p in indexed],
        "paper_manifest_ref": "paper-manifest.json",
        "presentation_manifest_ref": "presentation-data-manifest.json",
        "render_manifest_refs": ["presentation-render-manifest.json"],
        "verification_report_refs": ["reference/verification/verification-report.json"],
        "missing_artifacts": [],
        "gate_decision": "PASS",
    }
    write_json(run / "submission-manifest.json", submission)

    return run


def test_v10_v2_final_gate_core_fixture(tmp_path: Path):
    run = build_fixture(tmp_path)

    report = evaluate_final_submission_gate(
        run,
        require_paper=False,
        require_cross_artifact_consistency=True,
        require_reproducibility=False,
        require_environment_closure=False,
        require_clean_room_execution=False,
        require_execution_replay=False,
        require_host_materialization=False,
        require_dependency_materialization=False,
        require_venv_tool_execution=False,
        require_unified_reproducibility=False,
        require_claim_lineage_conflict=True,
        require_claim_evidence_index=True,
        require_claim_entity_closure=True,
        require_claim_numeric_trace=True,
        require_claim_model_trace=True,
        require_model_execution_binding=True,
        require_paper_consistency_audit=True,
    )

    by_id = {c["check_id"]: c["decision"] for c in report["checks"]}
    core = [
        "F1_RESULT_BUNDLE", "F2_VERIFICATION", "F3_RENDER_MANIFEST",
        "F4_SUBMISSION_MANIFEST", "F6_CROSS_ARTIFACT",
        "F16_SINGLE_EVIDENCE_REFERENCE", "F17_CLAIM_LINEAGE_CONFLICT",
        "F18_CLAIM_EVIDENCE_INDEX", "F19_CLAIM_ENTITY_CLOSURE",
        "F20_CLAIM_NUMERIC_TRACE", "F21_CLAIM_MODEL_TRACE",
        "F22_MODEL_EXECUTION_BINDING", "F23_PAPER_CONSISTENCY_AUDIT",
    ]
    assert all(by_id[x] == "PASS" for x in core)

    # External execution/rebuild evidence is deliberately not fabricated.
    for x in [
        "F7_REPRODUCIBILITY", "F8_ENVIRONMENT_CLOSURE",
        "F9_CLEAN_ROOM_EXECUTION", "F10_EXECUTION_REPLAY",
        "F11_HOST_MATERIALIZATION", "F12_DEPENDENCY_MATERIALIZATION",
        "F13_VENV_TOOL_EXECUTION", "F14_EVIDENCE_UNIFICATION",
        "F15_UNIFIED_REPRODUCIBILITY",
    ]:
        assert by_id[x] == "NOT_RUN"
    assert report["gate_decision"] == "NOT_RUN"


def test_v10_v2_mutated_result_fails_core_gate(tmp_path: Path):
    run = build_fixture(tmp_path)
    # Generate the claim artifacts once through the same gate.
    first = evaluate_final_submission_gate(
        run,
        require_reproducibility=False, require_environment_closure=False,
        require_clean_room_execution=False, require_execution_replay=False,
        require_host_materialization=False, require_dependency_materialization=False,
        require_venv_tool_execution=False, require_unified_reproducibility=False,
    )
    assert first["gate_decision"] == "NOT_RUN"

    result_path = run / "reference" / "execution" / "result-bundle.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["outputs"][0]["value"] = 9.9
    write_json(result_path, result)

    report = evaluate_final_submission_gate(
        run,
        require_reproducibility=False, require_environment_closure=False,
        require_clean_room_execution=False, require_execution_replay=False,
        require_host_materialization=False, require_dependency_materialization=False,
        require_venv_tool_execution=False, require_unified_reproducibility=False,
    )
    by_id = {c["check_id"]: c["decision"] for c in report["checks"]}
    assert by_id["F22_MODEL_EXECUTION_BINDING"] == "FAIL"
    assert by_id["F23_PAPER_CONSISTENCY_AUDIT"] == "FAIL"
