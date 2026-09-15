"""Real LLM host adapter through V0.9-D deterministic binding and numerical execution."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from .artifact_builder import build_data_profile, build_problem_map, build_problem_spec, persist_artifact, validate_artifact
from .execution_engine import ToolExecutionEngine
from .host_adapter import HostRequest, HostResponse
from .input_boundary import ingest_runtime_input
from .llm_config import LLMConfig
from .model_adapter import ModelAdapter
from .orchestrator import RuntimeOrchestrator, RuntimeStage
from .task_context import TaskContext
from .providers.openai_compatible import OpenAICompatibleModelAdapter
from ..modeling.model_selector import select_models
from ..modeling.model_plan_builder import build_model_plan, build_model_spec
from ..modeling.data_binding import resolve_binding
from .tool_dispatch import build_dispatch
from .v09_tools import register_default_tools


def _proposal_for_task(output: object, task_id: str) -> dict:
    if not isinstance(output, dict):
        return {}
    items = output.get("task_models")
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and item.get("task_id") == task_id:
                return item
    if output.get("task_id") == task_id:
        return output
    return {}


class RealLLMHostAdapter:
    """Run ingestion, semantic front-end, deterministic selection, binding and compute."""
    def __init__(self, repo_root: Path, model: Optional[ModelAdapter] = None, config: Optional[LLMConfig] = None):
        self.repo_root=repo_root
        self.config=config or LLMConfig.from_env()
        self.model=model or OpenAICompatibleModelAdapter(self.config)

    def run(self, request: HostRequest) -> HostResponse:
        task_id=request.task_id or "runtime-llm-001"
        project_dir=Path(request.output_dir).resolve()
        ingested=ingest_runtime_input(request.problem_input.get("problem",""),request.problem_input.get("attachments",[]),project_dir)
        ctx=TaskContext(task_id=task_id,project_dir=project_dir,problem_input=ingested,metadata={"host":"real-llm","llm":self.config.safe_dict(),**request.metadata})
        for name,path in ingested.get("artifact_paths",{}).items():
            ctx.register_artifact(f"input:{name}",Path(path))
        runtime=RuntimeOrchestrator(repo_root=self.repo_root,model=self.model)

        def save_output(stage):
            def ex(s):
                payload=s.metadata.get("model_outputs",{}).get(stage,{})
                p=s.project_dir/"runtime"/f"{stage}.json"
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
                s.register_artifact(stage,p)
            return ex
        def s00(s):
            save_output("00-start")(s); a,e=build_problem_spec(self.repo_root,s.metadata["model_outputs"]["00-start"].get("output",{}),s.problem_input); p=persist_artifact(s.project_dir,"problem-spec",a); s.register_artifact("ProblemSpec",p)
            if e: raise RuntimeError("00-start gate failed: "+"; ".join(e))
        def s01(s):
            save_output("01-analysis")(s); spec=json.loads((s.project_dir/"artifacts/problem-spec.json").read_text(encoding="utf-8")); a,e=build_problem_map(self.repo_root,s.metadata["model_outputs"]["01-analysis"].get("output",{}),spec); p=persist_artifact(s.project_dir,"problem-map",a); s.register_artifact("ProblemMap",p)
            if e: raise RuntimeError("01-analysis gate failed: "+"; ".join(e))
        def s02(s):
            save_output("02-data")(s); a,e=build_data_profile(self.repo_root,s.problem_input["data_profile"],s.metadata["model_outputs"]["02-data"].get("output",{})); p=persist_artifact(s.project_dir,"data-profile",a); s.register_artifact("DataProfile",p)
            if e: raise RuntimeError("02-data gate failed: "+"; ".join(e))
        stages=[
            RuntimeStage("00-start",request.instruction+"\nReturn ONLY JSON ProblemSpec. Required: artifact_type, schema_version, status, problem_id, source{title,mode}, tasks[]. Never invent missing data.",s00),
            RuntimeStage("01-analysis","Return ONLY JSON ProblemMap. Map every ProblemSpec task exactly once with identical task_id. Required task_id, objective, inputs, outputs.",s01),
            RuntimeStage("02-data","Return ONLY JSON semantic DataProfile additions. Deterministic ingestion facts are authoritative; do not rewrite them.",s02)]
        runtime.run(ctx,stages)
        problem_map=json.loads((project_dir/"artifacts/problem-map.json").read_text(encoding="utf-8"))
        data_profile=json.loads((project_dir/"artifacts/data-profile.json").read_text(encoding="utf-8"))
        selection=select_models(problem_map,data_profile)
        ctx.metadata["model_selection"]=selection
        proposal_output={}

        def s03(s):
            nonlocal proposal_output
            save_output("03-modeling")(s)
            proposal_output=s.metadata["model_outputs"]["03-modeling"].get("output",{})
            plan=build_model_plan(selection)
            spec_dir=s.project_dir/"artifacts/model-spec"; spec_dir.mkdir(parents=True,exist_ok=True)
            for item in plan["task_models"]:
                proposal=_proposal_for_task(proposal_output,item["task_id"])
                task=next((t for t in problem_map.get("tasks",[]) if t.get("task_id")==item["task_id"]),{})
                binding=resolve_binding(item["selection"]["model_id"],task,data_profile,proposal)
                item["data_binding"]=binding
                resolved_proposal=dict(proposal)
                resolved_proposal["data_binding"]=binding
                spec=build_model_spec(item,problem_map,resolved_proposal)
                e=validate_artifact(self.repo_root,spec,"ModelSpec")
                if e: raise RuntimeError(f"ModelSpec gate failed for {item['task_id']}: "+"; ".join(e))
                p=spec_dir/f"{item['task_id']}.json"; p.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding="utf-8"); s.register_artifact(f"ModelSpec:{item['task_id']}",p)
                candidates=[]
                for rank,c in enumerate(item["candidates"],1): candidates.append({"model_id":c["model_id"],"name":c["name"],"method":c["model_id"],"evidence":[c["fit_rationale"],f"评分={c.get('score',0)}"],"metrics":{"selection_score":c.get('score',0)},"rank":rank})
                comp={"artifact_type":"ModelComparison","schema_version":"0.8","status":"VALIDATED","task_id":item["task_id"],"candidates":candidates,"comparison_protocol":{"same_data":True,"same_metric_basis":True,"cross_validation":False,"holdout":False,"bootstrap_or_resampling":False},"decision":{"selected_model_id":item["selection"]["model_id"],"reason":item["selection"]["reason"],"tradeoffs":["实际拟合指标在V0.9计算阶段补充"]}}
                e=validate_artifact(self.repo_root,comp,"ModelComparison")
                if e: raise RuntimeError(f"ModelComparison gate failed: "+"; ".join(e))
                cp=persist_artifact(s.project_dir,f"model-comparison-{item['task_id']}",comp); s.register_artifact(f"ModelComparison:{item['task_id']}",cp)
            plan["status"]="VALIDATED"
            pp=persist_artifact(s.project_dir,"model-plan",plan); s.register_artifact("ModelPlan",pp)

        def s04(s):
            plan=json.loads((s.project_dir/"artifacts/model-plan.json").read_text(encoding="utf-8"))
            dispatch=build_dispatch(plan)
            e=validate_artifact(self.repo_root,dispatch,"ToolDispatchPlan")
            if e: raise RuntimeError("04-compute dispatch gate failed: "+"; ".join(e))
            p=persist_artifact(s.project_dir,"tool-dispatch",dispatch); s.register_artifact("ToolDispatchPlan",p)
            registry=__import__(".tool_registry",package=__package__,fromlist=["ToolRegistry"]).ToolRegistry()
            register_default_tools(registry)
            engine=ToolExecutionEngine(self.repo_root,registry)
            executions=engine.execute(dispatch,project_dir,request.problem_input.get("problem", ""))
            ep=s.project_dir/"artifacts/v09-execution.json"; ep.write_text(json.dumps(executions,ensure_ascii=False,indent=2),encoding="utf-8"); s.register_artifact("V09Execution",ep)
            s.metadata["dispatch_status"]="EXECUTED"
        tail=[RuntimeStage("03-modeling","Use metadata.model_selection as authoritative. Return JSON task_models with optional semantic binding hints only (target/features/source/target/time_col). Never guess or override selected models; every proposed column/path must be checkable against DataProfile.",s03),RuntimeStage("04-compute","Execute the closed dispatch through registered tools. BLOCKED bindings remain fail-closed as INPUT_BLOCKED; never fabricate data.",s04)]
        runtime.run(ctx,tail)
        manifest=ctx.persist()
        return HostResponse(status="completed",task_id=task_id,manifest=str(manifest),message="V0.9-D completed: deterministic DataProfile-to-binding resolution, binding gate, numerical dispatch, and fail-closed execution.",artifacts={k:str(v) for k,v in ctx.artifacts.items()})
