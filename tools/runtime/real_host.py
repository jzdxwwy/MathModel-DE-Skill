"""Real LLM host adapter with V0.8 model selection and dispatch planning."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from .artifact_builder import build_data_profile, build_problem_map, build_problem_spec, persist_artifact, validate_artifact
from .host_adapter import HostRequest, HostResponse
from .input_boundary import ingest_runtime_input
from .llm_config import LLMConfig
from .model_adapter import ModelAdapter
from .orchestrator import RuntimeOrchestrator, RuntimeStage
from .providers.openai_compatible import OpenAICompatibleModelAdapter
from .task_context import TaskContext
from ..modeling.model_selector import select_models
from ..modeling.model_plan_builder import build_model_plan, build_model_spec
from .tool_dispatch import build_dispatch

class RealLLMHostAdapter:
    """Run ingestion, front-end artifacts, deterministic model selection and dispatch planning."""
    def __init__(self, repo_root: Path, model: Optional[ModelAdapter] = None, config: Optional[LLMConfig] = None):
        self.repo_root=repo_root; self.config=config or LLMConfig.from_env(); self.model=model or OpenAICompatibleModelAdapter(self.config)

    def run(self, request: HostRequest) -> HostResponse:
        task_id=request.task_id or "runtime-llm-001"; project_dir=Path(request.output_dir).resolve()
        ingested=ingest_runtime_input(request.problem_input.get("problem",""),request.problem_input.get("attachments",[]),project_dir)
        ctx=TaskContext(task_id=task_id,project_dir=project_dir,problem_input=ingested,metadata={"host":"real-llm","llm":self.config.safe_dict(),**request.metadata})
        for name,path in ingested.get("artifact_paths",{}).items(): ctx.register_artifact(f"input:{name}",Path(path))
        runtime=RuntimeOrchestrator(repo_root=self.repo_root,model=self.model)

        def save_output(stage):
            def ex(s):
                payload=s.metadata.get("model_outputs",{}).get(stage,{})
                p=s.project_dir/"runtime"/f"{stage}.json"; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str),encoding="utf-8"); s.register_artifact(stage,p)
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
        problem_map=json.loads((project_dir/"artifacts/problem-map.json").read_text(encoding="utf-8")); data_profile=json.loads((project_dir/"artifacts/data-profile.json").read_text(encoding="utf-8")); selection=select_models(problem_map,data_profile); ctx.metadata["model_selection"]=selection
        def s03(s):
            save_output("03-modeling")(s); plan=build_model_plan(selection); e=validate_artifact(self.repo_root,plan,"ModelPlan")
            if e: raise RuntimeError("03-modeling ModelPlan gate failed: "+"; ".join(e))
            pp=persist_artifact(s.project_dir,"model-plan",plan); s.register_artifact("ModelPlan",pp); spec_dir=s.project_dir/"artifacts/model-spec"; spec_dir.mkdir(parents=True,exist_ok=True)
            for item in plan["task_models"]:
                spec=build_model_spec(item,problem_map); e=validate_artifact(self.repo_root,spec,"ModelSpec")
                if e: raise RuntimeError(f"ModelSpec gate failed for {item['task_id']}: "+"; ".join(e))
                p=spec_dir/f"{item['task_id']}.json"; p.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding="utf-8"); s.register_artifact(f"ModelSpec:{item['task_id']}",p)
                candidates=[]
                for rank,c in enumerate(item["candidates"],1): candidates.append({"model_id":c["model_id"],"name":c["name"],"method":c["model_id"],"evidence":[c["fit_rationale"],f"评分={c.get('score',0)}"],"metrics":{"selection_score":c.get("score",0)},"rank":rank})
                comp={"artifact_type":"ModelComparison","schema_version":"0.8","status":"VALIDATED","task_id":item["task_id"],"candidates":candidates,"comparison_protocol":{"same_data":True,"same_metric_basis":True,"cross_validation":False,"holdout":False,"bootstrap_or_resampling":False},"decision":{"selected_model_id":item["selection"]["model_id"],"reason":item["selection"]["reason"],"tradeoffs":["实际拟合指标在V0.9计算阶段补充"]}}
                e=validate_artifact(self.repo_root,comp,"ModelComparison")
                if e: raise RuntimeError(f"ModelComparison gate failed: "+"; ".join(e))
                cp=persist_artifact(s.project_dir,f"model-comparison-{item['task_id']}",comp); s.register_artifact(f"ModelComparison:{item['task_id']}",cp)
        def s04(s):
            plan=json.loads((s.project_dir/"artifacts/model-plan.json").read_text(encoding="utf-8")); dispatch=build_dispatch(plan); e=validate_artifact(self.repo_root,dispatch,"ToolDispatchPlan")
            if e: raise RuntimeError("04-compute dispatch gate failed: "+"; ".join(e))
            p=persist_artifact(s.project_dir,"tool-dispatch",dispatch); s.register_artifact("ToolDispatchPlan",p); s.metadata["dispatch_status"]="PLANNED_ONLY"
        tail=[RuntimeStage("03-modeling","Use metadata.model_selection as authoritative. Return JSON ModelSpec proposals; do not override deterministic selected models or invent data.",s03),RuntimeStage("04-compute","Create the closed tool-dispatch plan from the validated ModelPlan. Do not execute numerical tools; V0.8 plans dispatch only.",s04)]
        runtime.run(ctx,tail); manifest=ctx.persist()
        return HostResponse(status="completed",task_id=task_id,manifest=str(manifest),message="V0.8 completed: model selection, ModelPlan/ModelSpec/ModelComparison and closed tool dispatch plan. Numerical execution is deferred to V0.9.",artifacts={k:str(v) for k,v in ctx.artifacts.items()})
