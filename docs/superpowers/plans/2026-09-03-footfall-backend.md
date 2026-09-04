# Footfall Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add SQLite persistence, video counting, camera capture, and WebSocket broadcasting for retail footfall events.

**Architecture:** `CameraWorker` owns the camera lifecycle and sends each crossing returned by `FootfallCounter` to the database and `ConnectionManager`. Database helpers use synchronous SQLite connections with WAL and map results to the existing Pydantic schemas.

**Tech Stack:** Python 3.11, sqlite3, FastAPI WebSocket, OpenCV, Ultralytics YOLO, Supervision, pytest.

**Spec:** `docs/superpowers/specs/2026-09-03-footfall-backend-design.md`

## Global Constraints

- Create only `backend/src/database.py`, `backend/src/counter.py`, `backend/src/capture.py`, and `backend/src/ws_manager.py` as production files.
- Each requested production file remains below 150 lines.
- Enable WAL mode for each SQLite connection.
- `crossing_events.direction` accepts only `IN` and `OUT`.
- Use `src.config.settings` and existing `src.schemas` models where applicable.
- Do not commit, push, or change Git configuration.

---

### Task 1: SQLite persistence

**Files:**
- Create: `backend/src/database.py`
- Test: `backend/tests/test_database.py`

**Interfaces:**
- Produces: `init_db()`, `insert_event(direction, camera_id, tracker_id, confidence, timestamp=None)`, `get_stats(period="today")`, `get_hourly_trend()`, `get_daily_trend()`, `get_recent_events(limit=50)`, `update_camera_status(camera_id, label, is_online, last_seen=None)`, and `get_cameras()`.

- [ ] Write temporary-database tests proving event insertion, IN/OUT aggregation, and camera-status upsert.
- [ ] Run `cd backend && pytest tests/test_database.py -v` and confirm failures are caused by missing database helpers.
- [ ] Implement parameterized SQLite queries, UTC ISO timestamps, schema initialization, and Pydantic response mapping.
- [ ] Re-run `cd backend && pytest tests/test_database.py -v` and confirm it passes.

### Task 2: Live connection manager

**Files:**
- Create: `backend/src/ws_manager.py`
- Test: `backend/tests/test_ws_manager.py`

**Interfaces:**
- Produces: `ConnectionManager.connect(websocket)`, `disconnect(websocket)`, and async `broadcast(message)`.
- Consumes: FastAPI `WebSocket` instances with `accept()` and `send_json()`.

- [ ] Write tests proving accepted connections receive a JSON message and failed connections are removed.
- [ ] Run `cd backend && pytest tests/test_ws_manager.py -v` and confirm failures are caused by the missing manager.
- [ ] Implement a connection set and resilient async fan-out using `asyncio.gather`.
- [ ] Re-run `cd backend && pytest tests/test_ws_manager.py -v` and confirm it passes.

### Task 3: Footfall counter

**Files:**
- Create: `backend/src/counter.py`
- Test: `backend/tests/test_counter.py`

**Interfaces:**
- Produces: `FootfallCounter(line_start, line_end)` and `process_frame(frame) -> list[dict]`.
- Consumes: YOLO detections, `sv.ByteTrack`, and `sv.LineZone`.
- Produces crossings shaped as `{"direction": "IN"|"OUT", "tracker_id": int, "confidence": float}`.

- [ ] Write mocked-inference tests proving new line-zone IN and OUT triggers become crossings with tracker ID and confidence.
- [ ] Run `cd backend && pytest tests/test_counter.py -v` and confirm failures are caused by the missing counter.
- [ ] Implement YOLO person filtering, ByteTrack updates, line-zone triggering, and delta detection for new crossings.
- [ ] Re-run `cd backend && pytest tests/test_counter.py -v` and confirm it passes.

### Task 4: Camera worker

**Files:**
- Create: `backend/src/capture.py`
- Test: `backend/tests/test_capture.py`

**Interfaces:**
- Produces: `CameraWorker(camera_config, manager)` as a daemon `threading.Thread`.
- Consumes: configured camera index, `FootfallCounter.process_frame`, database helpers, and `ConnectionManager.broadcast`.
- Produces: persisted and broadcast `LiveUpdate` payloads; camera status transitions.

- [ ] Write mocked-camera tests proving skipped-frame processing, event persistence/broadcast, and offline status after a failed read.
- [ ] Run `cd backend && pytest tests/test_capture.py -v` and confirm failures are caused by the missing worker.
- [ ] Implement AVFoundation capture, five-second reconnection retry, frame skipping, status updates, and coroutine-safe broadcasts.
- [ ] Re-run `cd backend && pytest tests/test_capture.py -v` and confirm it passes.

### Task 5: Integrated verification

**Files:**
- Verify: `backend/tests/test_database.py`, `backend/tests/test_ws_manager.py`, `backend/tests/test_counter.py`, `backend/tests/test_capture.py`

- [ ] Run `cd backend && pytest -v`.
- [ ] Run `cd backend && python -m compileall src`.
- [ ] Confirm every requested production file is fewer than 150 lines.
