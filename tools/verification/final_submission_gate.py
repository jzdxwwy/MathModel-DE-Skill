"""V1.0 deterministic Final Submission Gate."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json
from .cross_artifact_consistency import evaluate_cross_artifact_consistency
from .reproducibility_gate import evaluate_reproducibility_gate
from .environment_gate import evaluate_environment_gate
from .execution_evidence_gate import evaluate_execution_evidence_gate
from .execution_replay_gate import evaluate_execution_replay_gate
from .materialization_gate import evaluate_materialization_gate
from .dependency_materialization_gate import evaluate_dependency_materialization_gate
from .venv_tool_execution_gate import evaluate_venv_tool_execution_gate
from .execution_evidence_unifier import unify
from .evidence_unification_gate import evaluate_evidence_unification_gate

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"

def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file(): return None
    try:
        value = json.loads(path.read_text(encoding="utf-8")); return value if isinstance(value, dict) else None
    except (OSError, ValueError, TypeError): return None

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()

def _check(check_id: str, category: str, decision: str, message: str = "", refs: list[str] | None = None) -> dict[str, Any]:
    return {"check_id": check_id, "category": category, "decision": decision, "message": message, "refs": refs or []}

def _gate(checks: list[dict[str, Any]], run_id: str) -> dict[str, Any]:
    failures = [x["check_id"] for x in checks if x["decision"] == FAIL]
    not_run = [x["check_id"] for x in checks if x["decision"] == NOT_RUN]
    decision = FAIL if failures else (NOT_RUN if not_run else PASS)
    return {"artifact_type": "FinalSubmissionGateReport", "schema_version": "1.0", "run_id": run_id,
            "checks": checks, "blocking_failures": failures, "not_run_checks": not_run, "gate_decision": decision}

def evaluate_final_submission_gate(run_dir: str | Path, *, required_artifacts: list[str] | None = None,
    require_paper: bool = False, require_submission_manifest: bool = True,
    require_cross_artifact_consistency: bool = True, require_reproducibility: bool = True,
    require_environment_closure: bool = True, require_clean_room_execution: bool = True,
    require_execution_replay: bool = True, require_host_materialization: bool = True,
    require_dependency_materialization: bool = True, require_venv_tool_execution: bool = True,
    rebuild_dir: str | Path | None = None) -> dict[str, Any]:
    """Evaluate persisted evidence; NOT_RUN never becomes PASS."""
    root = Path(run_dir); run_id = root.name; checks: list[dict[str, Any]] = []
    result = _read_json(root / "result-bundle.json")
    verification = _read_json(root / "verification-report.json")
    render = _read_json(root / "presentation-render-manifest.json")
    submission = _read_json(root / "submission-manifest.json")
    checks.append(_check("F1_RESULT_BUNDLE", "evidence", PASS if result and result.get("status") in {"VALIDATED", "FROZEN"} else FAIL, "ResultBundle must exist and be VALIDATED/FROZEN.", ["result-bundle.json"]))
    if verification is None: checks.append(_check("F2_VERIFICATION", "verification", NOT_RUN, "VerificationReport missing.", ["verification-report.json"]))
    else:
        decision = str(verification.get("gate_decision") or verification.get("decision") or NOT_RUN)
        checks.append(_check("F2_VERIFICATION", "verification", decision if decision in {PASS, FAIL, NOT_RUN} else NOT_RUN, "Verification gate decision.", ["verification-report.json"]))
    if render is None: checks.append(_check("F3_RENDER_MANIFEST", "presentation", NOT_RUN, "PresentationRenderManifest missing.", ["presentation-render-manifest.json"]))
    else:
        decision = str(render.get("gate_decision", NOT_RUN)); checks.append(_check("F3_RENDER_MANIFEST", "presentation", decision if decision in {PASS, FAIL, NOT_RUN} else NOT_RUN, "Presentation render materialization gate.", ["presentation-render-manifest.json"]))
    checks.append(_check("F4_SUBMISSION_MANIFEST", "reproducibility", PASS if submission else (FAIL if require_submission_manifest else NOT_RUN), "SubmissionManifest is required for V1.0." if require_submission_manifest else "SubmissionManifest is optional in this invocation.", ["submission-manifest.json"]))
    if require_cross_artifact_consistency:
        cross = evaluate_cross_artifact_consistency(root.parent.parent, run_id); d = cross.get("gate_decision", NOT_RUN)
        checks.append(_check("F6_CROSS_ARTIFACT", "cross-artifact", d if d in {PASS, FAIL, NOT_RUN} else NOT_RUN, "V1.0-B cross-artifact closure gate.", ["cross-artifact-consistency"]))
    else: checks.append(_check("F6_CROSS_ARTIFACT", "cross-artifact", NOT_RUN, "Cross-artifact consistency was not required by this invocation."))
    if require_reproducibility:
        repro = evaluate_reproducibility_gate(root, rebuild_dir=rebuild_dir); d = repro.get("gate_decision", NOT_RUN)
        checks.append(_check("F7_REPRODUCIBILITY", "reproducibility", d if d in {PASS, FAIL, NOT_RUN} else NOT_RUN, "V1.0-C independent rebuild gate.", ["reproducibility-gate.json"]))
    else: checks.append(_check("F7_REPRODUCIBILITY", "reproducibility", NOT_RUN, "Reproducibility was not required by this invocation."))
    if require_environment_closure:
        env = evaluate_environment_gate(root, rebuild_dir=rebuild_dir); d = env.get("gate_decision", NOT_RUN)
        checks.append(_check("F8_ENVIRONMENT_CLOSURE", "environment", d if d in {PASS, FAIL, NOT_RUN} else NOT_RUN, "V1.0-E environment closure gate.", ["environment-gate.json", "environment-closure.json"]))
    else: checks.append(_check("F8_ENVIRONMENT_CLOSURE", "environment", NOT_RUN, "Environment closure was not required by this invocation."))
    if require_clean_room_execution:
        execution = evaluate_execution_evidence_gate(root, rebuild_dir=rebuild_dir); d = execution.get("gate_decision", NOT_RUN)
        checks.append(_check("F9_CLEAN_ROOM_EXECUTION", "environment", d if d in {PASS, FAIL, NOT_RUN} else NOT_RUN, "V1.0-G trusted-host execution evidence gate.", ["execution-evidence-gate.json", "execution-evidence.json"]))
    else: checks.append(_check("F9_CLEAN_ROOM_EXECUTION", "environment", NOT_RUN, "Clean-room execution evidence was not required by this invocation."))
    replay_root = Path(rebuild_dir) if rebuild_dir else root
    if require_execution_replay:
        replay = evaluate_execution_replay_gate(replay_root); d = replay.get("gate_decision", NOT_RUN)
        checks.append(_check("F10_EXECUTION_REPLAY", "execution", d if d in {PASS, FAIL, NOT_RUN} else NOT_RUN, "V1.0-H controlled execution replay gate.", ["execution-replay-result.json", "execution-log.json", "result-bundle.json"]))
    else: checks.append(_check("F10_EXECUTION_REPLAY", "execution", NOT_RUN, "Execution replay was not required by this invocation."))
    if require_host_materialization:
        material = evaluate_materialization_gate(replay_root); d = material.get("gate_decision", NOT_RUN)
        checks.append(_check("F11_HOST_MATERIALIZATION", "environment", d if d in {PASS, FAIL, NOT_RUN} else NOT_RUN, "V1.0-I concrete Python venv materialization gate.", ["venv-materialization-evidence.json"]))
    else: checks.append(_check("F11_HOST_MATERIALIZATION", "environment", NOT_RUN, "Host materialization was not required by this invocation."))
    if require_dependency_materialization:
        dep = evaluate_dependency_materialization_gate(replay_root, lock_path=(replay_root / "lock.json") if (replay_root / "lock.json").is_file() else None)
        d = dep.get("gate_decision", NOT_RUN)
        checks.append(_check("F12_DEPENDENCY_MATERIALIZATION", "environment", d if d in {PASS, FAIL, NOT_RUN} else NOT_RUN, "V1.0-J locked dependency installation and observed inventory gate.", ["dependency-materialization-evidence.json", "environment-inventory.json"]))
    else: checks.append(_check("F12_DEPENDENCY_MATERIALIZATION", "environment", NOT_RUN, "Dependency materialization was not required by this invocation."))
    if require_venv_tool_execution:
        k = evaluate_venv_tool_execution_gate(replay_root); d = k.get("gate_decision", NOT_RUN)
        checks.append(_check("F13_VENV_TOOL_EXECUTION", "execution", d if d in {PASS, FAIL, NOT_RUN} else NOT_RUN, "V1.0-K registered-tool execution inside target venv.", ["venv-tool-execution-evidence.json", "execution-log.json", "result-bundle.json"]))
    else:
        checks.append(_check("F13_VENV_TOOL_EXECUTION", "execution", NOT_RUN, "Venv tool execution was not required by this invocation."))
    try:
        if (replay_root / "venv-tool-execution-evidence.json").is_file() and not (replay_root / "unified-execution-evidence.json").is_file():
            unify(replay_root)
    except Exception:
        pass
    if (replay_root / "venv-tool-execution-evidence.json").is_file() or (replay_root / "unified-execution-evidence.json").is_file():
        u = evaluate_evidence_unification_gate(replay_root); d = u.get("gate_decision", NOT_RUN)
        checks.append(_check("F14_EVIDENCE_UNIFICATION", "evidence", d if d in {PASS, FAIL, NOT_RUN} else NOT_RUN, "V1.0-L canonical execution evidence gate.", ["unified-execution-evidence.json"]))
    else:
        checks.append(_check("F14_EVIDENCE_UNIFICATION", "evidence", NOT_RUN, "No K/G/H execution evidence available for V1.0-L unification."))\n    for rel in required_artifacts or []:
        path = root / rel; exists = path.exists() and path.is_file()
        checks.append(_check("ARTIFACT:" + rel, "delivery", PASS if exists else FAIL, "Required artifact exists and can be hashed." if exists else "Required artifact is missing.", [rel]))
    if require_paper:
        candidates = [root / "paper.pdf", root / "paper" / "main.pdf", root / "paper.docx", root / "paper" / "main.docx"]
        existing = next((p for p in candidates if p.is_file()), None)
        checks.append(_check("F5_PAPER_DELIVERABLE", "delivery", PASS if existing else FAIL, "Paper deliverable exists." if existing else "Paper deliverable required but missing.", [str(existing.relative_to(root))] if existing else []))
    else: checks.append(_check("F5_PAPER_DELIVERABLE", "delivery", NOT_RUN, "Paper deliverable was not required by this invocation."))
    report = _gate(checks, run_id)
    report["artifact_hashes"] = {rel: _sha256(root / rel) for rel in required_artifacts or [] if (root / rel).is_file()}
    return report

def persist_final_submission_gate(run_dir: str | Path, report: dict[str, Any]) -> Path:
    root = Path(run_dir); root.mkdir(parents=True, exist_ok=True); path = root / "final-submission-gate.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"); return path
