"""Minimal artifact-driven workflow engine for MathModel-DE-Skill.

The engine is intentionally small: it orchestrates Stage adapters and Gates,
while domain/model knowledge stays in Stage Skills and tools.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional
import json


@dataclass
class StageContext:
    project_dir: Path
    artifacts: Dict[str, Path] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)

    def register(self, name: str, path: Path) -> None:
        self.artifacts[name] = path
        self.logs.append(f"REGISTER {name} -> {path}")


@dataclass
class Stage:
    name: str
    inputs: List[str]
    outputs: List[str]
    runner: Callable[[StageContext], None]
    gate: Optional[Callable[[StageContext], None]] = None

    def run(self, ctx: StageContext) -> None:
        missing = [x for x in self.inputs if x not in ctx.artifacts]
        if missing:
            raise RuntimeError(f"{self.name}: missing upstream artifacts: {missing}")
        self.runner(ctx)
        missing_outputs = [x for x in self.outputs if x not in ctx.artifacts]
        if missing_outputs:
            raise RuntimeError(f"{self.name}: missing outputs: {missing_outputs}")
        if self.gate:
            self.gate(ctx)
        ctx.logs.append(f"PASS {self.name}")


class WorkflowEngine:
    def __init__(self, stages: Iterable[Stage]):
        self.stages = list(stages)

    def run(self, ctx: StageContext) -> Path:
        ctx.project_dir.mkdir(parents=True, exist_ok=True)
        for stage in self.stages:
            stage.run(ctx)
        manifest = ctx.project_dir / "manifest" / "workflow_manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps(
                {"status": "completed", "artifacts": {k: str(v) for k, v in ctx.artifacts.items()}, "logs": ctx.logs},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return manifest


def require_files(*artifact_names: str) -> Callable[[StageContext], None]:
    def gate(ctx: StageContext) -> None:
        for name in artifact_names:
            path = ctx.artifacts.get(name)
            if not path or not path.exists() or path.stat().st_size == 0:
                raise RuntimeError(f"Gate failed: artifact {name} is missing or empty")
    return gate
