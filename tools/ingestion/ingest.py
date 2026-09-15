"""V0.7 ingestion pipeline: problem statement + heterogeneous attachments."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .inspectors import inspect_file


@dataclass
class IngestionResult:
    problem: dict[str, Any]
    attachments: list[dict[str, Any]]
    warnings: list[str]

    def envelope(self) -> dict[str, Any]:
        return {
            "ingestion_version": "0.7",
            "problem": self.problem,
            "attachments": self.attachments,
            "warnings": self.warnings,
        }


def _problem_from_input(problem: str | None) -> dict[str, Any]:
    if not problem:
        return {"source": "none", "text": "", "path": None}
    path = Path(problem).expanduser()
    if path.exists() and path.is_file():
        item = inspect_file(str(path))
        return {
            "source": "file",
            "path": item["path"],
            "name": item["name"],
            "sha256": item.get("sha256"),
            "format": item.get("extension", ""),
            "text": item.get("text", ""),
            "text_chars": item.get("text_chars", 0),
            "extraction_warning": item.get("extraction_warning"),
        }
    return {"source": "inline", "path": None, "text": problem, "text_chars": len(problem)}


def _expand_attachments(values: Iterable[str]) -> list[str]:
    paths: list[str] = []
    for value in values:
        p = Path(value).expanduser()
        if p.is_dir():
            paths.extend(str(x) for x in sorted(p.rglob("*")) if x.is_file())
        else:
            paths.append(str(p))
    return paths


def ingest_problem(problem: str | None, attachments: Iterable[str] = ()) -> IngestionResult:
    """Inspect all supplied inputs without performing semantic modeling.

    The result deliberately preserves both raw file references and extracted text.
    Semantic interpretation is left to Stage 00/02 and the LLM.
    """
    problem_info = _problem_from_input(problem)
    attachment_info = [inspect_file(p) for p in _expand_attachments(attachments)]
    warnings: list[str] = []
    if problem_info.get("extraction_warning"):
        warnings.append(f"problem: {problem_info['extraction_warning']}")
    for item in attachment_info:
        if item.get("status") == "MISSING":
            warnings.append(f"missing attachment: {item['path']}")
        if item.get("extraction_warning"):
            warnings.append(f"{item['name']}: {item['extraction_warning']}")
        if item.get("data_profile_error"):
            warnings.append(f"{item['name']}: {item['data_profile_error']}")
    return IngestionResult(problem_info, attachment_info, warnings)


def write_ingestion_artifacts(result: IngestionResult, output_dir: str | Path) -> dict[str, Path]:
    """Persist the deterministic ingestion envelope and extracted problem text."""
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / "manifest" / "ingestion_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(result.envelope(), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    text = root / "input" / "problem_text.txt"
    text.parent.mkdir(parents=True, exist_ok=True)
    text.write_text(result.problem.get("text", ""), encoding="utf-8")
    return {"ingestion_manifest": manifest, "problem_text": text}
