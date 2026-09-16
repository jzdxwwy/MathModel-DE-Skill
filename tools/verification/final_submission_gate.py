"""V1.0 deterministic Final Submission Gate.

The gate aggregates existing evidence artifacts. It never invents missing
results and never turns NOT_RUN into PASS. A publishable submission requires
all mandatory checks to PASS.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

from .cross_artifact_consistency import evaluate_cross_artifact_consistency
from .reproducibility_gate import evaluate_reproducibility_gate

PASS = "PASS"
FAIL = "FAIL"
NOT_RUN = "NOT_RUN"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _check(check_id: str, category: str, decision: str, message: str = "", refs: list[str] | None = None) -> dict[str, Any]:
    return {"check_id": check_id, "category": category, "decision": decision, "message": message, "refs": refs or []}


def _gate(checks: list[dict[str, Any]], run_id: str) -> dict[str, Any]:
    failures = [x["check_id"] for x in checks if x["decision"] == FAIL]
    not_run = [x["check_id"] for x in checks if x["decision"] == NOT_RUN]
    decision = FAIL if failures else (NOT_RUN if not_run else PASS)
    return {
        "artifact_type": "FinalSubmissionGateReport",
        "schema_version": "1.0",
        "run_id": run_id,
        "checks": checks,
        "blocking_failures": failures,
        "not_run_checks": not_run,
        "gate_decision": decision,
    }


def evaluate_final_submission_gate(
    run_dir: str | Path,
    *,
    required_artifacts: list[str] | None = None,
    require_paper: bool = False,
    require_submission_manifest: bool = True,
    require_cross_artifact_consistency: bool = True,
    require_reproducibility: bool = True,
    rebuild_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Evaluate persisted evidence for final submission.

    Reproducibility is a mandatory V1.0-C gate by default. Without an
    independently supplied rebuild, C is NOT_RUN and therefore blocks PASS.
    This function never executes arbitrary code and never modifies the
    reference ResultBundle.
    """
    root = Path(run_dir)
    run_id = root.name
    checks: list[dict[str, Any]] = []

    result = _read_json(root / "result-bundle.json")
    verification = _read_json(root / "verification-report.json")
    render = _read_json(root / "presentation-render-manifest.json")
    submission = _read_json(root / "submission-manifest.json")

    checks.append(_check(
        "F1_RESULT_BUNDLE", "evidence", PASS if result and result.get("status") in {"VALIDATED", "FROZEN"} else FAIL,
        "ResultBundle must exist and be VALIDATED/FROZEN.", ["result-bundle.json"]
    ))

    if verification is None:
        checks.append(_check("F2_VERIFICATION", "verification", NOT_RUN, "VerificationReport missing.", ["verification-report.json"]))
    else:
        decision = str(verification.get("gate_decision") or verification.get("decision") or "NOT_RUN")
        checks.append(_check("F2_VERIFICATION", "verification", decision if decision in {PASS, FAIL, NOT_RUN} else NOT_RUN,
                             "Verification gate decision.", ["verification-report.json"]))

    if render is None:
        checks.append(_check("F3_RENDER_MANIFEST", "presentation", NOT_RUN, "PresentationRenderManifest missing.", ["presentation-render-manifest.json"]))
    else:
        decision = str(render.get("gate_decision", NOT_RUN))
        checks.append(_check("F3_RENDER_MANIFEST", "presentation", decision if decision in {PASS, FAIL, NOT_RUN} else NOT_RUN,
                             "Presentation render materialization gate.", ["presentation-render-manifest.json"]))

    if require_submission_manifest:
        checks.append(_check("F4_SUBMISSION_MANIFEST", "reproducibility", PASS if submission else FAIL,
                             "SubmissionManifest is required for V1.0.", ["submission-manifest.json"]))
    else:
        checks.append(_check("F4_SUBMISSION_MANIFEST", "reproducibility", PASS if submission else NOT_RUN,
                             "SubmissionManifest is optional in this invocation.", ["submission-manifest.json"]))

    if require_cross_artifact_consistency:
        cross = evaluate_cross_artifact_consistency(root.parent.parent, run_id)
        cross_decision = cross.get("gate_decision", NOT_RUN)
        checks.append(_check("F6_CROSS_ARTIFACT", "cross-artifact", cross_decision if cross_decision in {PASS, FAIL, NOT_RUN} else NOT_RUN,
                             "V1.0-B cross-artifact closure gate.", ["cross-artifact-consistency"]))
    else:
        checks.append(_check("F6_CROSS_ARTIFACT", "cross-artifact", NOT_RUN,
                             "Cross-artifact consistency was not required by this invocation."))

    if require_reproducibility:
        repro = evaluate_reproducibility_gate(root, rebuild_dir=rebuild_dir)
        repro_decision = repro.get("gate_decision", NOT_RUN)
        checks.append(_check("F7_REPRODUCIBILITY", "reproducibility", repro_decision if repro_decision in {PASS, FAIL, NOT_RUN} else NOT_RUN,
                             "V1.0-C independent rebuild gate.", ["reproducibility-gate.json"]))
    else:
        checks.append(_check("F7_REPRODUCIBILITY", "reproducibility", NOT_RUN,
                             "Reproducibility was not required by this invocation."))

    for rel in required_artifacts or []:
        path = root / rel
        checks.append(_check("ARTIFACT:" + rel, "delivery", PASS if path.exists() and path.is_file() else FAIL,
                             "Required artifact exists and can be hashed." if path.exists() and path.is_file() else "Required artifact is missing.", [rel]))

    if require_paper:
        paper_candidates = [root / "paper.pdf", root / "paper" / "main.pdf", root / "paper.docx", root / "paper" / "main.docx"]
        existing = next((p for p in paper_candidates if p.is_file()), None)
        checks.append(_check("F5_PAPER_DELIVERABLE", "delivery", PASS if existing else FAIL,
                             "Paper deliverable exists." if existing else "Paper deliverable required but missing.",
                             [str(existing.relative_to(root))] if existing else []))
    else:
        checks.append(_check("F5_PAPER_DELIVERABLE", "delivery", NOT_RUN, "Paper deliverable was not required by this invocation."))

    report = _gate(checks, run_id)
    report["artifact_hashes"] = {rel: _sha256(root / rel) for rel in required_artifacts or [] if (root / rel).is_file()}
    return report


def persist_final_submission_gate(run_dir: str | Path, report: dict[str, Any]) -> Path:
    root = Path(run_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "final-submission-gate.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path
