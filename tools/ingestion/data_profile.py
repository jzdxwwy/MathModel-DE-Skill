"""Build a deterministic DataProfile skeleton from ingestion facts."""
from __future__ import annotations

from typing import Any

from .inspectors import TEXT_ENCODINGS

# Attachments that are expected to yield a tabular profile. A PDF problem
# statement legitimately has none, so only these suffixes raise a data risk;
# otherwise every real run would carry a meaningless warning.
TABULAR_SUFFIXES = {".csv", ".tsv", ".json", ".xlsx", ".xls"}


def _schema_from(columns_profile: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {"name": str(c.get("name", f"column_{j + 1}")), "dtype": str(c.get("dtype", "unknown"))}
        for j, c in enumerate(columns_profile)
    ]


def _quality(profile: dict[str, Any]) -> dict[str, str]:
    missing = (
        str(profile.get("empty_cells", 0)) + " empty cells"
        if "empty_cells" in profile
        else "not profiled"
    )
    if "duplicate_rows" in profile:
        duplicates = str(profile["duplicate_rows"]) + " duplicate rows"
    elif "duplicate_rows_sample" in profile:
        duplicates = (
            f"{profile['duplicate_rows_sample']} duplicate rows detected in "
            f"{profile.get('duplicate_scope', 'sample')}"
        )
    else:
        duplicates = "not profiled"
    return {
        "missing": missing,
        "duplicates": duplicates,
        "anomalies": "not profiled by deterministic ingestion",
    }


def _asset(
    item: dict[str, Any],
    asset_id: str,
    columns_profile: list[dict[str, Any]],
    rows: Any,
    columns: Any,
    path_or_ref: str | None,
) -> dict[str, Any]:
    schema = _schema_from(columns_profile)
    return {
        "asset_id": asset_id,
        "path_or_ref": path_or_ref,
        "format": item.get("extension", ""),
        "size": {
            "rows": int(rows or 0),
            "columns": int(columns or len(schema)),
            "bytes": int(item.get("bytes", 0) or 0),
        },
        "schema": schema,
        "quality": _quality(item.get("data_profile") or {}),
    }


def build_data_profile(attachments: list[dict[str, Any]]) -> dict[str, Any]:
    assets: list[dict[str, Any]] = []
    risks: list[str] = []
    tabular_expected = 0
    tabular_profiled = 0
    for idx, item in enumerate(attachments, 1):
        name = item.get("name", "unknown")
        profile = item.get("data_profile") or {}
        sheets = profile.get("sheets")
        item_assets: list[dict[str, Any]] = []

        if isinstance(sheets, list) and len(sheets) > 1:
            # Real CUMCM workbooks ship several sheets with unrelated schemas
            # (2026E: daily delivery records, daily registrations, keyword
            # statistics). Flattening them into a single asset silently drops
            # every sheet but the first, so each sheet becomes its own asset;
            # the DataProfile schema already allows an arbitrary asset array.
            for sheet in sheets:
                item_assets.append(_asset(
                    item,
                    f"asset_{idx:03d}_{sheet.get('index', 0) + 1}",
                    sheet.get("columns_profile", []),
                    sheet.get("rows", 0),
                    sheet.get("columns", 0),
                    f"{item.get('path')}#{sheet.get('name')}",
                ))
            sheet_names = ", ".join(str(s.get("name", "?")) for s in sheets)
            risks.append(
                f"{name}: workbook has {len(sheets)} sheets ({sheet_names}); each sheet is "
                f"profiled as its own asset, and cross-sheet joins are not inferred"
            )
        else:
            columns_profile = profile.get("columns_profile", [])
            item_assets.append(_asset(
                item,
                f"asset_{idx:03d}",
                columns_profile,
                profile.get("rows", 0),
                profile.get("columns", len(columns_profile)),
                item.get("path"),
            ))

        assets.extend(item_assets)
        if str(item.get("extension", "")).lower() in TABULAR_SUFFIXES:
            tabular_expected += 1
            if any(a["schema"] for a in item_assets):
                tabular_profiled += 1

        if item.get("status") != "READABLE":
            risks.append(f"{name}: unreadable or missing")
        if item.get("extraction_warning"):
            risks.append(f"{name}: {item['extraction_warning']}")
        if profile.get("duplicate_scope"):
            risks.append(f"{name}: duplicate detection is bounded to {profile['duplicate_scope']}")
        if profile.get("profile_skipped"):
            risks.append(f"{name}: {profile.get('reason', 'profile skipped')}")
        if profile.get("profile_limited"):
            risks.append(f"{name}: {profile['profile_limited']}")
        if profile.get("encoding_lossless") is False:
            # Fail closed on undecodable text: decoding with errors="replace" would
            # silently corrupt column names and values instead of reporting a problem.
            risks.append(
                f"{name}: could not be decoded losslessly as any of "
                f"{', '.join(TEXT_ENCODINGS)}; column names and text may be corrupted"
            )

        if not profile:
            if str(item.get("extension", "")).lower() in TABULAR_SUFFIXES:
                risks.append(f"{name}: tabular attachment produced no data profile")
        elif not any(a["schema"] for a in item_assets):
            # Fail closed. A readable attachment whose profile carries no column
            # schema was not actually understood; reporting it as a clean pass is
            # the silent-success failure this project exists to prevent.
            risks.append(
                f"{name}: readable but no column schema was read from the tabular "
                f"profile; column-level binding is impossible"
            )

    if tabular_expected and not tabular_profiled:
        # Fail closed. Every tabular attachment was expected to carry a readable
        # column schema and none did, so the profile describes nothing. The
        # DataProfile schema allows FAIL; returning PASS here is precisely the
        # silent success this project exists to prevent.
        risks.append(
            "no tabular attachment yielded a readable column schema; the data profile "
            "is empty and no column-level binding is possible"
        )
        gate_decision = "FAIL"
    else:
        gate_decision = "PASS_WITH_WARNINGS" if risks else "PASS"

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
        "gate_decision": gate_decision,
    }
