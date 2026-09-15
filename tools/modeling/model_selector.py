"""V0.8 deterministic task classification and model selection."""
from __future__ import annotations
from dataclasses import asdict
from typing import Any
from .model_catalog import CATALOG, ModelFamily

WEIGHTS = {"fit":25,"data":15,"constraints":15,"interpretability":15,"verifiability":15,"robustness":10,"cost":5}
KEYWORDS = {
    "optimization": ("优化", "最优", "最大化", "最小化", "资源配置", "调度"),
    "classification": ("分类", "类别", "判别", "识别"),
    "clustering": ("聚类", "分群", "客户群"),
    "time_series": ("时间序列", "趋势", "预测", "未来", "随时间"),
    "network": ("路径", "路网", "网络", "节点", "边", "最短"),
    "simulation": ("仿真", "模拟", "传播", "扩散", "动力学"),
    "risk": ("风险", "概率", "不确定性", "可靠性"),
    "sensitivity": ("敏感性", "影响程度", "稳健性"),
    "dimension_reduction": ("降维", "主成分", "高维"),
    "prediction": ("回归", "预测", "估计", "拟合"),
}


def _text(problem_map: dict[str, Any]) -> str:
    return str(problem_map).lower()


def classify_task(problem_map: dict[str, Any], data_profile: dict[str, Any]) -> list[str]:
    text = _text(problem_map)
    found = [k for k, words in KEYWORDS.items() if any(w.lower() in text for w in words)]
    if not found:
        found = ["prediction"] if data_profile.get("assets") else ["mechanism"]
    return found[:3]


def _has_tabular_data(dp: dict[str, Any]) -> bool:
    return any(a.get("format", "").lower() in {"csv","tsv","xlsx","xls","json"} and a.get("status") != "unreadable" for a in dp.get("assets", []))


def select_models(problem_map: dict[str, Any], data_profile: dict[str, Any]) -> dict[str, Any]:
    task_types = classify_task(problem_map, data_profile)
    has_data = _has_tabular_data(data_profile)
    out = {}
    for task_type in task_types:
        candidates = []
        for m in CATALOG:
            if task_type not in m.task_types:
                continue
            hard_reject = (not has_data and m.model_id in {"linear_regression","tree_ensemble_regression","logistic_classification","tree_ensemble_classification","clustering","pca"})
            if hard_reject:
                continue
            score = round(sum(WEIGHTS[k] * m.priors.get(k, 0) / 5 for k in WEIGHTS), 2)
            candidates.append({"model_id":m.model_id,"name":m.name,"score":score,"method":m.tool,"evidence":[f"任务类型匹配：{task_type}", f"数据资产可用：{has_data}"],"assumptions":list(m.assumptions),"limitations":list(m.limitations),"baseline":m.baseline})
        candidates.sort(key=lambda x:(-x["score"], not x["baseline"], x["model_id"]))
        if len(candidates) == 1:
            # Comparison artifacts require >=2 candidates; add the nearest compatible family.
            for m in CATALOG:
                if m.model_id != candidates[0]["model_id"] and set(m.task_types) & {task_type}:
                    candidates.append({"model_id":m.model_id,"name":m.name,"score":round(sum(WEIGHTS[k]*m.priors.get(k,0)/5 for k in WEIGHTS),2),"method":m.tool,"evidence":[f"任务类型匹配：{task_type}","备选模型"],"assumptions":list(m.assumptions),"limitations":list(m.limitations),"baseline":m.baseline})
                    break
        if not candidates:
            continue
        selected = candidates[0]
        out[task_type] = {"task_type":task_type,"candidates":candidates,"selected":selected,"reason":f"按预设七维权重选择得分最高模型；保留基线与可比较备选。"}
    return {"task_types":task_types,"tasks":out,"weights":WEIGHTS}
