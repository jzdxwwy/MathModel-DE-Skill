"""V0.9-E verification bridge: every compute run gets a verification artifact."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..verification.result_verifier import persist_report, verify_run


def verify_executions(project_dir: str | Path, executions: list[dict[str, Any]], dispatch: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(project_dir)
    dispatch_by_task = {x.get("task_id"): x for x in dispatch.get("dispatches", [])}
    reports = []
    for execution in executions:
        run_id = execution.get("run_id")
        if not run_id:
            continue
        run_dir = root / "runs" / run_id
        report = verify_run(run_dir, dispatch_by_task.get(execution.get("question")))
        path = persist_report(run_dir, report)
        report["artifact_ref"] = str(path)
        reports.append(report)
    summary = root / "artifacts" / "verification-summary.json"
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps({"artifact_type":"VerificationSummary","schema_version":"0.9","reports":reports}, ensure_ascii=False, indent=2), encoding="utf-8")
    return reports
