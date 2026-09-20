from pathlib import Path

from tools.benchmark.data_profile_runner import profile_benchmark_inputs


def test_v42_csv_flows_through_generic_ingestion(tmp_path: Path):
    source = tmp_path / "traffic.csv"
    source.write_text(
        "vehicle_id,timestamp,node\n"
        "A,2024-10-01 08:00:00,N1\n"
        "A,2024-10-01 08:05:00,N2\n"
        "B,2024-10-01 08:02:00,N1\n",
        encoding="utf-8",
    )

    result = profile_benchmark_inputs(
        tmp_path / "run",
        "CUMCM-2024E",
        [str(source)],
        problem="traffic flow benchmark",
    )

    assert result["status"] == "READY"
    assert result["attachment_count"] == 1

    profile = (tmp_path / "run" / "data" / "data_profile.json").read_text(encoding="utf-8")
    assert '"artifact_type": "DataProfile"' in profile
    assert '"rows": 3' in profile
    assert '"columns": 3' in profile


def test_v42_missing_attachment_is_warning_not_fabricated(tmp_path: Path):
    result = profile_benchmark_inputs(
        tmp_path / "run",
        "CUMCM-2024E",
        [str(tmp_path / "missing.xlsx")],
    )
    assert result["status"] == "READY_WITH_WARNINGS"
    assert result["attachment_count"] == 1
    assert result["warnings"]
