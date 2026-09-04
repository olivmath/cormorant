from datetime import UTC, datetime, timedelta

import pytest

from src.config import settings


@pytest.fixture
def database(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "footfall.sqlite"))
    from src import database

    database.init_db()
    return database


def test_events_are_persisted_and_recent_events_are_newest_first(database):
    older = datetime(2026, 9, 3, 10, 0, tzinfo=UTC)
    newer = datetime(2026, 9, 3, 11, 0, tzinfo=UTC)
    first = database.insert_event("IN", 4, 18, 0.91, older)
    second = database.insert_event("OUT", 4, 19, 0.82, newer)

    recent = database.get_recent_events(limit=2)

    assert first.id < second.id
    assert [(event.direction, event.camera_id, event.confidence) for event in recent] == [
        ("OUT", 4, 0.82),
        ("IN", 4, 0.91),
    ]
    assert recent[0].timestamp == newer


def test_stats_count_each_direction_in_requested_window(database):
    now = datetime.now(UTC)
    database.insert_event("IN", 1, 1, 0.9, now - timedelta(minutes=10))
    database.insert_event("IN", 1, 2, 0.9, now - timedelta(minutes=5))
    database.insert_event("OUT", 1, 3, 0.9, now - timedelta(minutes=2))
    database.insert_event("OUT", 1, 4, 0.9, now - timedelta(days=2))

    stats = database.get_stats("hour")

    assert (stats.period, stats.count_in, stats.count_out, stats.net) == ("hour", 2, 1, 1)
    assert stats.from_time <= now <= stats.to_time


def test_camera_status_upsert_replaces_current_status(database):
    seen_at = datetime(2026, 9, 3, 12, 30, tzinfo=UTC)
    database.update_camera_status(7, "Entrance", True, seen_at)
    database.update_camera_status(7, "Entrance camera", False)

    cameras = database.get_cameras()

    assert len(cameras) == 1
    assert cameras[0].model_dump() == {
        "camera_id": 7,
        "label": "Entrance camera",
        "is_online": False,
        "last_seen": seen_at,
    }


def test_trends_group_current_events_by_hour_and_day(database):
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    database.insert_event("IN", 1, 1, 0.8, now - timedelta(hours=1))
    database.insert_event("OUT", 1, 2, 0.8, now - timedelta(hours=1))
    database.insert_event("IN", 1, 3, 0.8, now)

    hourly = database.get_hourly_trend()
    daily = database.get_daily_trend()

    assert any((bucket.count_in, bucket.count_out) == (1, 1) for bucket in hourly.buckets)
    assert any((bucket.count_in, bucket.count_out) == (2, 1) for bucket in daily.buckets)
