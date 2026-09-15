"""Build schema-oriented ModelPlan/ModelSpec artifacts from deterministic selection."""
from __future__ import annotations
from typing import Any
from .model_catalog import BY_ID


def build_model_plan(selection: dict[str, Any], prior: str = "NONE") -> dict[str, Any]:
    task_models=[]
    for item in selection.get("tasks", []):
        candidates=[{"model_id":c["model_id"],"name":c["name"],"fit_rationale":c["evidence"][0],"assumptions":c.get("assumptions",[]),"limitations":c.get("limitations",[]),"score":c.get("score",0)} for c in item["candidates"]]
        task_models.append({"task_id":item["task_id"],"candidates":candidates,"selection":{"model_id":item["selected"]["model_id"],"reason":item["reason"],"alternatives_rejected":[c["model_id"] for c in candidates[1:]]}})
    return {"artifact_type":"ModelPlan","schema_version":"0.8","status":"VALIDATED","task_models":task_models,"selection_principles":["确定性七维评分优先于LLM主观猜测","先硬约束淘汰，再比较候选模型","保留基线与至少一个可比较备选","D/E仅作为先验，不作为固定工作流"],"d_or_e_prior":prior}


def build_model_spec(task: dict[str, Any], problem_map: dict[str, Any]) -> dict[str, Any]:
    model_id=task["selection"]["model_id"]
    model=BY_ID[model_id]
    task_id=task["task_id"]
    objective=f"针对任务 {task_id}，使用{model.name}建立可验证模型并服务于题目目标。"
    return {"artifact_type":"ModelSpec","schema_version":"0.8","status":"DRAFT","model_id":model_id,"task_id":task_id,"name":model.name,"objective":objective,"variables":[{"symbol":"X","role":"input","meaning":"由题目或数据确定的输入变量"},{"symbol":"Y","role":"target","meaning":"任务对应的目标量"}],"parameters":[],"equations":[f"{model.name}的模型方程由后续计算阶段根据真实数据/机理确定"],"constraints":[],"assumptions":list(model.assumptions),"solution_method":model.tool,"validation_plan":["留出或交叉验证（适用时）","与基线模型比较","残差/误差或约束满足性检查","敏感性或稳健性检查（适用时）"],"limitations":list(model.limitations)}
