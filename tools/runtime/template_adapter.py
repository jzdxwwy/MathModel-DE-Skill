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


def _resolve_sheet(binding: dict[str, Any]) -> Any:
    """Sheet selector for an Excel binding: a name ("Sheet2") or a 0-based index.

    Defaults to the first sheet. Before this existed every workbook silently
    resolved to sheet 0, so the registration table (Sheet2) and the keyword table
    (Sheet3) of a real CUMCM attachment were unreachable from the compute stage
    even though ingestion had already profiled them as separate assets.
    """
    sheet = binding.get("sheet")
    return 0 if sheet is None else sheet


def _prepare_csv(data_path: Path, run_dir: Path, sheet: Any = None) -> Path:
    if data_path.suffix.lower() == ".csv":
        return data_path
    if data_path.suffix.lower() in {".tsv", ".txt"}:
        df = pd.read_csv(data_path, sep="\t")
    elif data_path.suffix.lower() in {".xlsx", ".xls"}:
        try:
            df = pd.read_excel(data_path, sheet_name=0 if sheet is None else sheet)
        except ValueError as exc:
            raise InputBlocked(f"cannot read sheet {sheet!r} from {data_path.name}: {exc}") from exc
    else:
        raise InputBlocked(f"template adapter does not support tabular format: {data_path.suffix}")
    # Real attachments carry header padding: 2026E Sheet2 is "新注册数 " with a
    # trailing space, while DataProfile records the stripped name. Normalising here
    # keeps a binding written against the DataProfile column name working.
    df.columns = [str(c).strip() for c in df.columns]
    csv_path = run_dir / "data" / "input.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    return csv_path


# Which model family maps to which template, including families the catalog
# advertises but that have nothing data-driven behind them. They are listed
# explicitly so the refusal is precise instead of a bare "no adapter", and so
# that nobody closes the gap by wiring up a demonstrator.
MODEL_TEMPLATE: dict[str, str | None] = {
    "linear_regression": "baseline_regression.py",
    "tree_ensemble_regression": "model_compare.py",
    "logistic_classification": "classification_cv.py",
    "tree_ensemble_classification": "classification_cv.py",
    "time_series_baseline": "time_series_cv.py",
    "optimization": "optimization.py",
    "monte_carlo": "monte_carlo.py",
    "sensitivity": "sensitivity.py",
    "mechanism_simulation": "trajectory_reconstruction.py",
    "shortest_path": "graph_shortest_path.py",
    "clustering": None,
    "pca": None,
}

# How a template can be driven.
TEMPLATE_CAPABILITIES: dict[str, str] = {
    "baseline_regression.py": "native",
    "model_compare.py": "native",
    "classification_cv.py": "native",
    "time_series_cv.py": "native",
    # Data-driven, but driven through a CLI argument contract (--input,
    # --entity-col, ...) instead of module attributes.
    "trajectory_reconstruction.py": "argv",
    # TARGET here is the destination node, not a dependent-variable column, so it
    # needs its own invocation path rather than the generic tabular one.
    "graph_shortest_path.py": "network",
    # Demonstrators. The objective/event is hard-coded and no external input is
    # read, so running one against a real binding would emit fabricated numbers
    # with a valid-looking run manifest and a RUN_COMPLETE status.
    "optimization.py": "toy",
    "monte_carlo.py": "toy",
    "sensitivity.py": "toy",
    "stochastic_coverage_optimization.py": "toy",
}

_REFUSAL_REASONS = {
    "argv": "{model} maps to {template}, which is driven through a CLI argument contract; "
            "this adapter does not implement that invocation path yet.",
    "network": "{model} maps to {template}, where TARGET is the destination node rather than a "
               "dependent-variable column; it needs its own invocation path.",
    "toy": "{model} maps to {template}, a demonstrator whose objective is hard-coded and which "
           "reads no external input. Running it against real data would fabricate a result, so "
           "it is refused until a data-driven template exists.",
}


def _resolve_template(model_id: str) -> str:
    if model_id not in MODEL_TEMPLATE:
        raise InputBlocked(f"no V0.9-B tabular adapter for model: {model_id}")
    filename = MODEL_TEMPLATE[model_id]
    if filename is None:
        raise InputBlocked(
            f"{model_id} has no data-driven implementation in 05_python/templates; the catalog "
            f"points it at a template that does something else (model_compare.py is a regression "
            f"comparison, not clustering or PCA)."
        )
    kind = TEMPLATE_CAPABILITIES.get(filename, "native")
    if kind in _REFUSAL_REASONS:
        raise InputBlocked(_REFUSAL_REASONS[kind].format(model=model_id, template=filename))
    return filename


def execute_tabular_template(repo_root: Path, project_dir: Path, run_dir: Path, model_id: str, binding: dict[str, Any]) -> TemplateExecutionResult:
    """Execute one of the existing E-type tabular templates.

    Runnable families: linear regression, model comparison, (tree-ensemble)
    classification and the time-series rolling baseline. Every other catalog
    family is refused with an explicit reason; see MODEL_TEMPLATE and
    TEMPLATE_CAPABILITIES above.
    """
    filename = _resolve_template(model_id)

    # Templates are executed with the run directory as CWD, so it must exist
    # before the adapter chdirs into it. CSV inputs previously skipped the
    # directory creation performed by _prepare_csv.
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    data_path = _resolve_data_path(project_dir, binding)
    csv_path = _prepare_csv(data_path, run_dir, _resolve_sheet(binding))
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
    for attr, key, cast in (
        ("SEED", "seed", int),
        ("TEST_SIZE", "test_size", float),
        ("N_SPLITS", "n_splits", int),
        ("TIME_COL", "time_col", str),
        ("TEST_HORIZON", "test_horizon", int),
        ("MIN_TRAIN", "min_train", int),
    ):
        if key in binding and hasattr(module, attr):
            setattr(module, attr, cast(binding[key]))

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
