"""Real LLM host adapter with V0.7 problem/attachment ingestion."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .host_adapter import HostRequest, HostResponse
from .input_boundary import ingest_runtime_input
from .llm_config import LLMConfig
from .model_adapter import ModelAdapter
from .orchestrator import RuntimeOrchestrator, RuntimeStage
from .providers.openai_compatible import OpenAICompatibleModelAdapter
from .task_context import TaskContext


class RealLLMHostAdapter:
    """Run the Runtime against a real LLM after deterministic input ingestion."""

    def __init__(self, repo_root: Path, model: Optional[ModelAdapter] = None, config: Optional[LLMConfig] = None):
        self.repo_root = repo_root
        self.config = config or LLMConfig.from_env()
        self.model = model or OpenAICompatibleModelAdapter(self.config)

    def run(self, request: HostRequest) -> HostResponse:
        task_id = request.task_id or "runtime-llm-001"
        project_dir = Path(request.output_dir).resolve()
        raw_problem = request.problem_input.get("problem", "")
        raw_attachments = request.problem_input.get("attachments", [])
        ingested = ingest_runtime_input(raw_problem, raw_attachments, project_dir)
        ctx = TaskContext(
            task_id=task_id,
            project_dir=project_dir,
            problem_input=ingested,
            metadata={"host": "real-llm", "llm": self.config.safe_dict(), **request.metadata},
        )
        runtime = RuntimeOrchestrator(repo_root=self.repo_root, model=self.model)

        def persist_model_output(stage_name: str):
            def executor(stage_ctx: TaskContext):
                payload = stage_ctx.metadata.get("model_outputs", {}).get(stage_name, {})
                path = stage_ctx.project_dir / "runtime" / f"{stage_name}.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
                stage_ctx.register_artifact(stage_name, path)
            return executor

        stages = [
            RuntimeStage("00-start", request.instruction, persist_model_output("00-start")),
            RuntimeStage("01-analysis", "Build and validate the initial ProblemMap from the extracted problem statement and attachment inventory. Do not infer unreadable content.", persist_model_output("01-analysis")),
            RuntimeStage("02-data", "Build and validate the DataProfile from deterministic ingestion facts; identify missing data, quality risks, leakage risks, and required preprocessing.", persist_model_output("02-data")),
        ]
        manifest = runtime.run(ctx, stages)
        return HostResponse(
            status="completed",
            task_id=task_id,
            manifest=str(manifest),
            message="V0.7 ingestion + real LLM stages completed.",
            artifacts={k: str(v) for k, v in ctx.artifacts.items()},
        )
