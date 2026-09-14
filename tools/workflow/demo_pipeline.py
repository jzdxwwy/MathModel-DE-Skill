"""Runnable V0 end-to-end pipeline on a tiny synthetic regression problem.

This is a production smoke path, not a contest solution. Real Stage Skills can
replace the demo runners without changing the workflow contract.
"""
from __future__ import annotations

from pathlib import Path
import json

from .engine import Stage, StageContext, WorkflowEngine, require_files


def write_json(ctx: StageContext, name: str, relative: str, payload: dict) -> None:
    path = ctx.project_dir / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    ctx.register(name, path)


def start(ctx):
    write_json(ctx, "ProblemSpec", "artifacts/problem_spec.json", {
        "problem_id": "demo-001", "type": "E", "questions": ["建立销量预测模型"],
        "attachments": ["sales.csv"], "requirements": ["给出预测结果并验证"]
    })


def analysis(ctx):
    write_json(ctx, "ProblemMap", "artifacts/problem_map.json", {
        "problem_id": "demo-001", "tasks": [{"id": "Q1", "type": "prediction", "input": ["x"], "output": ["y_hat"], "candidate_families": ["linear_regression"]}]
    })


def data(ctx):
    write_json(ctx, "DataProfile", "artifacts/data_profile.json", {
        "files": [{"name": "sales.csv", "rows": 10, "columns": ["x", "y"], "missing": 0}],
        "quality": "pass", "preprocessing": ["none"]
    })


def modeling(ctx):
    write_json(ctx, "ModelPlan", "artifacts/model_plan.json", {
        "baseline": "linear_regression", "selection_reason": "small clean dataset and interpretable relationship"
    })
    write_json(ctx, "ModelSpec", "artifacts/model_spec.json", {
        "model_id": "M1", "family": "linear_regression", "equation": "y = beta0 + beta1*x",
        "validation": "holdout", "parameters": {"beta0": 1.0, "beta1": 2.0}
    })


def compute(ctx):
    write_json(ctx, "RunManifest", "manifest/run_manifest.json", {
        "run_id": "demo-run-001", "model_id": "M1", "input": "DataProfile", "status": "success"
    })
    write_json(ctx, "ResultBundle", "results/problem_1.json", {
        "run_id": "demo-run-001", "metrics": {"rmse": 0.12, "r2": 0.98},
        "key_results": {"beta0": 1.0, "beta1": 2.0}
    })


def visualization(ctx):
    path = ctx.project_dir / "figures" / "figure_1_placeholder.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Figure 1\nGenerated from `results/problem_1.json`. Replace with real plotting tool output.\n", encoding="utf-8")
    ctx.register("FigureEvidence", path)


def verification(ctx):
    write_json(ctx, "VerificationReport", "verification/verification_report.json", {
        "status": "pass", "checks": ["formula", "metric", "provenance"],
        "evidence": ["results/problem_1.json", "manifest/run_manifest.json"]
    })


def writing(ctx):
    evidence = ctx.project_dir / "paper" / "evidence_index.md"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("""# Evidence Index\n\n- Q1 model: `artifacts/model_spec.json`\n- Q1 result: `results/problem_1.json`\n- Verification: `verification/verification_report.json`\n- Figure: `figures/figure_1_placeholder.md`\n""", encoding="utf-8")
    ctx.register("PaperEvidence", evidence)


def final(ctx):
    paper = ctx.project_dir / "paper" / "paper.md"
    paper.write_text("""# 数学建模论文（V0）\n\n## 摘要\n本文建立可解释的线性回归模型完成销量预测，并通过留出验证检查模型效果。\n\n## 模型与求解\n模型为 $y=\\beta_0+\\beta_1x$，本次运行参数为 $\\beta_0=1.0,\\beta_1=2.0$。\n\n## 结果与验证\nRMSE=0.12，R²=0.98。结果来自 `demo-run-001`，验证状态为 PASS。\n\n## 结论\n该 V0 流水线已完成从问题规格、数据档案、模型规格、计算、验证到论文证据的闭环。\n""", encoding="utf-8")
    ctx.register("Paper", paper)


def build_engine():
    return WorkflowEngine([
        Stage("00-start", [], ["ProblemSpec"], start, require_files("ProblemSpec")),
        Stage("01-analysis", ["ProblemSpec"], ["ProblemMap"], analysis, require_files("ProblemMap")),
        Stage("02-data", ["ProblemSpec", "ProblemMap"], ["DataProfile"], data, require_files("DataProfile")),
        Stage("03-modeling", ["ProblemMap", "DataProfile"], ["ModelPlan", "ModelSpec"], modeling, require_files("ModelPlan", "ModelSpec")),
        Stage("04-compute", ["ModelSpec", "DataProfile"], ["RunManifest", "ResultBundle"], compute, require_files("RunManifest", "ResultBundle")),
        Stage("05-visualization", ["ResultBundle"], ["FigureEvidence"], visualization, require_files("FigureEvidence")),
        Stage("06-verification", ["ModelSpec", "RunManifest", "ResultBundle"], ["VerificationReport"], verification, require_files("VerificationReport")),
        Stage("07-writing", ["VerificationReport", "FigureEvidence"], ["PaperEvidence"], writing, require_files("PaperEvidence")),
        Stage("final", ["PaperEvidence", "VerificationReport"], ["Paper"], final, require_files("Paper")),
    ])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="demo_run")
    args = parser.parse_args()
    ctx = StageContext(Path(args.out).resolve())
    manifest = build_engine().run(ctx)
    print(manifest)
