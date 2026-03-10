from src.storage.models import get_evaluation_stats
from src.analytics.drift_detector import get_drift_events


async def generate_report(format: str = "json") -> dict:
    stats_24h = await get_evaluation_stats(hours=24)
    stats_7d = await get_evaluation_stats(hours=168)
    stats_30d = await get_evaluation_stats(hours=720)
    drift_events = await get_drift_events(limit=10)

    report = {
        "summary": {
            "24h": stats_24h,
            "7d": stats_7d,
            "30d": stats_30d,
        },
        "drift_events": drift_events,
        "hallucination_rate": {
            "24h": _calc_hallucination_rate(stats_24h),
            "7d": _calc_hallucination_rate(stats_7d),
            "30d": _calc_hallucination_rate(stats_30d),
        },
    }

    return report


def _calc_hallucination_rate(stats: dict) -> float:
    total = stats.get("total", 0)
    if total == 0:
        return 0.0
    blocked = stats.get("blocked", 0) or 0
    warned = stats.get("warned", 0) or 0
    return round((blocked + warned) / total, 3)
