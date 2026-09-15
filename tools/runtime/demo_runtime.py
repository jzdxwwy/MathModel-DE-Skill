"""V0.6 runtime smoke/demo.

This uses a fake model adapter only to demonstrate the host/runtime boundary.
It is not a CUMCM problem solver and does not claim real modeling results.
"""
from __future__ import annotations

from pathlib import Path
import json

from .model_adapter import ModelRequest, ModelResponse
from .orchestrator import RuntimeOrchestrator, RuntimeStage
from .task_context import TaskContext


class DemoModel:
    def invoke(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            status="ok",
            output={"decision": "execute_demo_stage", "stage": request.stage},
            message="demo model accepted runtime request",
        )


def write_artifact(ctx: TaskContext, name: str, filename: str, payload: dict) -> None:
    path = ctx.project_dir / "artifacts" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    ctx.register_artifact(name, path)


def build_stages():
    def start(ctx):
        write_artifact(ctx, "ProblemSpec", "problem_spec.json", {
            "problem_id": "runtime-demo-001",
            "type": "E",
            "source": "synthetic runtime demo",
        })

    def analysis(ctx):
        write_artifact(ctx, "ProblemMap", "problem_map.json", {
            "problem_id": "runtime-demo-001",
            "tasks": [{"id": "Q1", "type": "prediction"}],
        })

    return [
        RuntimeStage("00-start", "Inspect the task and establish ProblemSpec.", start),
        RuntimeStage("01-analysis", "Map the problem into computable tasks.", analysis),
    ]


def main(out: str = "runtime_demo_run"):
    ctx = TaskContext(task_id="runtime-demo-001", project_dir=Path(out).resolve())
    runtime = RuntimeOrchestrator(Path(__file__).resolve().parents[2], DemoModel())
    return runtime.run(ctx, build_stages())


if __name__ == "__main__":
    print(main())
