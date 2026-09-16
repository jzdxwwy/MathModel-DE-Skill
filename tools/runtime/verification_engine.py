"""V0.9-N verification bridge with presentation materialization."""
from __future__ import annotations
import json
from pathlib import Path
from ..verification.default_rules import build_default_registry
from ..verification.result_verifier import persist_report, verify_run
from ..verification.rule_evaluator import evaluate_model, gate
from ..verification.recompute_engine import recompute
from ..verification.evidence_lineage import build_lineage
from ..verification.rendered_consistency import verify_presentation_consistency
from ..verification.presentation_materializer import materialize_presentation


def _load_presentation_manifest(root: Path) -> dict | None:
    path = root / "artifacts" / "presentation-data-manifest.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def verify_executions(project_dir: str | Path, executions: list[dict], dispatch: dict) -> list[dict]:
    root = Path(project_dir)
    dispatch_by_task = {x.get("task_id"): x for x in dispatch.get("dispatches", [])}
    registry = build_default_registry(); reports = []
    presentation_manifest = _load_presentation_manifest(root)
    for execution in executions:
        run_id = execution.get("run_id")
        if not run_id: continue
        run_dir = root / "runs" / run_id
        dispatch_item = dispatch_by_task.get(execution.get("question"))
        report = verify_run(run_dir, dispatch_item)
        result_path = run_dir / "result-bundle.json"
        if report.get("gate_decision") != "FAIL" and result_path.exists():
            result = json.loads(result_path.read_text(encoding="utf-8"))
            model_id = str(result.get("model_id", ""))
            binding = (dispatch_item or {}).get("binding") or (dispatch_item or {}).get("data_binding") or {}
            domain_checks = registry.verify(model_id, result, binding)
            acceptance_checks = evaluate_model(model_id, result, binding)
            recompute_checks = recompute(model_id, result)
            report["checks"].extend(domain_checks); report["checks"].extend(acceptance_checks); report["checks"].extend(recompute_checks)
            report["gate_decision"] = gate(report["checks"])
            report["status"] = "VALIDATED" if report["gate_decision"] != "FAIL" else "DRAFT"
            report["critical_issues"] = [c["evidence"] for c in report["checks"] if c["status"] == "FAIL"]
            report["recommendations"] = [c["evidence"] for c in report["checks"] if c["status"] == "NOT_RUN"]
            report["domain_rule_manifest"] = registry.manifest()
            report["acceptance_version"] = "0.9-H"; report["recompute_version"] = "0.9-I"
            lineage = build_lineage(execution, result, report, dispatch_item)
            lineage_path = run_dir / "evidence-lineage.json"
            lineage_path.write_text(json.dumps(lineage, ensure_ascii=False, indent=2), encoding="utf-8")
            report["lineage_ref"] = str(lineage_path)

            if presentation_manifest is not None:
                consistency = verify_presentation_consistency(presentation_manifest, result)
                report["presentation_consistency"] = consistency
                if consistency.get("gate_decision") == "FAIL":
                    report["gate_decision"] = "FAIL"
                    report["status"] = "DRAFT"
                render_manifest = materialize_presentation(root, presentation_manifest, result)
                report["presentation_render_manifest_ref"] = str(root / "artifacts" / "presentation-render-manifest.json")
                if render_manifest.get("gate_decision") == "FAIL":
                    report["gate_decision"] = "FAIL"
                    report["status"] = "DRAFT"
        path = persist_report(run_dir, report); report["artifact_ref"] = str(path); reports.append(report)
    summary = root / "artifacts" / "verification-summary.json"; summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps({"artifact_type":"VerificationSummary","schema_version":"0.9-N","acceptance_version":"0.9-H","recompute_version":"0.9-I","lineage_version":"0.9-J","presentation_consistency_version":"0.9-M","presentation_materialization_version":"0.9-N","rule_registry":registry.manifest(),"reports":reports}, ensure_ascii=False, indent=2), encoding="utf-8")
    return reports
