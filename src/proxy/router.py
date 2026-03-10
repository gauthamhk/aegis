import time

from fastapi import APIRouter
from fastapi.responses import Response

from src.analytics.prometheus_metrics import (
    active_verifications,
    faithfulness_score,
    get_metrics,
    requests_total,
    verification_latency,
)
from src.analytics.reporter import generate_report
from src.analytics.drift_detector import check_drift, get_drift_events
from src.layers.pipeline import run_pipeline
from src.proxy.llm_client import llm_client
from src.proxy.request_models import Decision, ProxyRequest, VerifyRequest
from src.storage.models import get_evaluation_stats
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/verify", response_model=Decision)
async def verify(request: VerifyRequest):
    start = time.time()
    active_verifications.inc()
    try:
        decision = await run_pipeline(
            response_text=request.response_text,
            context=request.context,
            prompt=request.prompt,
            domain=request.domain,
        )

        latency = time.time() - start
        verification_latency.observe(latency)
        requests_total.labels(action=decision.action.value, domain=request.domain or "general").inc()
        if decision.faithfulness:
            faithfulness_score.observe(decision.faithfulness.score)

        return decision
    finally:
        active_verifications.dec()


@router.post("/proxy", response_model=Decision)
async def proxy(request: ProxyRequest):
    start = time.time()
    active_verifications.inc()
    try:
        llm_response = await llm_client.generate(
            prompt=request.prompt,
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        decision = await run_pipeline(
            response_text=llm_response,
            context=request.context,
            prompt=request.prompt,
            domain=request.domain,
        )

        latency = time.time() - start
        verification_latency.observe(latency)
        requests_total.labels(action=decision.action.value, domain=request.domain or "general").inc()
        if decision.faithfulness:
            faithfulness_score.observe(decision.faithfulness.score)

        return decision
    finally:
        active_verifications.dec()


@router.get("/metrics")
async def metrics():
    return Response(content=get_metrics(), media_type="text/plain")


@router.get("/analytics/summary")
async def analytics_summary():
    return {
        "24h": await get_evaluation_stats(hours=24),
        "7d": await get_evaluation_stats(hours=168),
        "30d": await get_evaluation_stats(hours=720),
    }


@router.get("/analytics/drift")
async def analytics_drift():
    events = await get_drift_events()
    return {"drift_events": events}


@router.get("/analytics/report")
async def analytics_report():
    return await generate_report()
