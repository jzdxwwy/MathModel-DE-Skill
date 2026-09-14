"""Minimal evidence-driven paper builder.

V0 deliberately builds Markdown first. A DOCX/PDF renderer can consume the
same evidence package later, keeping writing separate from computation.
"""
from __future__ import annotations

from pathlib import Path
import json


def build_paper(project_dir: str | Path, output: str = "paper/paper.md") -> Path:
    root = Path(project_dir)
    result = json.loads((root / "results/problem_1.json").read_text(encoding="utf-8"))
    verification = json.loads((root / "verification/verification_report.json").read_text(encoding="utf-8"))
    model = json.loads((root / "artifacts/model_spec.json").read_text(encoding="utf-8"))
    paper = root / output
    paper.parent.mkdir(parents=True, exist_ok=True)
    paper.write_text(
        f"""# 数学建模论文\n\n## 摘要\n针对题目中的预测任务，建立{model['family']}模型，并依据真实运行结果进行验证。\n\n## 1 问题分析\n本研究将任务抽象为可解释的预测问题。\n\n## 2 模型建立\n模型：`{model['equation']}`。\n\n## 3 模型求解\n运行编号：`{result['run_id']}`。关键参数：`{result['key_results']}`。\n\n## 4 结果与验证\nRMSE={result['metrics']['rmse']}，R²={result['metrics']['r2']}。验证状态：**{verification['status'].upper()}**。\n\n## 5 结论\n模型结果及其验证证据均可通过 Evidence Index 追溯。\n""",
        encoding="utf-8",
    )
    return paper
