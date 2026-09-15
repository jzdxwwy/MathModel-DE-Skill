"""V0.6 runtime orchestrator.

It binds the model adapter, Skill loader, workflow engine, tools and task context.
The orchestrator intentionally does not contain modeling knowledge.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

from .model_adapter import ModelAdapter, ModelRequest
from .skill_loader import SkillLoader
from .task_context import TaskContext
from .tool_registry import ToolRegistry


@dataclass
class RuntimeStage:
    name: str
    instruction: str
    executor: Callable[[TaskContext], None]
    gate: Optional[Callable[[TaskContext], None]] = None


class RuntimeOrchestrator:
    """Run model-driven stages while keeping artifacts and gates authoritative."""

    def __init__(self, repo_root: Path, model: ModelAdapter, tools: Optional[ToolRegistry] = None):
        self.loader = SkillLoader(repo_root)
        self.model = model
        self.tools = tools or ToolRegistry()

    def execute_stage(self, ctx: TaskContext, stage: RuntimeStage) -> None:
        bundle = self.loader.load_bundle(stage.name)
        request = ModelRequest(
            task_id=ctx.task_id,
            stage=stage.name,
            instruction=stage.instruction,
            context={
                "problem_input": ctx.problem_input,
                "artifacts": ctx.artifacts,
                "stage_status": ctx.stage_status,
                "metadata": ctx.metadata,
                "skill": bundle,
                "tools": self.tools.describe(),
            },
        )
        response = self.model.invoke(request)
        if response.status not in {"ok", "pass", "completed"}:
            ctx.set_stage(stage.name, "MODEL_FAIL")
            ctx.persist()
            raise RuntimeError(f"{stage.name}: model adapter failed: {response.message}")
        ctx.metadata.setdefault("model_outputs", {})[stage.name] = {
            "status": response.status,
            "output": response.output,
            "message": response.message,
        }
        stage.executor(ctx)
        if stage.gate:
            stage.gate(ctx)
        ctx.set_stage(stage.name, "PASS")
        ctx.persist()

    def run(self, ctx: TaskContext, stages: Iterable[RuntimeStage]) -> Path:
        ctx.project_dir.mkdir(parents=True, exist_ok=True)
        ctx.set_stage("runtime", "STARTED")
        ctx.persist()
        for stage in stages:
            self.execute_stage(ctx, stage)
        ctx.set_stage("runtime", "COMPLETED")
        return ctx.persist()
