from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class StatsResponse(BaseModel):
    period: str
    count_in: int
    count_out: int
    net: int
    from_time: datetime
    to_time: datetime


class HourlyBucket(BaseModel):
    hour: str
    count_in: int
    count_out: int


class DailyBucket(BaseModel):
    date: str
    count_in: int
    count_out: int


class TrendResponse(BaseModel):
    buckets: list[HourlyBucket] | list[DailyBucket]


class EventResponse(BaseModel):
    id: int
    timestamp: datetime
    direction: str
    camera_id: int
    confidence: float

class CameraResponse(BaseModel):
    camera_id: int
    label: str
    is_online: bool
    last_seen: datetime | None


class LiveUpdate(BaseModel):
    type: str = "crossing"
    direction: str
    camera_id: int
    timestamp: datetime
    today_in: int
    today_out: int


class LiveKitTokenRequest(BaseModel):
    role: Literal["publisher", "viewer"]


class LiveKitTokenResponse(BaseModel):
    server_url: str
    token: str
    room: str


class CameraCalibration(BaseModel):
    start: tuple[float, float]
    end: tuple[float, float]
