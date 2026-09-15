"""V0.9-B adapters for executing approved Python templates with explicit bindings.

The LLM may propose semantic bindings, but this layer only accepts explicit
paths/columns supplied by the dispatch. It never guesses a target column.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


class InputBlocked(RuntimeError):
    """Raised when a numerical template cannot be safely bound to real data."""


@dataclass
class TemplateExecutionResult:
    outputs: list[dict[str, Any]]
    metrics: dict[str, Any]
    artifacts: list[dict[str, str]]
    stdout: str = ""
    stderr: str = ""


def _load_module(path: Path):
    name = f"mathmodel_template_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load template: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _resolve_data_path(project_dir: Path, binding: dict[str, Any]) -> Path:
    raw = binding.get("data_path")
    if not raw:
        raise InputBlocked("data_path is required; refusing to guess an input asset")
    path = Path(raw)
    if not path.is_absolute():
        path = (project_dir / path).resolve()
    if not path.exists() or not path.is_file():
        raise InputBlocked(f"data_path does not exist: {path}")
    return path


def _prepare_csv(data_path: Path, run_dir: Path) -> Path:
    if data_path.suffix.lower() == ".csv":
        return data_path
    if data_path.suffix.lower() in {".tsv", ".txt"}:
        df = pd.read_csv(data_path, sep="\t")
    elif data_path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(data_path, sheet_name=0)
    else:
        raise InputBlocked(f"template adapter does not support tabular format: {data_path.suffix}")
    csv_path = run_dir / "data" / "input.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    return csv_path


def execute_tabular_template(repo_root: Path, project_dir: Path, run_dir: Path, model_id: str, binding: dict[str, Any]) -> TemplateExecutionResult:
    """Execute one of the existing E-type tabular templates.

    Supported now: linear regression, model comparison and logistic
    classification. Other tools remain explicitly INPUT_BLOCKED until their
    own mathematical input contract is defined.
    """
    template_map = {
        "linear_regression": "baseline_regression.py",
        "tree_ensemble_regression": "model_compare.py",
        "logistic_classification": "classification_cv.py",
        "tree_ensemble_classification": "classification_cv.py",
    }
    filename = template_map.get(model_id)
    if filename is None:
        raise InputBlocked(f"no V0.9-B tabular adapter for model: {model_id}")

    data_path = _resolve_data_path(project_dir, binding)
    csv_path = _prepare_csv(data_path, run_dir)
    target = binding.get("target")
    if not target:
        raise InputBlocked("target is required; refusing to infer the dependent variable")

    features = binding.get("features", [])
    if not isinstance(features, list):
        raise InputBlocked("features must be an explicit list when provided")
    df = pd.read_csv(csv_path)
    missing = [c for c in [target, *features] if c not in df.columns]
    if missing:
        raise InputBlocked(f"columns not found: {missing}")
    if not features:
        features = [c for c in df.columns if c != target]
    if not features:
        raise InputBlocked("no predictor columns remain after excluding target")

    module = _load_module(repo_root / "05_python" / "templates" / filename)
    module.DATA_PATH = csv_path
    module.TARGET = target
    module.FEATURES = features
    if "seed" in binding:
        module.SEED = int(binding["seed"])
    if "test_size" in binding and hasattr(module, "TEST_SIZE"):
        module.TEST_SIZE = float(binding["test_size"])
    if "n_splits" in binding and hasattr(module, "N_SPLITS"):
        module.N_SPLITS = int(binding["n_splits"])

    old_cwd = Path.cwd()
    old_env = os.environ.get("MATHMODEL_RUN_DIR")
    os.environ["MATHMODEL_RUN_DIR"] = str(run_dir)
    try:
        os.chdir(run_dir)
        module.main()
    finally:
        os.chdir(old_cwd)
        if old_env is None:
            os.environ.pop("MATHMODEL_RUN_DIR", None)
        else:
            os.environ["MATHMODEL_RUN_DIR"] = old_env

    artifacts_dir = run_dir / "results"
    artifacts = []
    if artifacts_dir.exists():
        for path in sorted(artifacts_dir.iterdir()):
            if path.is_file():
                artifacts.append({"kind": path.suffix.lstrip(".") or "file", "path": str(path), "description": "template output"})
    metrics: dict[str, Any] = {}
    for candidate in [artifacts_dir / "model_comparison.csv", artifacts_dir / "classification_cv.csv", artifacts_dir / "run_manifest.json", artifacts_dir / "model_comparison_manifest.json", artifacts_dir / "classification_cv_manifest.json"]:
        if candidate.exists() and candidate.suffix == ".json":
            try:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
                metrics.update(payload.get("mean_metrics", {}))
                notes = payload.get("notes")
                if isinstance(notes, str):
                    try:
                        metrics.update(json.loads(notes).get("metrics", {}))
                    except Exception:
                        pass
            except Exception:
                pass
    return TemplateExecutionResult(outputs=[{"name": "template_execution", "value": "completed", "unit": "status", "source_ref": str(run_dir)}], metrics=metrics, artifacts=artifacts)
