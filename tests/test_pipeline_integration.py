import pytest
from unittest.mock import AsyncMock, patch

from src.proxy.request_models import Action


@pytest.mark.asyncio
@patch("src.layers.pipeline.verify_faithfulness")
@patch("src.layers.pipeline.audit_citations")
@patch("src.layers.pipeline.save_evaluation", new_callable=AsyncMock)
async def test_pipeline_pass(mock_save, mock_citations, mock_faithfulness):
    from src.proxy.request_models import FaithfulnessResult, CitationResult

    mock_faithfulness.return_value = FaithfulnessResult(
        score=0.9, total_claims=5, supported_claims=4,
        claims=[], unsupported_claims=[],
    )
    mock_citations.return_value = CitationResult(
        total_citations=0, valid=0, invalid=0, score=None, details=[],
    )
    mock_save.return_value = "test-id"

    from src.layers.pipeline import run_pipeline
    decision = await run_pipeline(
        response_text="Accurate response",
        context="Supporting context",
        prompt="Test prompt",
    )
    assert decision.action == Action.PASS
    mock_save.assert_called_once()


@pytest.mark.asyncio
@patch("src.layers.pipeline.verify_faithfulness")
@patch("src.layers.pipeline.audit_citations")
@patch("src.layers.pipeline.save_evaluation", new_callable=AsyncMock)
async def test_pipeline_block(mock_save, mock_citations, mock_faithfulness):
    from src.proxy.request_models import FaithfulnessResult, CitationResult

    mock_faithfulness.return_value = FaithfulnessResult(
        score=0.1, total_claims=10, supported_claims=1,
        claims=[], unsupported_claims=[],
    )
    mock_citations.return_value = CitationResult(
        total_citations=2, valid=0, invalid=2, score=0.0, details=[],
    )
    mock_save.return_value = "test-id"

    from src.layers.pipeline import run_pipeline
    decision = await run_pipeline(
        response_text="Hallucinated response",
        context="Real context",
        prompt="Test prompt",
    )
    assert decision.action == Action.BLOCK
