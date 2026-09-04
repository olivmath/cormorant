# Footfall Backend Design

**Goal:** Persist detected line crossings, provide aggregate query helpers, and broadcast live crossings from camera workers.

## Architecture

```text
CameraWorker -> FootfallCounter -> SQLite database -> ConnectionManager
```

- `counter.py` owns model inference, tracking, and line-crossing detection.
- `capture.py` owns camera lifecycle and turns counter results into durable, live events.
- `database.py` owns synchronous SQLite schema and query helpers.
- `ws_manager.py` owns active WebSocket connections only.

## Data model

`crossing_events` records one detected crossing:

```text
id | timestamp (UTC ISO-8601) | direction (IN|OUT) | camera_id | tracker_id | confidence
```

`camera_status` stores one current row per camera:

```text
camera_id (PK) | label | is_online | last_seen (UTC ISO-8601, nullable)
```

Each database connection enables WAL mode. Aggregate helpers return the existing Pydantic response models:

| Helper | Window / grouping |
|---|---|
| `get_stats(period)` | `hour`, `today`, `week`, or `month`; IN, OUT, net |
| `get_hourly_trend()` | current-day hourly buckets |
| `get_daily_trend()` | current-week daily buckets |
| `get_recent_events(limit)` | newest events first |

## Runtime flow

1. `CameraWorker` opens its configured AVFoundation camera.
2. It processes every configured Nth frame through `FootfallCounter`.
3. Each crossing is inserted into SQLite, then broadcast as a serialized live event.
4. The worker upserts camera status while connected; on disconnect it marks the camera offline and retries after five seconds.

## Counter contract

`FootfallCounter.process_frame(frame)` returns dictionaries containing `direction`, `tracker_id`, and `confidence`. It uses YOLO person detections, `sv.ByteTrack`, and `sv.LineZone`; line direction is mapped to `IN` or `OUT` from `LineZone` counts for newly triggered crossings.

## Error handling and testing

- Camera open/read failures never terminate the worker; they trigger status update and retry.
- Failed WebSocket sends remove the stale connection without preventing delivery to the others.
- Tests use temporary SQLite databases and mock YOLO, Supervision, OpenCV, and WebSockets; no camera or model download is required.
- Each requested Python module remains below 150 lines.
