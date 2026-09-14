"""End-to-end smoke test for the V0 production pipeline."""
from pathlib import Path
import tempfile

from tools.workflow.demo_pipeline import build_engine
from tools.workflow.engine import StageContext


def test_demo_pipeline_reaches_paper():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ctx = StageContext(root)
        manifest = build_engine().run(ctx)
        assert manifest.exists()
        assert (root / "paper/evidence_index.md").exists()
        assert (root / "paper/paper.md").exists()
        assert (root / "results/problem_1.json").exists()
        assert (root / "verification/verification_report.json").exists()
