"""Offline smoke tests for V0.7 input ingestion."""
from __future__ import annotations

import json
from pathlib import Path

from tools.ingestion.data_profile import build_data_profile
from tools.ingestion.ingest import ingest_problem, write_ingestion_artifacts


def test_csv_ingestion(tmp_path: Path):
    csv_path = tmp_path / "traffic.csv"
    csv_path.write_text("time,flow\n08:00,120\n08:05,130\n08:05,130\n", encoding="utf-8")
    result = ingest_problem(None, [str(csv_path)])
    assert len(result.attachments) == 1
    item = result.attachments[0]
    assert item["status"] == "READABLE"
    assert item["sha256"]
    assert item["data_profile"]["rows"] == 3
    assert item["data_profile"]["duplicate_rows"] == 1


def test_docx_extraction_without_semantic_guess(tmp_path: Path):
    # A plain text problem path is deliberately supported as an inline/file input;
    # semantic interpretation remains outside deterministic ingestion.
    p = tmp_path / "problem.txt"
    p.write_text("问题1：建立预测模型。\n问题2：优化方案。", encoding="utf-8")
    result = ingest_problem(str(p), [])
    assert "问题1" in result.problem["text"]
    assert result.problem["source"] == "file"


def test_profile_artifact_is_serializable(tmp_path: Path):
    p = tmp_path / "data.csv"
    p.write_text("x,y\n1,2\n3,4\n", encoding="utf-8")
    result = ingest_problem(None, [str(p)])
    profile = build_data_profile(result.attachments)
    assert profile["artifact_type"] == "DataProfile"
    out = write_ingestion_artifacts(result, tmp_path / "out")
    payload = json.loads(out["ingestion_manifest"].read_text(encoding="utf-8"))
    assert payload["ingestion_version"] == "0.7"


def test_missing_attachment_is_explicit(tmp_path: Path):
    result = ingest_problem(None, [str(tmp_path / "missing.xlsx")])
    assert result.attachments[0]["status"] == "MISSING"
    assert result.warnings
