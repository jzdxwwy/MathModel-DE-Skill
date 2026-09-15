"""Load the Master Skill and stage instructions without binding to a model vendor."""
from __future__ import annotations

from pathlib import Path
from typing import Dict


class SkillLoader:
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root).resolve()

    def load_master(self) -> str:
        path = self.repo_root / "SKILL.md"
        if not path.exists():
            raise FileNotFoundError(f"Master Skill not found: {path}")
        return path.read_text(encoding="utf-8")

    def load_stage(self, stage: str) -> str:
        path = self.repo_root / "skills" / stage / "SKILL.md"
        if not path.exists():
            raise FileNotFoundError(f"Stage Skill not found: {path}")
        return path.read_text(encoding="utf-8")

    def load_bundle(self, stage: str) -> Dict[str, str]:
        return {"master": self.load_master(), "stage": self.load_stage(stage)}
