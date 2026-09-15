"""Deterministic catalog of reusable mathematical-model families for V0.8."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelFamily:
    model_id: str
    name: str
    task_types: tuple[str, ...]
    tool: str
    baseline: bool = False
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    priors: dict[str, float] = field(default_factory=dict)


CATALOG = (
    ModelFamily("linear_regression", "线性回归", ("prediction", "evaluation"), "python.baseline_regression", True, ("连续响应变量可建模",), ("非线性关系可能拟合不足",), {"fit": 4,"data": 5,"constraints": 4,"interpretability": 5,"verifiability": 5,"robustness": 3,"cost": 5}),
    ModelFamily("tree_ensemble_regression", "树集成回归", ("prediction", "evaluation"), "python.model_compare", False, ("样本量足以支持非线性拟合",), ("解释性低于线性模型",), {"fit": 5,"data": 4,"constraints": 3,"interpretability": 3,"verifiability": 4,"robustness": 4,"cost": 3}),
    ModelFamily("logistic_classification", "逻辑回归分类", ("classification",), "python.classification_cv", True, ("目标为离散类别",), ("复杂非线性边界能力有限",), {"fit": 4,"data": 4,"constraints": 4,"interpretability": 5,"verifiability": 5,"robustness": 4,"cost": 5}),
    ModelFamily("tree_ensemble_classification", "树集成分类", ("classification",), "python.classification_cv", False, ("目标为离散类别",), ("模型解释需要额外分析",), {"fit": 5,"data": 4,"constraints": 3,"interpretability": 3,"verifiability": 4,"robustness": 4,"cost": 3}),
    ModelFamily("time_series_baseline", "时间序列基线", ("time_series", "prediction"), "python.time_series_cv", True, ("存在有序时间索引",), ("结构突变时稳定性下降",), {"fit": 4,"data": 5,"constraints": 4,"interpretability": 5,"verifiability": 5,"robustness": 4,"cost": 5}),
    ModelFamily("clustering", "聚类分析", ("clustering", "evaluation"), "python.model_compare", True, ("存在可比较的数值特征",), ("需要选择距离或相似度",), {"fit": 4,"data": 4,"constraints": 3,"interpretability": 4,"verifiability": 4,"robustness": 3,"cost": 4}),
    ModelFamily("pca", "主成分分析", ("dimension_reduction", "evaluation"), "python.model_compare", True, ("多个相关数值变量",), ("降维后的解释需要谨慎",), {"fit": 3,"data": 4,"constraints": 4,"interpretability": 4,"verifiability": 4,"robustness": 4,"cost": 5}),
    ModelFamily("optimization", "约束优化", ("optimization", "decision"), "python.optimization", True, ("存在明确目标函数与约束",), ("依赖目标函数与约束质量",), {"fit": 5,"data": 4,"constraints": 5,"interpretability": 5,"verifiability": 5,"robustness": 4,"cost": 4}),
    ModelFamily("shortest_path", "最短路径/网络优化", ("network", "optimization"), "python.graph_shortest_path", True, ("网络可表示为节点与边",), ("无法表达非网络型任务",), {"fit": 5,"data": 4,"constraints": 5,"interpretability": 5,"verifiability": 5,"robustness": 5,"cost": 5}),
    ModelFamily("monte_carlo", "蒙特卡洛模拟", ("simulation", "risk", "uncertainty"), "python.monte_carlo", True, ("概率机制或不确定性可定义",), ("结果依赖随机机制与重复次数",), {"fit": 4,"data": 3,"constraints": 4,"interpretability": 4,"verifiability": 5,"robustness": 5,"cost": 3}),
    ModelFamily("sensitivity", "敏感性分析", ("sensitivity", "risk", "evaluation"), "python.sensitivity", True, ("存在可扰动参数或输入",), ("不能单独替代主模型",), {"fit": 4,"data": 4,"constraints": 4,"interpretability": 5,"verifiability": 5,"robustness": 5,"cost": 5}),
    ModelFamily("mechanism_simulation", "机理/动力学模拟", ("mechanism", "simulation"), "python.trajectory_reconstruction", False, ("存在可计算的状态转移或机理关系",), ("机理假设和参数需验证",), {"fit": 5,"data": 3,"constraints": 5,"interpretability": 5,"verifiability": 4,"robustness": 3,"cost": 2}),
)

BY_ID = {m.model_id: m for m in CATALOG}
