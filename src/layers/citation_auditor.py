import asyncio
import re

import httpx

from src.embeddings.encoder import encode_texts, cosine_similarity
from src.proxy.request_models import CitationResult
from src.utils.config import get_default_config
from src.utils.logging import get_logger

logger = get_logger(__name__)

URL_PATTERN = re.compile(r'https?://[^\s\)\]\},\"\']+')
REFERENCE_PATTERN = re.compile(
    r'(?:according to|as (?:stated|reported|noted) (?:by|in)|(?:study|research|paper) by)\s+([^,\.\;]+)',
    re.IGNORECASE,
)
FOOTNOTE_PATTERN = re.compile(r'\[(\d+)\]')


def _extract_citations(text: str) -> list[dict]:
    citations = []

    for match in URL_PATTERN.finditer(text):
        url = match.group().rstrip(".,;:)")
        citations.append({"type": "url", "value": url, "position": match.start()})

    for match in REFERENCE_PATTERN.finditer(text):
        citations.append({
            "type": "reference",
            "value": match.group(1).strip(),
            "position": match.start(),
        })

    return citations


async def _check_url(url: str, timeout: float = 5.0) -> dict:
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.head(url)
            if response.status_code < 400:
                return {"url": url, "status": "resolved", "code": response.status_code}
            else:
                return {"url": url, "status": "broken", "code": response.status_code}
    except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPError) as e:
        return {"url": url, "status": "unreachable", "error": str(type(e).__name__)}


async def _verify_url_content(url: str, claim_text: str, timeout: float = 5.0) -> dict:
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.get(url)
            if response.status_code >= 400:
                return {"supported": False, "reason": f"HTTP {response.status_code}"}

            content = response.text[:5000]
            embeddings = encode_texts([claim_text, content])
            sim = cosine_similarity(embeddings[0], embeddings[1])
            config = get_default_config()
            threshold = config.get("citation_auditor", {}).get("content_similarity_threshold", 0.6)
            return {
                "supported": sim >= threshold,
                "similarity": round(float(sim), 3),
                "reason": "content_match" if sim >= threshold else "content_mismatch",
            }
    except Exception:
        return {"supported": False, "reason": "fetch_failed"}


async def audit_citations(response_text: str) -> CitationResult:
    citations = _extract_citations(response_text)

    if not citations:
        return CitationResult(
            total_citations=0, valid=0, invalid=0, score=None, details=[]
        )

    config = get_default_config()
    url_timeout = config.get("citation_auditor", {}).get("url_timeout_seconds", 5)
    max_urls = config.get("citation_auditor", {}).get("max_urls_per_response", 10)

    url_citations = [c for c in citations if c["type"] == "url"][:max_urls]
    ref_citations = [c for c in citations if c["type"] == "reference"]

    details = []
    valid = 0
    invalid = 0

    if url_citations:
        check_tasks = [_check_url(c["value"], url_timeout) for c in url_citations]
        url_results = await asyncio.gather(*check_tasks)

        for citation, result in zip(url_citations, url_results):
            detail = {**citation, **result}
            if result["status"] == "resolved":
                valid += 1
            else:
                invalid += 1
                detail["hallucinated"] = True
            details.append(detail)

    for ref in ref_citations:
        details.append({**ref, "status": "unverified", "note": "reference verification requires knowledge base"})

    total = len(url_citations)
    score = valid / total if total > 0 else None

    logger.info(
        "citation_auditor.complete",
        total=len(citations),
        urls_checked=len(url_citations),
        valid=valid,
        invalid=invalid,
    )

    return CitationResult(
        total_citations=len(citations),
        valid=valid,
        invalid=invalid,
        score=score,
        details=details,
    )
