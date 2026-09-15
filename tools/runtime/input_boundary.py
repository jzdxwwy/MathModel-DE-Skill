"""V0.7 runtime input boundary.

Keeps the legacy HostRequest contract intact while upgrading real execution to
consume actual files and extracted content rather than path strings only.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..ingestion.data_profile import build_data_profile
from ..ingestion.ingest import ingest_problem, write_ingestion_artifacts


def ingest_runtime_input(problem: str | None, attachments: list[str], output_dir: str | Path) -> dict[str, Any]:
    result = ingest_problem(problem, attachments)
    artifacts = write_ingestion_artifacts(result, output_dir)
    envelope = result.envelope()
    envelope["data_profile"] = build_data_profile(result.attachments)
    envelope["artifact_paths"] = {k: str(v) for k, v in artifacts.items()}
    return envelope
