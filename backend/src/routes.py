import logging

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from src.database import (
    get_cameras,
    get_daily_trend,
    get_detector_model,
    get_hourly_trend,
    get_recent_events,
    get_stats,
    get_mobile_calibration,
    save_detector_model,
    save_mobile_calibration,
)
from src.detector import DETECTOR_WEIGHTS
from src.schemas import (
    CameraResponse,
    DetectorConfig,
    DetectorConfigUpdate,
    EventResponse,
    LiveKitTokenRequest,
    LiveKitTokenResponse,
    CameraCalibration,
    StatsResponse,
    TrendResponse,
)
from src.livekit_auth import configured, create_room_token
from src.ws_manager import ConnectionManager

router = APIRouter(prefix="/api")
manager = ConnectionManager()
logger = logging.getLogger(__name__)


@router.post("/livekit/token", response_model=LiveKitTokenResponse)
def livekit_token(request: LiveKitTokenRequest):
    if not configured():
        logger.warning("cormorant.api.livekit_token_rejected role=%s reason=not_configured", request.role)
        raise HTTPException(status_code=503, detail="LiveKit is not configured")
    logger.info("cormorant.api.livekit_token_issued role=%s", request.role)
    return create_room_token(request.role)


@router.get("/cameras/mobile/calibration", response_model=CameraCalibration | None)
def mobile_calibration():
    calibration = get_mobile_calibration()
    logger.info("cormorant.api.mobile_calibration_read configured=%s", calibration is not None)
    return calibration


@router.put("/cameras/mobile/calibration", response_model=CameraCalibration)
def set_mobile_calibration(calibration: CameraCalibration):
    logger.info("cormorant.api.mobile_calibration_saved start=%s end=%s", calibration.start, calibration.end)
    return save_mobile_calibration(calibration)


@router.get("/detector", response_model=DetectorConfig)
def detector():
    return DetectorConfig(model_name=get_detector_model(), available_models=sorted(DETECTOR_WEIGHTS))


@router.put("/detector", response_model=DetectorConfig)
def set_detector(update: DetectorConfigUpdate):
    if update.model_name not in DETECTOR_WEIGHTS:
        raise HTTPException(status_code=400, detail=f"Unknown detector model: {update.model_name!r}")
    logger.info("cormorant.api.detector_changed model_name=%s", update.model_name)
    return DetectorConfig(model_name=save_detector_model(update.model_name), available_models=sorted(DETECTOR_WEIGHTS))


@router.get("/stats", response_model=StatsResponse)
def stats(period: str = Query("today", pattern="^(today|hour|week|month)$")):
    result = get_stats(period)
    logger.info("cormorant.api.stats period=%s count_in=%s count_out=%s net=%s", period, result.count_in, result.count_out, result.net)
    return result


@router.get("/stats/hourly", response_model=TrendResponse)
def hourly():
    return get_hourly_trend()


@router.get("/stats/daily", response_model=TrendResponse)
def daily():
    return get_daily_trend()


@router.get("/events", response_model=list[EventResponse])
def events(limit: int = Query(50, ge=1, le=500)):
    result = get_recent_events(limit)
    logger.info("cormorant.api.events limit=%s returned=%s", limit, len(result))
    return result


@router.get("/cameras", response_model=list[CameraResponse])
def cameras():
    result = get_cameras()
    logger.info("cormorant.api.cameras returned=%s online=%s", len(result), sum(camera.is_online for camera in result))
    return result


@router.websocket("/ws/live")
async def live(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
