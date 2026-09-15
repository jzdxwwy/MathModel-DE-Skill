"""Build a deterministic DataProfile skeleton from ingestion facts."""
from __future__ import annotations

from typing import Any


def build_data_profile(attachments: list[dict[str, Any]]) -> dict[str, Any]:
    assets = []
    risks = []
    for idx, item in enumerate(attachments, 1):
        profile = item.get("data_profile") or {}
        cols = profile.get("columns_profile", [])
        schema = [
            {"name": str(c.get("name", f"column_{j+1}")), "dtype": str(c.get("dtype", "unknown"))}
            for j, c in enumerate(cols)
        ]
        rows = int(profile.get("rows", 0) or 0)
        columns = int(profile.get("columns", len(schema)) or len(schema))
        missing = str(profile.get("empty_cells", 0)) + " empty cells" if "empty_cells" in profile else "not profiled"
        if "duplicate_rows" in profile:
            duplicates = str(profile["duplicate_rows"]) + " duplicate rows"
        elif "duplicate_rows_sample" in profile:
            duplicates = f"{profile['duplicate_rows_sample']} duplicate rows detected in {profile.get('duplicate_scope', 'sample')}"
        else:
            duplicates = "not profiled"
        quality = {"missing": missing, "duplicates": duplicates, "anomalies": "not profiled by deterministic ingestion"}
        assets.append({
            "asset_id": f"asset_{idx:03d}",
            "path_or_ref": item.get("path"),
            "format": item.get("extension", ""),
            "size": {"rows": rows, "columns": columns, "bytes": int(item.get("bytes", 0) or 0)},
            "schema": schema,
            "quality": quality,
        })
        if item.get("status") != "READABLE":
            risks.append(f"{item.get('name', 'unknown')}: unreadable or missing")
        if item.get("extraction_warning"):
            risks.append(f"{item.get('name', 'unknown')}: {item['extraction_warning']}")
        if profile.get("duplicate_scope"):
            risks.append(f"{item.get('name', 'unknown')}: duplicate detection is bounded to {profile['duplicate_scope']}")
        if profile.get("profile_skipped"):
            risks.append(f"{item.get('name', 'unknown')}: {profile.get('reason', 'profile skipped')}")
        if not profile:
            risks.append(f"{item.get('name', 'unknown')}: no tabular profile available")
    return {
        "artifact_type": "DataProfile",
        "schema_version": "0.1",
        "status": "DRAFT",
        "assets": assets or [{
            "asset_id": "no_assets",
            "format": "none",
            "size": {"rows": 0, "columns": 0, "bytes": 0},
            "quality": {"missing": "no assets", "duplicates": "no assets", "anomalies": "no assets"},
        }],
        "data_risks": risks,
        "gate_decision": "PASS_WITH_WARNINGS" if risks else "PASS",
    }
