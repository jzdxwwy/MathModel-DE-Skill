"""Validate MathModel-DE-Skill artifacts against their JSON Schemas.

Usage:
    python tests/artifact/validate_artifacts.py path/to/artifact.json path/to/schema.json

The validator intentionally performs schema validation only. Cross-artifact
lineage and stage-gate rules belong to the gate layer.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: jsonschema") from exc


def validate(artifact_path: str, schema_path: str) -> int:
    artifact = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(artifact), key=lambda e: list(e.path))
    if errors:
        print(f"FAIL: {artifact_path}")
        for error in errors:
            location = ".".join(str(x) for x in error.path) or "<root>"
            print(f"  - {location}: {error.message}")
        return 1
    print(f"PASS: {artifact_path}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: validate_artifacts.py ARTIFACT.json SCHEMA.json")
    raise SystemExit(validate(sys.argv[1], sys.argv[2]))
