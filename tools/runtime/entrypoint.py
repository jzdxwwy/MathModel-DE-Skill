"""Executable entry point for MathModel-DE-Skill Runtime V0.6-C.

Usage:
    Demo/offline:
        python -m tools.runtime.entrypoint --host demo --problem problem.pdf

    Real OpenAI-compatible endpoint:
        set MATHMODEL_LLM_BASE_URL, MATHMODEL_LLM_API_KEY, MATHMODEL_LLM_MODEL
        python -m tools.runtime.entrypoint --host real --problem problem.pdf --attachments ./attachments

The real host is provider-neutral at the Runtime boundary and currently uses
an OpenAI-compatible HTTP chat-completions adapter. No API key is stored in code.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .host_adapter import HostRequest, HostResponse, normalize_problem_input
from .model_adapter import CallbackModelAdapter, ModelResponse
from .real_host import RealLLMHostAdapter
from .task_context import TaskContext
from .orchestrator import RuntimeOrchestrator, RuntimeStage


class DemoHostAdapter:
    """Deterministic host used to prove the executable boundary without an API key."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def run(self, request: HostRequest) -> HostResponse:
        task_id = request.task_id or "runtime-demo-001"
        ctx = TaskContext(
            task_id=task_id,
            project_dir=Path(request.output_dir).resolve(),
            problem_input=request.problem_input,
        )

        def model_callback(model_request):
            return ModelResponse(
                status="ok",
                output={
                    "decision": "continue",
                    "stage": model_request.stage,
                    "instruction": model_request.instruction,
                },
                message="demo host accepted stage",
            )

        runtime = RuntimeOrchestrator(
            repo_root=self.repo_root,
            model=CallbackModelAdapter(model_callback),
        )

        def write_stage(stage_name: str):
            def executor(stage_ctx):
                path = stage_ctx.project_dir / "runtime" / f"{stage_name}.txt"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    f"Runtime demo executed stage: {stage_name}\n",
                    encoding="utf-8",
                )
                stage_ctx.register_artifact(stage_name, path)
            return executor

        stages = [
            RuntimeStage("00-start", "Initialize the modeling task and inspect the supplied input.", write_stage("00-start")),
            RuntimeStage("01-analysis", "Build the initial problem map from the task context.", write_stage("01-analysis")),
            RuntimeStage("02-data", "Profile available data inputs and identify data risks.", write_stage("02-data")),
        ]
        manifest = runtime.run(ctx, stages)
        return HostResponse(
            status="completed",
            task_id=task_id,
            manifest=str(manifest),
            message="V0.6-B executable runtime completed demo stages.",
            artifacts={k: str(v) for k, v in ctx.artifacts.items()},
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run MathModel-DE-Skill Runtime")
    parser.add_argument("--host", choices=["demo", "real"], default="demo", help="Execution host")
    parser.add_argument("--problem", help="Problem statement path or text")
    parser.add_argument("--attachments", nargs="*", default=[], help="Attachment paths")
    parser.add_argument("--out", default="runtime_run", help="Runtime output directory")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--instruction", default="Run the MathModel-DE-Skill workflow.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    request = HostRequest(
        instruction=args.instruction,
        problem_input=normalize_problem_input(args.problem, args.attachments),
        output_dir=args.out,
        task_id=args.task_id,
    )
    host = DemoHostAdapter(repo_root) if args.host == "demo" else RealLLMHostAdapter(repo_root)
    response = host.run(request)
    print(f"status={response.status}")
    print(f"task_id={response.task_id}")
    print(f"manifest={response.manifest}")
    if response.message:
        print(f"message={response.message}")
    return 0 if response.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
