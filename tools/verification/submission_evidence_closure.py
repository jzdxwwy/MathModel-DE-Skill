"""V1.0-N: close publication references to canonical UnifiedExecutionEvidence."""
from __future__ import annotations
import json
from pathlib import Path

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"

def _read(p: Path):
    try:
        v = json.loads(p.read_text(encoding="utf-8"))
        return v if isinstance(v, dict) else None
    except Exception:
        return None

def _first(root: Path, *names):
    for n in names:
        p = root / n
        if p.is_file():
            return p
    return None

def _rel(p: Path, root: Path) -> str:
    return str(p.relative_to(root)).replace("\\", "/")

def evaluate_submission_evidence_closure(run_dir: str | Path) -> dict:
    root = Path(run_dir)
    ue = _first(root / "reference" / "execution", "unified-execution-evidence.json") or _first(root, "unified-execution-evidence.json")
    if ue is None:
        return {"artifact_type": "SubmissionEvidenceClosure", "schema_version": "1.0-N",
                "gate_decision": NOT_RUN, "checked_refs": [],
                "violations": [{"reason": "UnifiedExecutionEvidence missing"}]}
    ue_ref = _rel(ue, root)
    violations = []
    checked = [ue_ref]

    sources = [
        ("paper-evidence.json", _first(root, "paper-evidence.json") or _first(root / "paper", "paper-evidence.json")),
        ("submission-manifest.json", _first(root, "submission-manifest.json")),
    ]
    for label, p in sources:
        if p is None:
            continue
        doc = _read(p)
        if doc is None:
            violations.append({"artifact": label, "reason": "invalid JSON"})
            continue
        checked.append(_rel(p, root))

        if label == "paper-evidence.json":
            claims = doc.get("claims", []) if isinstance(doc.get("claims", []), list) else []
            for claim in claims:
                refs = claim.get("unified_execution_evidence_refs", []) if isinstance(claim, dict) else []
                if not refs:
                    violations.append({"artifact": label, "claim_id": claim.get("claim_id") if isinstance(claim, dict) else None,
                                       "reason": "canonical UnifiedExecutionEvidence reference missing"})
                elif not any(str(ref).replace("\\", "/").endswith("unified-execution-evidence.json") for ref in refs):
                    violations.append({"artifact": label, "claim_id": claim.get("claim_id") if isinstance(claim, dict) else None,
                                       "reason": "canonical UnifiedExecutionEvidence reference missing"})
            continue

        artifacts = doc.get("artifacts", []) if isinstance(doc.get("artifacts", []), list) else []
        candidates = []
        for art in artifacts:
            if not isinstance(art, dict):
                continue
            kind = str(art.get("kind", "")).strip().lower()
            path = str(art.get("path", "")).replace("\\", "/")
            if kind in {"execution-evidence", "unified-execution-evidence"} or path.endswith("unified-execution-evidence.json"):
                candidates.append((kind, path))
        if not candidates:
            violations.append({"artifact": label, "reason": "canonical UnifiedExecutionEvidence not indexed"})
        elif not any(path == ue_ref for _, path in candidates):
            violations.append({"artifact": label, "reason": "indexed UnifiedExecutionEvidence path is not canonical",
                               "expected": ue_ref, "actual": [path for _, path in candidates]})

    return {"artifact_type": "SubmissionEvidenceClosure", "schema_version": "1.0-N",
            "gate_decision": FAIL if violations else PASS, "checked_refs": checked, "violations": violations}
