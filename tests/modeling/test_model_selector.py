"""Offline V0.8 selector contract tests. Not executed in this environment."""
from tools.modeling.model_selector import select_models


def test_selector_preserves_task_ids_and_returns_candidates():
    problem_map={"tasks":[{"task_id":"Q1","objective":"预测指标趋势","inputs":["data"],"outputs":["forecast"]}]}
    data_profile={"assets":[{"format":"csv","status":"ok"}]}
    result=select_models(problem_map,data_profile)
    assert result["tasks"][0]["task_id"]=="Q1"
    assert len(result["tasks"][0]["candidates"])>=2
    assert result["tasks"][0]["selected"]["model_id"] in {c["model_id"] for c in result["tasks"][0]["candidates"]}


def test_selector_rejects_tabular_models_without_tabular_asset():
    problem_map={"tasks":[{"task_id":"Q1","objective":"分类识别","inputs":[],"outputs":[]}]}
    result=select_models(problem_map,{"assets":[]})
    ids={c["model_id"] for c in result["tasks"][0]["candidates"]}
    assert "logistic_classification" not in ids


def test_selector_treats_dotted_extension_as_tabular_data():
    """Regression: build_data_profile() stores the extension as ".xlsx", but the
    selector compared it against "xlsx". Every real profiled workbook was therefore
    reported as "no data", which pushed the selector onto its mechanism/simulation
    fallback and made all data-driven model families unreachable."""
    problem_map = {"tasks": [{"task_id": "Q1", "objective": "对关键词进行分类", "inputs": [], "outputs": []}]}
    dotted = {"assets": [{"format": ".xlsx", "status": "READABLE"}]}
    plain = {"assets": [{"format": "xlsx", "status": "READABLE"}]}

    dotted_candidates = select_models(problem_map, dotted)["tasks"][0]
    plain_candidates = select_models(problem_map, plain)["tasks"][0]

    assert {c["model_id"] for c in dotted_candidates["candidates"]} == \
           {c["model_id"] for c in plain_candidates["candidates"]}
    assert "logistic_classification" in {c["model_id"] for c in dotted_candidates["candidates"]}
    assert dotted_candidates["selected"]["model_id"] == "logistic_classification"


def test_evaluation_tasks_reach_the_evaluation_family():
    """KEYWORDS had no "评价" group, so 2026E 问题 1 (从四个方面评价合理性) could
    only be misclassified as a time-series task and no evaluation family was
    reachable from the catalog at all."""
    problem_map = {"tasks": [{
        "task_id": "E1",
        "objective": "从广告的设计质量与创意、出价策略与预算等方面评价该公司SEM广告投放策略的合理性",
        "inputs": [], "outputs": [],
    }]}
    data_profile = {"assets": [{"format": ".xlsx", "status": "READABLE"}]}

    task = select_models(problem_map, data_profile)["tasks"][0]

    assert task["task_type"] == "evaluation"
    assert "entropy_topsis" in {c["model_id"] for c in task["candidates"]}
