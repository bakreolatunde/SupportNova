"""Placeholder integration tests — flesh out once genai_pipeline.pipeline
is wired to a live/mocked API key. Kept here so CI has something to run
from day one instead of an empty tests/ directory."""
import pytest


@pytest.mark.skip(reason="Requires ANTHROPIC_API_KEY or a mocked client — wire up in Day 3")
def test_analyze_complaint_returns_valid_schema():
    pass
