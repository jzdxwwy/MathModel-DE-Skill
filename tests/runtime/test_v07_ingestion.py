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
    item = result.attachments[0]
    assert item["status"] == "READABLE"
    assert item["sha256"]
    assert item["data_profile"]["rows"] == 3
    assert item["data_profile"]["duplicate_rows_sample"] == 1


def test_csv_large_profile_is_bounded(tmp_path: Path):
    csv_path = tmp_path / "large.csv"
    with csv_path.open("w", encoding="utf-8") as f:
        f.write("id,value\n")
        for i in range(10000):
            f.write(f"{i},1\n")
    result = ingest_problem(None, [str(csv_path)])
    profile = result.attachments[0]["data_profile"]
    assert profile["rows"] == 10000
    assert profile["duplicate_scope"] == "first_5000_rows_only"


def test_problem_text_extraction_without_semantic_guess(tmp_path: Path):
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


def _make_xlsx(path: Path, sheets: dict) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    workbook.remove(workbook.active)
    for title, rows in sheets.items():
        worksheet = workbook.create_sheet(title=title)
        for row in rows:
            worksheet.append(row)
    workbook.save(path)


def test_xlsx_attachment_yields_real_schema_and_counts(tmp_path: Path):
    """Regression: _xlsx_profile used to return a ``sheets`` shape that the
    DataProfile builder could not read, so every real .xlsx competition
    attachment silently became 0 rows / 0 columns / empty schema while the
    artifact still reported PASS."""
    path = tmp_path / "attach.xlsx"
    _make_xlsx(path, {"Sheet1": [["城市", "流量"], ["北京", 120], ["上海", 130]]})

    result = ingest_problem(None, [str(path)])
    profile = result.attachments[0]["data_profile"]
    assert profile["rows"] == 2
    assert profile["columns"] == 2
    assert [c["name"] for c in profile["columns_profile"]] == ["城市", "流量"]
    assert profile["columns_profile"][1]["dtype"] == "number"

    artifact = build_data_profile(result.attachments)
    asset = artifact["assets"][0]
    assert asset["size"]["rows"] == 2
    assert asset["size"]["columns"] == 2
    assert [c["name"] for c in asset["schema"]] == ["城市", "流量"]
    assert artifact["gate_decision"] == "PASS"


def test_multi_sheet_workbook_becomes_one_asset_per_sheet(tmp_path: Path):
    """Real CUMCM workbooks carry several unrelated sheets; dropping all but the
    first silently loses the data most sub-problems depend on."""
    path = tmp_path / "multi.xlsx"
    _make_xlsx(path, {
        "投放记录": [["日期", "消费"], ["2025-01-01", 1.0], ["2025-01-02", 2.0]],
        "注册数": [["日期", "注册"], ["2025-01-01", 7]],
    })

    artifact = build_data_profile(ingest_problem(None, [str(path)]).attachments)
    assert artifact["gate_decision"] == "PASS_WITH_WARNINGS"
    assert [a["asset_id"] for a in artifact["assets"]] == ["asset_001_1", "asset_001_2"]

    first, second = artifact["assets"]
    assert first["size"]["rows"] == 2
    assert first["size"]["columns"] == 2
    assert [c["name"] for c in first["schema"]] == ["日期", "消费"]
    assert second["size"]["rows"] == 1
    assert [c["name"] for c in second["schema"]] == ["日期", "注册"]
    assert first["path_or_ref"].endswith("#投放记录")
    assert second["path_or_ref"].endswith("#注册数")

    joined = " | ".join(artifact["data_risks"])
    assert "2 sheets" in joined
    assert "投放记录" in joined and "注册数" in joined


def test_xlsx_without_openpyxl_fails_closed(tmp_path: Path, monkeypatch):
    """If the header cannot be read the profile must carry a risk, never a clean pass."""
    path = tmp_path / "attach.xlsx"
    _make_xlsx(path, {"Sheet1": [["a", "b"], [1, 2]]})

    import builtins

    real_import = builtins.__import__

    def deny_openpyxl(name, *args, **kwargs):
        if name == "openpyxl":
            raise ImportError("denied for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", deny_openpyxl)
    try:
        result = ingest_problem(None, [str(path)])
    finally:
        monkeypatch.undo()

    profile = result.attachments[0]["data_profile"]
    assert profile["columns_profile"] == []
    assert profile["profile_limited"]

    artifact = build_data_profile(result.attachments)
    assert artifact["gate_decision"] == "FAIL"
    assert any("openpyxl is not installed" in r for r in artifact["data_risks"])
    assert any(
        "no tabular attachment yielded a readable column schema" in r
        for r in artifact["data_risks"]
    )


def test_unreadable_pdf_problem_is_a_warning_not_a_silent_pass(tmp_path: Path):
    path = tmp_path / "problem.pdf"
    path.write_bytes(b"%PDF-1.4 this is not a parseable document")
    result = ingest_problem(str(path), [])
    assert result.warnings
    assert result.problem["text_chars"] == 0
