"""V1.0-S deterministic Claim -> ModelSpec formula/parameter trace."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json, math, re

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"


def _load(p: Path):
    try:
        x = json.loads(p.read_text(encoding="utf-8")); return x if isinstance(x, dict) else None
    except (OSError, ValueError, TypeError): return None


def _find(root: Path, names: list[str]):
    for name in names:
        for p in (root / name, root / "modeling" / name, root / "reference" / name,
                  root / "reference" / "modeling" / name, root / "paper" / name):
            if p.is_file(): return p
    return None


def _hash_expr(s: str) -> str:
    normalized = " ".join(str(s).strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _num(v):
    if isinstance(v, bool): return None
    if isinstance(v, (int, float)) and math.isfinite(float(v)): return float(v)
    if isinstance(v, str):
        m = re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", v.strip().replace(",", ""))
        if m:
            try: return float(m.group(0))
            except ValueError: return None
    return None


def _compare(a, b, atol, rtol):
    if a is None or b is None: return "NOT_COMPARABLE"
    return "MATCH" if abs(a - b) <= atol + rtol * abs(b) else "MISMATCH"


def _resolve_model_ref(ref: str, spec: dict[str, Any]):
    r = str(ref).strip()
    eqs = spec.get("equations", []) or []
    if r.startswith("equation:"):
        try:
            i = int(r.split(":", 1)[1])
            if 0 <= i < len(eqs): return str(eqs[i])
        except ValueError: pass
    if r.startswith("equation_hash:"):
        target = r.split(":", 1)[1]
        hits = [str(e) for e in eqs if _hash_expr(e) == target]
        if len(hits) == 1: return hits[0]
    if r in eqs: return r
    return None


def evaluate_claim_model_trace(root: str | Path, *, atol=1e-8, rtol=1e-6):
    root = Path(root)
    pe_path = _find(root, ["paper-evidence.json"])
    idx_path = _find(root, ["claim-evidence-index.json"])
    spec_path = _find(root, ["model-spec.json", "model-specs.json"])
    result_path = _find(root, ["result-bundle.json"])
    if not all((pe_path, idx_path, spec_path)):
        missing = [n for n, p in (("paper-evidence.json", pe_path), ("claim-evidence-index.json", idx_path),
                                  ("model-spec.json", spec_path)) if p is None]
        return {"artifact_type": "ClaimModelTrace", "schema_version": "1.0-S", "status": "DRAFT",
                "run_id": root.name, "claims": [], "gate_decision": NOT_RUN,
                "violations": ["missing: " + ", ".join(missing)]}
    pe, idx, spec = _load(pe_path), _load(idx_path), _load(spec_path)
    result = _load(result_path) if result_path else None
    if not all((pe, idx, spec)):
        return {"artifact_type": "ClaimModelTrace", "schema_version": "1.0-S", "status": "DRAFT",
                "run_id": root.name, "claims": [], "gate_decision": FAIL, "violations": ["invalid JSON"]}

    expected_model_id = str(result.get("model_id", "")) if result else ""
    if result is None or not expected_model_id:
        return {"artifact_type": "ClaimModelTrace", "schema_version": "1.0-S", "status": "DRAFT",
                "run_id": root.name, "claims": [], "gate_decision": FAIL,
                "violations": ["ResultBundle.model_id is required to anchor model identity"]}

    ib = {str(c.get("claim_id")): c for c in idx.get("claims", []) or []}
    violations = []
    claims = []
    spec_model_id = str(spec.get("model_id", ""))
    if spec_model_id != expected_model_id:
        violations.append("ModelSpec.model_id != ResultBundle.model_id")

    for pc in pe.get("claims", []) or []:
        cid = str(pc.get("claim_id", ""))
        ic = ib.get(cid)
        if not cid:
            violations.append("claim missing claim_id"); continue
        if ic is None:
            violations.append(f"{cid}: missing ClaimEvidenceIndex"); continue

        model_id = str(pc.get("model_id") or ic.get("model_id") or expected_model_id)
        if model_id != spec_model_id:
            violations.append(f"{cid}: model_id mismatch")

        eq_obs = pc.get("equation_observations", []) or []
        par_obs = pc.get("parameter_observations", []) or []
        eqb = []; pb = []
        for i, o in enumerate(eq_obs):
            cref = str(o.get("expression") or o.get("claim_ref") or "")
            mref = str(o.get("model_ref") or (f"equation:{i}" if i < len(spec.get("equations", []) or []) else ""))
            meq = _resolve_model_ref(mref, spec)
            match = bool(cref and meq and _hash_expr(cref) == _hash_expr(meq))
            eqb.append({"claim_ref": cref, "model_ref": mref, "normalized_match": match,
                        "claim_expression_hash": _hash_expr(cref) if cref else "",
                        "model_expression_hash": _hash_expr(meq) if meq else ""})
            if not match: violations.append(f"{cid}: equation mismatch or unresolved {mref}")
        for o in par_obs:
            sym = str(o.get("symbol", ""))
            cv = o.get("value", o.get("claim_value"))
            params = [p for p in spec.get("parameters", []) or [] if str(p.get("symbol")) == sym]
            if len(params) != 1:
                pb.append({"symbol": sym, "claim_value": cv, "model_value": None, "comparison": "MISSING", "atol": atol, "rtol": rtol})
                violations.append(f"{cid}: parameter {sym} not uniquely defined")
                continue
            mv = params[0].get("value"); unit = str(o.get("unit", ""))
            comp = _compare(_num(cv), _num(mv), atol, rtol)
            if unit and str(params[0].get("unit", "")) and unit != str(params[0].get("unit")): comp = "MISMATCH"
            if comp != "MATCH": violations.append(f"{cid}: parameter {sym} mismatch")
            pb.append({"symbol": sym, "claim_value": cv, "model_value": mv, "unit": unit, "comparison": comp, "atol": atol, "rtol": rtol})
        has_obs = bool(eq_obs or par_obs)
        closed = has_obs and all(x["normalized_match"] for x in eqb) and all(x["comparison"] == "MATCH" for x in pb) and model_id == spec_model_id == expected_model_id
        claims.append({"claim_id": cid, "model_id": model_id, "equation_bindings": eqb, "parameter_bindings": pb,
                       "trace_status": "CLOSED" if closed else "OPEN"})
    decision = FAIL if violations or any(c["trace_status"] != "CLOSED" for c in claims) else (PASS if claims else NOT_RUN)
    out = {"artifact_type": "ClaimModelTrace", "schema_version": "1.0-S",
           "status": "VALIDATED" if decision == PASS else "DRAFT", "run_id": root.name,
           "claims": claims, "gate_decision": decision, "violations": violations}
    (root / "claim-model-trace.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return out
