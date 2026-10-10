"""V0.8 deterministic task classification and model selection."""
from __future__ import annotations
from typing import Any
from .model_catalog import CATALOG

WEIGHTS = {"fit":25,"data":15,"constraints":15,"interpretability":15,"verifiability":15,"robustness":10,"cost":5}
TABULAR_FORMATS = {"csv", "tsv", "xlsx", "xls", "json"}
KEYWORDS = {
    "optimization": ("优化", "最优", "最大化", "最小化", "资源配置", "调度"),
    # "按成本与效益把对象分成几类" is not supervised classification and not
    # optimisation; without its own group it fell through to `classification`,
    # whose only family is logistic regression on a labelled target.
    "cost_benefit": ("成本", "效益", "象限"),
    "classification": ("分类", "类别", "判别", "识别"),
    "clustering": ("聚类", "分群"),
    # Comprehensive-evaluation tasks were previously unrecognisable: there was no
    # "evaluation" group at all, so 2026E 问题 1 (从四个方面评价合理性) could only
    # be misclassified as a time-series task, and no evaluation family was
    # reachable from the catalog.
    "evaluation": ("评价", "综合", "合理性", "优劣", "权重", "排序"),
    "time_series": ("时间序列", "趋势", "预测", "未来", "随时间"),
    "network": ("路径", "路网", "网络", "节点", "边", "最短"),
    "simulation": ("仿真", "模拟", "传播", "扩散", "动力学"),
    "risk": ("风险", "概率", "不确定性", "可靠性"),
    "sensitivity": ("敏感性", "影响程度", "稳健性"),
    "dimension_reduction": ("降维", "主成分", "高维"),
    "prediction": ("回归", "预测", "估计", "拟合"),
}


def classify_text(text: str, has_data: bool) -> list[str]:
    found = [k for k, words in KEYWORDS.items() if any(w.lower() in text.lower() for w in words)]
    if not found:
        found = ["prediction"] if has_data else ["mechanism"]
    return found[:3]


def classify_task(problem_map: dict[str, Any], data_profile: dict[str, Any]) -> list[str]:
    return classify_text(str(problem_map), _has_tabular_data(data_profile))


def _has_tabular_data(dp: dict[str, Any]) -> bool:
    # build_data_profile() records the extension WITH a leading dot (".xlsx"),
    # while data_binding.py already normalises it away with lstrip("."). Comparing
    # the raw value here made every real workbook look like "no data", which
    # silently pushed the whole selector onto its mechanism/simulation fallback
    # and made every data-driven model family unreachable.
    return any(
        str(a.get("format", "")).lower().lstrip(".") in TABULAR_FORMATS
        and a.get("status") != "unreadable"
        for a in dp.get("assets", [])
    )


def _candidates(task_type: str, has_data: bool) -> list[dict[str, Any]]:
    rows=[]
    for m in CATALOG:
        if task_type not in m.task_types:
            continue
        if (not has_data and m.model_id in {"linear_regression","tree_ensemble_regression","logistic_classification","tree_ensemble_classification","clustering","pca"}):
            continue
        score=round(sum(WEIGHTS[k]*m.priors.get(k,0)/5 for k in WEIGHTS),2)
        rows.append({"model_id":m.model_id,"name":m.name,"score":score,"method":m.tool,"evidence":[f"任务类型匹配：{task_type}",f"数据资产可用：{has_data}"],"assumptions":list(m.assumptions),"limitations":list(m.limitations),"baseline":m.baseline})
    rows.sort(key=lambda x:(-x["score"],not x["baseline"],x["model_id"]))
    return rows


def select_models(problem_map: dict[str, Any], data_profile: dict[str, Any]) -> dict[str, Any]:
    has_data=_has_tabular_data(data_profile)
    tasks=problem_map.get("tasks", [])
    if not tasks:
        tasks=[{"task_id":"task-1","objective":str(problem_map)}]
    result=[]
    for task in tasks:
        task_id=str(task.get("task_id"))
        text=str({"objective":task.get("objective"),"inputs":task.get("inputs"),"outputs":task.get("outputs")})
        task_types=classify_text(text,has_data)
        task_type=task_types[0]
        candidates=_candidates(task_type,has_data)
        if not candidates:
            # Nothing matched the task type at all, so fall back to generic families.
            candidates=_candidates("prediction" if has_data else "simulation",has_data)
        elif len(candidates)<2:
            # Keep the family that actually matched the task type first and only
            # append generic alternatives for comparison. The previous code replaced
            # the whole list here, which discarded the one correct family (any task
            # type backed by a single family, e.g. cost_benefit or evaluation) and
            # selected a generic predictor instead.
            seen={c["model_id"] for c in candidates}
            for extra in _candidates("prediction" if has_data else "simulation",has_data):
                if extra["model_id"] not in seen:
                    candidates.append(extra)
                    seen.add(extra["model_id"])
                if len(candidates)>=2:
                    break
        if not candidates:
            candidates=[{"model_id":"mechanism_simulation","name":"机理/动力学模拟","score":0,"method":"python.trajectory_reconstruction","evidence":["未发现可直接匹配的高置信模型，进入人工/LLM复核"],"assumptions":["需要补充可计算机理"],"limitations":["当前选择仅为占位"],"baseline":False}]
        selected=candidates[0]
        result.append({"task_id":task_id,"task_type":task_type,"candidates":candidates,"selected":selected,"reason":"先执行硬约束淘汰，再按七维权重选择得分最高者；任务类型精确匹配的族优先保留在首位，候选不足 2 个时补充通用备选用于对照；D/E仅作先验。"})
    return {"task_types":sorted({x["task_type"] for x in result}),"tasks":result,"weights":WEIGHTS}
