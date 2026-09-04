from datetime import datetime

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
