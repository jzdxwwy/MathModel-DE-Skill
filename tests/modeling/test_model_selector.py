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
