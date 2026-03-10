import pytest
from unittest.mock import AsyncMock, patch

from src.layers.citation_auditor import _extract_citations, audit_citations


def test_extract_urls():
    text = "Check https://example.com and http://test.org/page for details."
    citations = _extract_citations(text)
    urls = [c for c in citations if c["type"] == "url"]
    assert len(urls) == 2


def test_extract_references():
    text = "According to Dr. Smith, the results are significant."
    citations = _extract_citations(text)
    refs = [c for c in citations if c["type"] == "reference"]
    assert len(refs) == 1
    assert "Dr. Smith" in refs[0]["value"]


def test_extract_no_citations():
    text = "The sky is blue and grass is green."
    citations = _extract_citations(text)
    assert len(citations) == 0


@pytest.mark.asyncio
async def test_audit_no_citations():
    result = await audit_citations("Simple text with no citations.")
    assert result.total_citations == 0
    assert result.score is None


@pytest.mark.asyncio
@patch("src.layers.citation_auditor._check_url")
async def test_audit_with_urls(mock_check):
    mock_check.return_value = {"url": "https://example.com", "status": "resolved", "code": 200}
    result = await audit_citations("See https://example.com for more info.")
    assert result.total_citations >= 1
