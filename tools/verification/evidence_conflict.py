"""V1.0-O deterministic evidence conflict detection; never chooses a winning source."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import json, math

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"

def _load(path: Path) -> dict[str, Any] | None:
    try:
        v = json.loads(path.read_text(encoding="utf-8"))
        return v if isinstance(v, dict) else None
    except (OSError, ValueError, TypeError):
        return None

def _numeric(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))

def _equal_numeric(a: float, b: float, atol: float, rtol: float) -> bool:
    return abs(a - b) <= atol + rtol * max(abs(a), abs(b))

def evaluate_evidence_conflicts(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    p = root / "claim-lineage.json"
    if not p.is_file():
        return {"artifact_type":"EvidenceConflictReport","schema_version":"1.0-O",
                "gate_decision":NOT_RUN,"claims":[],"violations":["claim-lineage.json missing"]}
    data = _load(p)
    if data is None:
        return {"artifact_type":"EvidenceConflictReport","schema_version":"1.0-O",
                "gate_decision":FAIL,"claims":[],"violations":["invalid claim-lineage.json"]}

    reports: list[dict[str, Any]] = []
    violations: list[str] = []

    for c in data.get("claims", []):
        obs = c.get("observations", []) or []
        cid = str(c.get("claim_id",""))
        if not obs:
            reports.append({"claim_id":cid,"status":"MISSING_EVIDENCE","observations":[],"conflicts":[]})
            violations.append(f"{cid}: no observations supplied for conflict checking")
            continue

        conflicts = []
        status = "NO_CONFLICT"
        incomparable = False
        for i in range(len(obs)):
            for j in range(i + 1, len(obs)):
                a, b = obs[i], obs[j]
                ta, tb = a.get("comparison_type"), b.get("comparison_type")
                if ta == "none" or tb == "none":
                    continue
                if ta != tb:
                    incomparable = True
                    continue
                if ta == "numeric":
                    ua, ub = a.get("unit"), b.get("unit")
                    if ua != ub or not (_numeric(a.get("value")) and _numeric(b.get("value"))):
                        incomparable = True
                        continue
                    atol = max(float(a.get("atol",0.0)), float(b.get("atol",0.0)))
                    rtol = max(float(a.get("rtol",0.0)), float(b.get("rtol",0.0)))
                    av, bv = float(a["value"]), float(b["value"])
                    if not _equal_numeric(av, bv, atol, rtol):
                        status = "CONFLICT"
                        conflicts.append({
                            "left":str(a.get("source_ref")),"right":str(b.get("source_ref")),
                            "reason":f"numeric values differ beyond tolerance; units={ua!r}",
                            "difference":abs(av-bv),
                            "tolerance":atol + rtol * max(abs(av),abs(bv))
                        })
                elif ta == "exact":
                    av = str(a.get("normalized_value", a.get("value")))
                    bv = str(b.get("normalized_value", b.get("value")))
                    if av != bv:
                        status = "CONFLICT"
                        conflicts.append({
                            "left":str(a.get("source_ref")),"right":str(b.get("source_ref")),
                            "reason":"exact observations have different normalized values",
                            "difference":None,"tolerance":None
                        })

        if status != "CONFLICT" and incomparable:
            status = "NOT_COMPARABLE"
        reports.append({
            "claim_id":cid,"status":status,
            "observations":[str(x.get("source_ref")) for x in obs],
            "conflicts":conflicts
        })
        if status == "CONFLICT":
            violations.append(f"{cid}: evidence conflict detected")
        elif status == "NOT_COMPARABLE":
            violations.append(f"{cid}: observations are not deterministically comparable")

    decision = FAIL if violations else (PASS if reports else NOT_RUN)
    out = {"artifact_type":"EvidenceConflictReport","schema_version":"1.0-O",
           "gate_decision":decision,"claims":reports,"violations":violations}
    (root / "evidence-conflict-report.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return out
