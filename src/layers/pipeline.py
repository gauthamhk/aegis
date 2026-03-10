import asyncio
import time

from src.cache.redis_client import cache_get, cache_set
from src.layers.citation_auditor import audit_citations
from src.layers.decision_engine import make_decision
from src.layers.faithfulness import verify_faithfulness
from src.layers.semantic_entropy import detect_semantic_entropy
from src.proxy.request_models import Decision, EntropyResult, FaithfulnessResult, CitationResult
from src.storage.models import save_evaluation
from src.utils.config import get_default_config
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def _cached_faithfulness(response_text: str, context: str | None) -> FaithfulnessResult:
    cache_key_text = f"{response_text}:{context or ''}"
    cached = await cache_get("faithfulness", cache_key_text)
    if cached:
        return FaithfulnessResult(**cached)

    result = await verify_faithfulness(response_text, context)

    await cache_set("faithfulness", cache_key_text, result.model_dump(), ttl=1800)
    return result


async def _cached_citations(response_text: str) -> CitationResult:
    cached = await cache_get("citations", response_text)
    if cached:
        return CitationResult(**cached)

    result = await audit_citations(response_text)

    await cache_set("citations", response_text, result.model_dump(), ttl=1800)
    return result


async def run_pipeline(
    response_text: str,
    context: str | None = None,
    prompt: str | None = None,
    domain: str | None = None,
) -> Decision:
    start = time.time()
    config = get_default_config()
    se_config = config.get("semantic_entropy", {})
    trigger_range = se_config.get("trigger_faithfulness_range", [0.4, 0.7])

    faithfulness_task = _cached_faithfulness(response_text, context)
    citation_task = _cached_citations(response_text)

    faithfulness_result, citation_result = await asyncio.gather(
        faithfulness_task, citation_task
    )

    entropy_result: EntropyResult | None = None
    if prompt and trigger_range[0] <= faithfulness_result.score <= trigger_range[1]:
        logger.info(
            "pipeline.triggering_entropy",
            faithfulness_score=faithfulness_result.score,
        )
        entropy_result = await detect_semantic_entropy(prompt, response_text)

    decision = make_decision(
        faithfulness=faithfulness_result,
        entropy=entropy_result,
        citations=citation_result,
        response_text=response_text,
        domain=domain,
    )

    latency_ms = (time.time() - start) * 1000

    await save_evaluation(
        decision=decision,
        prompt=prompt,
        context=context,
        domain=domain or "general",
        latency_ms=latency_ms,
    )

    logger.info(
        "pipeline.complete",
        action=decision.action.value,
        composite=decision.composite_score,
        latency_ms=round(latency_ms, 1),
    )

    return decision
