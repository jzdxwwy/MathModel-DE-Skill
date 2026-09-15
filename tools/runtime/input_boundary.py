"""V0.7 runtime input boundary.

Keeps the legacy HostRequest contract intact while upgrading real execution to
consume actual files and extracted content rather than path strings only.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..ingestion.data_profile import build_data_profile
from ..ingestion.ingest import ingest_problem, write_ingestion_artifacts


def ingest_runtime_input(problem: str | None, attachments: list[str], output_dir: str | Path) -> dict[str, Any]:
    result = ingest_problem(problem, attachments)
    artifacts = write_ingestion_artifacts(result, output_dir)
    profile = build_data_profile(result.attachments)
    profile_path = Path(output_dir).resolve() / "data" / "data_profile.json"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    envelope = result.envelope()
    envelope["data_profile"] = profile
    envelope["artifact_paths"] = {
        **{k: str(v) for k, v in artifacts.items()},
        "data_profile": str(profile_path),
    }
    return envelope
