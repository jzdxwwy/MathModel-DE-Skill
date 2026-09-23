"""Compatibility wrapper for the historical V0.9-K import path.

The canonical builder lives in tools.writing.paper_evidence_builder. Keep this
module so older verification tests and downstream integrations continue to
work while the implementation has a single source of truth.
"""
from tools.writing.paper_evidence_builder import build_paper_evidence

__all__ = ["build_paper_evidence"]
