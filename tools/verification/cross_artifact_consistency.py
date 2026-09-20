"""V1.0-B cross-artifact consistency gate.

This gate checks closure between PaperEvidence, PaperManifest,
PresentationDataManifest, RenderManifest, SubmissionManifest and persisted
run artifacts. It validates references and hashes; it does not infer paper
prose, recompute numerical results, inspect pixels/OCR, or silently repair
artifacts.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"


def _load(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _ids(items: list[dict[str, Any]], key: str) -> set[str]:
    return {str(x[key]) for x in items if isinstance(x, dict) and x.get(key) is not None}


def _check_ref_set(check_id: str, refs: list[str], available: set[str], label: str) -> dict[str, Any]:
    missing = sorted(set(map(str, refs)) - available)
    return {"check_id": check_id, "status": PASS if not missing else FAIL,
            "evidence": f"{label}: all references resolve" if not missing else f"{label}: missing references={missing}"}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evaluate_cross_artifact_consistency(root: str | Path, run_id: str) -> dict[str, Any]:
    root = Path(root)
    run_dir = root / "runs" / str(run_id)
    paper_evidence = (_load(run_dir / "paper-evidence.json")
                      or _load(run_dir / "paper" / "paper-evidence.json")
                      or _load(root / "artifacts" / "paper-evidence.json"))
    paper_manifest = (_load(run_dir / "paper-manifest.json")
                      or _load(run_dir / "paper" / "paper-manifest.json")
                      or _load(root / "artifacts" / "paper-manifest.json"))
    # V1.0-M canonical topology first, legacy flat layout second.
    presentation = (_load(root / "artifacts" / "presentation-data-manifest.json")
                    or _load(run_dir / "presentation-data-manifest.json")
                    or _load(run_dir / "reference" / "presentation" / "presentation-data-manifest.json"))
    render = (_load(run_dir / "presentation-render-manifest.json")
              or _load(run_dir / "reference" / "presentation" / "presentation-render-manifest.json"))
    submission = _load(run_dir / "submission-manifest.json")
    result = (_load(run_dir / "reference" / "execution" / "result-bundle.json")
              or _load(run_dir / "result-bundle.json"))
    verification = (_load(run_dir / "reference" / "verification" / "verification-report.json")
                    or _load(run_dir / "verification-report.json"))

    checks: list[dict[str, Any]] = []
    missing_core = [name for name, obj in (("PaperEvidence", paper_evidence), ("PaperManifest", paper_manifest),
                                            ("PresentationDataManifest", presentation), ("RenderManifest", render),
                                            ("SubmissionManifest", submission)) if obj is None]
    if missing_core:
        checks.append({"check_id": "B00", "status": FAIL,
                       "evidence": f"Missing required cross-artifact manifests={missing_core}"})
        return _report(run_id, checks)

    claims = paper_evidence.get("claims") or []
    claim_ids = _ids(claims, "claim_id")
    sections = paper_manifest.get("sections") or []
    presentation_items = presentation.get("items") or []
    evidence_ids = _ids(presentation_items, "evidence_id")

    # B1: PaperManifest -> PaperEvidence closure.
    referenced_claims = {str(r) for s in sections for r in (s.get("claim_refs") or [])}
    checks.append(_check_ref_set("B01", list(referenced_claims), claim_ids, "PaperManifest.claim_refs -> PaperEvidence.claim_id"))

    # B2: every material claim is represented in the PaperManifest.
    checks.append({"check_id": "B02", "status": PASS if claim_ids <= referenced_claims else FAIL,
                   "evidence": "Every PaperEvidence claim is referenced by PaperManifest" if claim_ids <= referenced_claims
                   else f"Unreferenced claims={sorted(claim_ids - referenced_claims)}"})

    # B3: PaperEvidence presentation references -> PresentationDataManifest.
    for kind, field in (("figure", "figure_refs"), ("table", "table_refs"), ("equation", "equation_refs")):
        refs = {str(r) for c in claims for r in (c.get(field) or [])}
        available = {str(i["evidence_id"]) for i in presentation_items if i.get("kind") == kind}
        checks.append(_check_ref_set(f"B03-{kind[0].upper()}", list(refs), available,
                                     f"PaperEvidence.{field} -> PresentationDataManifest({kind})"))

    # B4: PresentationDataManifest must bind to a persisted ResultBundle.
    result_ok = result is not None and result.get("status") in {"VALIDATED", "FROZEN"}
    checks.append({"check_id": "B04", "status": PASS if result_ok else FAIL,
                   "evidence": "Presentation bindings have a VALIDATED/FROZEN ResultBundle" if result_ok
                   else "ResultBundle missing or not VALIDATED/FROZEN"})
    if result_ok:
        for item in presentation_items:
            binds = item.get("bindings") or []
            checks.append({"check_id": f"B04:{item.get('evidence_id')}",
                           "status": PASS if all(b.get("result_ref") for b in binds if isinstance(b, dict)) else FAIL,
                           "evidence": f"Presentation item {item.get('evidence_id')} declares result_ref bindings"})

    # B5: RenderManifest closes PresentationDataManifest.
    render_refs = set()
    for item in render.get("items", render.get("renders", [])) or []:
        if isinstance(item, dict):
            for k in ("evidence_id", "source_evidence_id", "presentation_evidence_id"):
                if item.get(k): render_refs.add(str(item[k]))
    if not render_refs:
        render_refs = {str(x) for x in (render.get("evidence_ids") or [])}
    checks.append(_check_ref_set("B05", list(evidence_ids), render_refs, "PresentationDataManifest.evidence_id -> RenderManifest"))

    # B6: PaperManifest presentation refs must resolve to presentation evidence.
    for kind, field in (("figure", "figure_refs"), ("table", "table_refs"), ("equation", "equation_refs")):
        refs = {str(r) for s in sections for r in (s.get(field) or [])}
        checks.append(_check_ref_set(f"B06-{kind[0].upper()}", list(refs), evidence_ids,
                                     f"PaperManifest.{field} -> PresentationDataManifest.evidence_id"))

    # B7: SubmissionManifest references and hashes must match actual files.
    artifact_checks = []
    for art in submission.get("artifacts") or []:
        if not isinstance(art, dict) or not art.get("path"):
            artifact_checks.append(False)
            continue
        path = root / str(art["path"])
        ok = path.is_file() and _sha256(path) == str(art.get("sha256", ""))
        artifact_checks.append(ok)
    checks.append({"check_id": "B07", "status": PASS if artifact_checks and all(artifact_checks) else FAIL,
                   "evidence": "SubmissionManifest artifact paths and SHA256 values match" if artifact_checks and all(artifact_checks)
                   else "SubmissionManifest contains missing files or SHA256 mismatches"})

    # B8: run identity consistency.
    ids_ok = all(obj.get("run_id") in {None, str(run_id)} for obj in (result or {}, verification or {}, submission or {}))
    checks.append({"check_id": "B08", "status": PASS if ids_ok else FAIL,
                   "evidence": "run_id is consistent across run artifacts" if ids_ok else "run_id mismatch across run artifacts"})

    return _report(run_id, checks)


def _report(run_id: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    decision = FAIL if any(c.get("status") == FAIL for c in checks) else NOT_RUN if any(c.get("status") == NOT_RUN for c in checks) else PASS
    return {"artifact_type": "CrossArtifactConsistencyReport", "schema_version": "1.0-B",
            "run_id": str(run_id), "gate_decision": decision, "checks": checks,
            "blocking_failures": [c["evidence"] for c in checks if c.get("status") == FAIL]}
