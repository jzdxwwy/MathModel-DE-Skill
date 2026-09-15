"""Persistent execution context shared by model, workflow, tools and gates."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
import json


@dataclass
class TaskContext:
    task_id: str
    project_dir: Path
    problem_input: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)
    stage_status: Dict[str, str] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def register_artifact(self, name: str, path: Path) -> None:
        self.artifacts[name] = str(path)
        self.logs.append(f"REGISTER {name} -> {path}")

    def set_stage(self, stage: str, status: str) -> None:
        self.stage_status[stage] = status
        self.logs.append(f"STAGE {stage} = {status}")

    def snapshot(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "project_dir": str(self.project_dir),
            "problem_input": self.problem_input,
            "artifacts": self.artifacts,
            "stage_status": self.stage_status,
            "metadata": self.metadata,
            "logs": self.logs,
        }

    def persist(self) -> Path:
        path = self.project_dir / "manifest" / "task_context.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.snapshot(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path
