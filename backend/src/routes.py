from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.database import (
    get_cameras,
    get_daily_trend,
    get_hourly_trend,
    get_recent_events,
    get_stats,
)
from src.schemas import (
    CameraResponse,
    EventResponse,
    StatsResponse,
    TrendResponse,
)
from src.ws_manager import ConnectionManager

router = APIRouter(prefix="/api")
manager = ConnectionManager()


@router.get("/stats", response_model=StatsResponse)
def stats(period: str = Query("today", pattern="^(today|hour|week|month)$")):
    return get_stats(period)


@router.get("/stats/hourly", response_model=TrendResponse)
def hourly():
    return get_hourly_trend()


@router.get("/stats/daily", response_model=TrendResponse)
def daily():
    return get_daily_trend()


@router.get("/events", response_model=list[EventResponse])
def events(limit: int = Query(50, ge=1, le=500)):
    return get_recent_events(limit)


@router.get("/cameras", response_model=list[CameraResponse])
def cameras():
    return get_cameras()


@router.websocket("/ws/live")
async def live(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
