import asyncio
import json
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.storage.models import get_evaluation_stats
from src.analytics.drift_detector import get_drift_events

router = APIRouter()


@router.get("/stats")
async def dashboard_stats():
    stats = await get_evaluation_stats(hours=24)
    drift = await get_drift_events(limit=5)
    return {
        "realtime": stats,
        "recent_drift_events": drift,
        "timestamp": time.time(),
    }


@router.websocket("/live")
async def live_feed(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            stats = await get_evaluation_stats(hours=1)
            await websocket.send_json({
                "type": "stats_update",
                "data": stats,
                "timestamp": time.time(),
            })
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
