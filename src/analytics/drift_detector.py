import json
import time

from src.statistics.anomaly import grubbs_test, rolling_zscore
from src.storage.database import get_db
from src.storage.models import get_recent_scores
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def check_drift() -> dict | None:
    scores = await get_recent_scores(limit=1000)
    if len(scores) < 100:
        return None

    recent_batch = scores[:100]
    historical = scores[100:]

    grubbs = grubbs_test(recent_batch)

    zscores = rolling_zscore(scores, window=30)
    recent_zscores = zscores[:100]
    max_z = max(abs(z) for z in recent_zscores) if recent_zscores else 0

    import numpy as np
    recent_mean = float(np.mean(recent_batch))
    historical_mean = float(np.mean(historical))
    drift_magnitude = abs(recent_mean - historical_mean)

    drift_detected = grubbs["is_outlier"] or max_z > 2.5 or drift_magnitude > 0.15

    if not drift_detected:
        return None

    severity = "low"
    if drift_magnitude > 0.25 or max_z > 3.0:
        severity = "high"
    elif drift_magnitude > 0.15 or max_z > 2.5:
        severity = "medium"

    event = {
        "timestamp": time.time(),
        "metric_name": "composite_score",
        "z_score": round(max_z, 3),
        "window_mean": round(recent_mean, 3),
        "baseline_mean": round(historical_mean, 3),
        "severity": severity,
        "details": json.dumps({
            "grubbs": grubbs,
            "drift_magnitude": round(drift_magnitude, 3),
            "max_rolling_z": round(max_z, 3),
        }),
    }

    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO drift_events (timestamp, metric_name, z_score, p_value,
               window_mean, baseline_mean, severity, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event["timestamp"],
                event["metric_name"],
                event["z_score"],
                None,
                event["window_mean"],
                event["baseline_mean"],
                event["severity"],
                event["details"],
            ),
        )
        await db.commit()
    finally:
        await db.close()

    logger.warning(
        "drift.detected",
        severity=severity,
        drift_magnitude=round(drift_magnitude, 3),
        max_z=round(max_z, 3),
    )

    return event


async def get_drift_events(limit: int = 50) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM drift_events ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()
