"""Real LLM host adapter with V0.7-B structured Artifact generation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .artifact_builder import build_data_profile, build_problem_map, build_problem_spec, persist_artifact
from .host_adapter import HostRequest, HostResponse
from .input_boundary import ingest_runtime_input
from .llm_config import LLMConfig
from .model_adapter import ModelAdapter
from .orchestrator import RuntimeOrchestrator, RuntimeStage
from .providers.openai_compatible import OpenAICompatibleModelAdapter
from .task_context import TaskContext


class RealLLMHostAdapter:
    """Run deterministic ingestion followed by model-backed front-end artifacts."""

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
        for name, path in ingested.get("artifact_paths", {}).items():
            ctx.register_artifact(f"input:{name}", Path(path))
        runtime = RuntimeOrchestrator(repo_root=self.repo_root, model=self.model)

        def persist_model_output(stage_name: str):
            def executor(stage_ctx: TaskContext):
                payload = stage_ctx.metadata.get("model_outputs", {}).get(stage_name, {})
                path = stage_ctx.project_dir / "runtime" / f"{stage_name}.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
                stage_ctx.register_artifact(stage_name, path)
            return executor

        def stage_00(stage_ctx: TaskContext):
            persist_model_output("00-start")(stage_ctx)
            output = stage_ctx.metadata["model_outputs"]["00-start"].get("output", {})
            artifact, errors = build_problem_spec(self.repo_root, output, stage_ctx.problem_input)
            path = persist_artifact(stage_ctx.project_dir, "problem-spec", artifact)
            stage_ctx.register_artifact("ProblemSpec", path)
            if errors:
                raise RuntimeError("00-start ProblemSpec gate failed: " + "; ".join(errors))

        def stage_01(stage_ctx: TaskContext):
            persist_model_output("01-analysis")(stage_ctx)
            output = stage_ctx.metadata["model_outputs"]["01-analysis"].get("output", {})
            spec = json.loads((stage_ctx.project_dir / "artifacts" / "problem-spec.json").read_text(encoding="utf-8"))
            artifact, errors = build_problem_map(self.repo_root, output, spec)
            path = persist_artifact(stage_ctx.project_dir, "problem-map", artifact)
            stage_ctx.register_artifact("ProblemMap", path)
            if errors:
                raise RuntimeError("01-analysis ProblemMap gate failed: " + "; ".join(errors))

        def stage_02(stage_ctx: TaskContext):
            persist_model_output("02-data")(stage_ctx)
            output = stage_ctx.metadata["model_outputs"]["02-data"].get("output", {})
            artifact, errors = build_data_profile(self.repo_root, stage_ctx.problem_input["data_profile"], output)
            path = persist_artifact(stage_ctx.project_dir, "data-profile", artifact)
            stage_ctx.register_artifact("DataProfile", path)
            if errors:
                raise RuntimeError("02-data DataProfile gate failed: " + "; ".join(errors))

        stages = [
            RuntimeStage(
                "00-start",
                request.instruction + "\nReturn ONLY JSON for a ProblemSpec artifact. Required: artifact_type=ProblemSpec, schema_version, status, problem_id, source{title,mode}, tasks[]. Use only extracted facts; never invent missing data.",
                stage_00,
            ),
            RuntimeStage(
                "01-analysis",
                "Return ONLY JSON for a ProblemMap artifact. Map every ProblemSpec task exactly once with the same task_id. Required task fields: task_id, objective, inputs, outputs. Do not infer unreadable content.",
                stage_01,
            ),
            RuntimeStage(
                "02-data",
                "Return ONLY JSON for semantic DataProfile additions. Deterministic asset facts are authoritative and will be merged separately. You may add data_risks and gate_decision, but do not rewrite paths, sizes, schemas, missingness or duplicate facts.",
                stage_02,
            ),
        ]
        manifest = runtime.run(ctx, stages)
        return HostResponse(
            status="completed",
            task_id=task_id,
            manifest=str(manifest),
            message="V0.7-B ingestion + structured ProblemSpec/ProblemMap/DataProfile generation completed.",
            artifacts={k: str(v) for k, v in ctx.artifacts.items()},
        )
