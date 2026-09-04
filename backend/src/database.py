"""Synchronous SQLite persistence for footfall data."""

import sqlite3
from datetime import UTC, datetime, timedelta

from src.config import settings
from src.schemas import (
    CameraResponse,
    CameraCalibration,
    DailyBucket,
    EventResponse,
    HourlyBucket,
    StatsResponse,
    TrendResponse,
)
def _now() -> datetime:
    return datetime.now(UTC)
def _iso(value: datetime) -> str:
    return value.replace(tzinfo=UTC).isoformat() if value.tzinfo is None else value.astimezone(UTC).isoformat()
def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(settings.db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    return connection
def init_db() -> None:
    with _connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS crossing_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                direction TEXT NOT NULL CHECK(direction IN ('IN', 'OUT')),
                camera_id INTEGER NOT NULL,
                tracker_id INTEGER NOT NULL,
                confidence REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS camera_status (
                camera_id INTEGER PRIMARY KEY,
                label TEXT NOT NULL,
                is_online INTEGER NOT NULL,
                last_seen TEXT
            );
            CREATE TABLE IF NOT EXISTS camera_calibration (
                camera_id INTEGER PRIMARY KEY, start_x REAL NOT NULL, start_y REAL NOT NULL,
                end_x REAL NOT NULL, end_y REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON crossing_events(timestamp);
            """
        )


def get_mobile_calibration() -> CameraCalibration | None:
    with _connection() as conn:
        row = conn.execute("SELECT * FROM camera_calibration WHERE camera_id = 100").fetchone()
    return CameraCalibration(start=(row["start_x"], row["start_y"]), end=(row["end_x"], row["end_y"])) if row else None


def save_mobile_calibration(calibration: CameraCalibration) -> CameraCalibration:
    with _connection() as conn:
        conn.execute("INSERT INTO camera_calibration VALUES (100, ?, ?, ?, ?) ON CONFLICT(camera_id) DO UPDATE SET start_x=excluded.start_x, start_y=excluded.start_y, end_x=excluded.end_x, end_y=excluded.end_y", (*calibration.start, *calibration.end))
    return calibration


def insert_event(
    direction: str, camera_id: int, tracker_id: int, confidence: float,
    timestamp: datetime | None = None,
) -> EventResponse:
    occurred_at = timestamp or _now()
    with _connection() as conn:
        cursor = conn.execute(
            "INSERT INTO crossing_events (timestamp, direction, camera_id, tracker_id, confidence) "
            "VALUES (?, ?, ?, ?, ?)",
            (_iso(occurred_at), direction, camera_id, tracker_id, confidence),
        )
        event_id = cursor.lastrowid
    return EventResponse(id=event_id, timestamp=occurred_at, direction=direction,
                         camera_id=camera_id, confidence=confidence)


def _window(period: str) -> tuple[datetime, datetime]:
    now = _now()
    if period == "hour":
        start = now.replace(minute=0, second=0, microsecond=0)
    elif period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError("period must be hour, today, week, or month")
    return start, now


def _counts(start: datetime, end: datetime) -> tuple[int, int]:
    with _connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(direction = 'IN'), 0) AS count_in, "
            "COALESCE(SUM(direction = 'OUT'), 0) AS count_out FROM crossing_events "
            "WHERE timestamp >= ? AND timestamp <= ?", (_iso(start), _iso(end)),
        ).fetchone()
    return int(row["count_in"]), int(row["count_out"])


def get_stats(period: str = "today") -> StatsResponse:
    start, end = _window(period)
    count_in, count_out = _counts(start, end)
    return StatsResponse(period=period, count_in=count_in, count_out=count_out,
                         net=count_in - count_out, from_time=start, to_time=end)


def get_hourly_trend() -> TrendResponse:
    start, end = _window("today")
    with _connection() as conn:
        rows = conn.execute(
            "SELECT substr(timestamp, 1, 13) AS bucket, SUM(direction = 'IN') AS count_in, "
            "SUM(direction = 'OUT') AS count_out FROM crossing_events "
            "WHERE timestamp >= ? AND timestamp <= ? GROUP BY bucket ORDER BY bucket",
            (_iso(start), _iso(end)),
        ).fetchall()
    return TrendResponse(buckets=[HourlyBucket(hour=row["bucket"] + ":00:00+00:00",
                         count_in=row["count_in"], count_out=row["count_out"]) for row in rows])


def get_daily_trend() -> TrendResponse:
    start, end = _window("week")
    with _connection() as conn:
        rows = conn.execute(
            "SELECT substr(timestamp, 1, 10) AS bucket, SUM(direction = 'IN') AS count_in, "
            "SUM(direction = 'OUT') AS count_out FROM crossing_events "
            "WHERE timestamp >= ? AND timestamp <= ? GROUP BY bucket ORDER BY bucket",
            (_iso(start), _iso(end)),
        ).fetchall()
    return TrendResponse(buckets=[DailyBucket(date=row["bucket"], count_in=row["count_in"],
                         count_out=row["count_out"]) for row in rows])


def get_recent_events(limit: int = 50) -> list[EventResponse]:
    with _connection() as conn:
        rows = conn.execute("SELECT * FROM crossing_events ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    return [EventResponse(id=row["id"], timestamp=datetime.fromisoformat(row["timestamp"]),
                          direction=row["direction"], camera_id=row["camera_id"],
                          confidence=row["confidence"]) for row in rows]


def update_camera_status(camera_id: int, label: str, is_online: bool,
                         last_seen: datetime | None = None) -> None:
    seen = last_seen or (_now() if is_online else None)
    with _connection() as conn:
        conn.execute("INSERT INTO camera_status (camera_id, label, is_online, last_seen) VALUES (?, ?, ?, ?) "
                     "ON CONFLICT(camera_id) DO UPDATE SET label=excluded.label, is_online=excluded.is_online, "
                     "last_seen=COALESCE(excluded.last_seen, camera_status.last_seen)",
                     (camera_id, label, is_online, _iso(seen) if seen else None))


def get_cameras() -> list[CameraResponse]:
    with _connection() as conn:
        rows = conn.execute("SELECT * FROM camera_status ORDER BY camera_id").fetchall()
    return [CameraResponse(camera_id=row["camera_id"], label=row["label"],
                           is_online=bool(row["is_online"]),
                           last_seen=datetime.fromisoformat(row["last_seen"]) if row["last_seen"] else None)
            for row in rows]
