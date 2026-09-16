"""V0.9-G verification bridge with registry-driven domain rules."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..verification.default_rules import build_default_registry
from ..verification.result_verifier import persist_report, verify_run


def verify_executions(project_dir: str | Path, executions: list[dict[str, Any]], dispatch: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(project_dir)
    dispatch_by_task = {x.get("task_id"): x for x in dispatch.get("dispatches", [])}
    registry = build_default_registry()
    reports = []
    for execution in executions:
        run_id = execution.get("run_id")
        if not run_id:
            continue
        run_dir = root / "runs" / run_id
        dispatch_item = dispatch_by_task.get(execution.get("question"))
        report = verify_run(run_dir, dispatch_item)
        if report.get("gate_decision") != "FAIL":
            result_path = run_dir / "result-bundle.json"
            if result_path.exists():
                result = json.loads(result_path.read_text(encoding="utf-8"))
                model_id = str(result.get("model_id", ""))
                binding = (dispatch_item or {}).get("binding") or (dispatch_item or {}).get("data_binding") or {}
                domain_checks = registry.verify(model_id, result, binding)
                report["checks"].extend(domain_checks)
                if any(c["status"] == "FAIL" for c in domain_checks):
                    report["gate_decision"] = "FAIL"
                    report["status"] = "DRAFT"
                elif any(c["status"] in {"WARN", "NOT_RUN"} for c in domain_checks):
                    report["gate_decision"] = "PASS_WITH_WARNINGS"
                report["critical_issues"] = [c["evidence"] for c in report["checks"] if c["status"] == "FAIL"]
                report["recommendations"] = [c["evidence"] for c in report["checks"] if c["status"] == "NOT_RUN"]
                report["domain_rule_manifest"] = registry.manifest()
        path = persist_report(run_dir, report)
        report["artifact_ref"] = str(path)
        reports.append(report)
    summary = root / "artifacts" / "verification-summary.json"
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps({"artifact_type":"VerificationSummary","schema_version":"0.9","rule_registry":registry.manifest(),"reports":reports}, ensure_ascii=False, indent=2), encoding="utf-8")
    return reports
