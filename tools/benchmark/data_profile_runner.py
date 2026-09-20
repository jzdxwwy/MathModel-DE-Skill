"""V1.0-V4.2 bridge from benchmark inputs to generic ingestion/DataProfile."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.ingestion.data_profile import build_data_profile
from tools.ingestion.ingest import ingest_problem, write_ingestion_artifacts


def profile_benchmark_inputs(
    run_dir: str | Path,
    benchmark_id: str,
    attachments: list[str],
    problem: str | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    root.mkdir(parents=True, exist_ok=True)

    result = ingest_problem(problem, attachments)
    ingestion_paths = write_ingestion_artifacts(result, root)
    profile = build_data_profile(result.attachments)

    profile_path = root / "data" / "data_profile.json"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = {
        "artifact_type": "BenchmarkDataProfile",
        "schema_version": "1.0",
        "benchmark_id": benchmark_id,
        "status": "READY" if not result.warnings else "READY_WITH_WARNINGS",
        "ingestion_manifest_ref": str(ingestion_paths["ingestion_manifest"]),
        "data_profile_ref": str(profile_path),
        "attachment_count": len(result.attachments),
        "warnings": list(result.warnings),
    }
    (root / "benchmark-data-profile.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report
