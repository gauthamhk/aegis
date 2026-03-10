import json
import time
import uuid

from src.proxy.request_models import Decision
from src.storage.database import get_db
from src.utils.config import settings
from src.utils.pii_redactor import redact_pii


def _redact(text: str | None) -> str | None:
    if text is None or not settings.pii_redaction_enabled:
        return text
    return redact_pii(text)


async def save_evaluation(
    decision: Decision,
    prompt: str | None = None,
    context: str | None = None,
    domain: str = "general",
    latency_ms: float | None = None,
) -> str:
    request_id = str(uuid.uuid4())
    db = await get_db()
    try:
        layer_details = {}
        if decision.faithfulness:
            layer_details["faithfulness"] = decision.faithfulness.model_dump()
        if decision.entropy:
            layer_details["entropy"] = decision.entropy.model_dump()
        if decision.citations:
            layer_details["citations"] = decision.citations.model_dump()

        await db.execute(
            """INSERT INTO evaluations
            (request_id, timestamp, prompt, response_text, context, domain,
             faithfulness_score, entropy_score, citation_score, composite_score,
             action, explanation, layer_details, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                request_id,
                time.time(),
                _redact(prompt),
                _redact(decision.response_text),
                _redact(context),
                domain,
                decision.faithfulness.score if decision.faithfulness else None,
                decision.entropy.entropy if decision.entropy else None,
                decision.citations.score if decision.citations else None,
                decision.composite_score,
                decision.action.value,
                decision.explanation,
                json.dumps(layer_details),
                latency_ms,
            ),
        )
        await db.commit()
    finally:
        await db.close()
    return request_id


async def get_recent_scores(limit: int = 1000) -> list[float]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT composite_score FROM evaluations ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows if row[0] is not None]
    finally:
        await db.close()


async def get_evaluation_stats(hours: int = 24) -> dict:
    db = await get_db()
    try:
        cutoff = time.time() - (hours * 3600)
        cursor = await db.execute(
            """SELECT
                COUNT(*) as total,
                AVG(composite_score) as avg_score,
                SUM(CASE WHEN action = 'PASS' THEN 1 ELSE 0 END) as passed,
                SUM(CASE WHEN action = 'WARN' THEN 1 ELSE 0 END) as warned,
                SUM(CASE WHEN action = 'BLOCK' THEN 1 ELSE 0 END) as blocked,
                SUM(CASE WHEN action = 'ESCALATE' THEN 1 ELSE 0 END) as escalated,
                AVG(latency_ms) as avg_latency
            FROM evaluations WHERE timestamp > ?""",
            (cutoff,),
        )
        row = await cursor.fetchone()
        return {
            "total": row[0],
            "avg_score": round(row[1], 3) if row[1] else 0,
            "passed": row[2],
            "warned": row[3],
            "blocked": row[4],
            "escalated": row[5],
            "avg_latency_ms": round(row[6], 1) if row[6] else 0,
        }
    finally:
        await db.close()
