import pytest
from unittest.mock import AsyncMock, patch

from src.layers.faithfulness import verify_faithfulness, _chunk_context


def test_chunk_context():
    text = " ".join(["word"] * 1200)
    chunks = _chunk_context(text, chunk_size=500)
    assert len(chunks) == 3
    assert all(len(c.split()) <= 500 for c in chunks)


def test_chunk_context_empty():
    chunks = _chunk_context("")
    assert chunks == [""]


@pytest.mark.asyncio
async def test_faithfulness_no_context():
    result = await verify_faithfulness("The sky is blue.", context=None)
    assert result.score == 0.5
    assert result.total_claims > 0


@pytest.mark.asyncio
@patch("src.layers.faithfulness.llm_client")
async def test_faithfulness_with_context(mock_client):
    mock_client.generate = AsyncMock(
        side_effect=[
            '[{"claim": "Paris is the capital of France", "claim_type": "factual"}]',
            "SUPPORTED",
        ]
    )

    result = await verify_faithfulness(
        "Paris is the capital of France.",
        context="France is a country in Europe. Its capital city is Paris.",
    )
    assert result.total_claims == 1
    assert result.supported_claims <= result.total_claims
