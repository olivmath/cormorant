# Mobile Live Camera Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow one mobile browser to publish low-latency video, display it in the Cormorant dashboard, and count line crossings from its frames.

**Architecture:** LiveKit Cloud transports a single WebRTC camera track. The FastAPI backend mints role-limited tokens and runs a subscriber worker that converts decoded LiveKit video frames into the existing counter input. The Next.js frontend exposes a mobile publishing route and an admin video card.

**Tech Stack:** FastAPI, Python LiveKit RTC/API SDKs, Next.js 16, React 19, LiveKit React components, Tailwind CSS, existing SQLite and YOLO counter.

**Spec:** `docs/superpowers/specs/2026-09-04-mobile-live-camera-design.md`

## Global Constraints

- Use exactly one room: `cormorant-mvp`.
- Never expose `LIVEKIT_API_SECRET` to a browser.
- Mobile tokens publish camera video only; dashboard tokens subscribe only.
- Keep existing REST, WebSocket, SQLite, and KPI contracts backward compatible.
- Do not run automated tests, lint, or build; perform the manual verification from the approved spec.
- Physical USB, RTSP, and ONVIF adapters remain out of scope; preserve a source boundary for their later addition.

---

### Task 1: Add LiveKit backend configuration and token endpoint

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/src/config.py`
- Create: `backend/src/livekit_auth.py`
- Modify: `backend/src/schemas.py`
- Modify: `backend/src/routes.py`

**Interfaces:**
- Produces: `create_room_token(role: Literal["publisher", "viewer"]) -> LiveKitTokenResponse`
- Produces: `POST /api/livekit/token` accepting `{ "role": "publisher" | "viewer" }`.

- [ ] Add the Python LiveKit API and RTC dependencies.
- [ ] Add `livekit_url`, `livekit_api_key`, and `livekit_api_secret` to settings; use the existing `CORMORANT_` environment prefix only for Cormorant settings.
- [ ] Create role-specific short-lived JWTs for `mobile-camera` and `admin-dashboard`, scoped to `cormorant-mvp`.
- [ ] Add a Pydantic response containing `server_url`, `token`, and `room`.
- [ ] Expose the endpoint without leaking the API secret or token-signing inputs.

### Task 2: Build the mobile publisher route

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/lib/api.ts`
- Create: `frontend/src/components/mobile-camera.tsx`
- Create: `frontend/src/app/camera/page.tsx`
- Modify: `frontend/src/app/globals.css`

**Interfaces:**
- Consumes: `requestLiveKitToken("publisher")`.
- Produces: public `/camera` route that publishes a `camera` track.

- [ ] Add the LiveKit client and React component dependencies.
- [ ] Add `requestLiveKitToken(role)` to the frontend API client.
- [ ] Request a publisher token only after the operator chooses to start the camera.
- [ ] Use the browser camera with rear-camera preference and video-only publishing.
- [ ] Render preview, start/stop control, and the five defined connection states.
- [ ] Stop local tracks and disconnect the room when the user stops streaming or leaves the page.

### Task 3: Add live video to the admin dashboard

**Files:**
- Create: `frontend/src/components/live-camera.tsx`
- Modify: `frontend/src/app/page.tsx`

**Interfaces:**
- Consumes: `requestLiveKitToken("viewer")`.
- Produces: a dashboard card rendering the `mobile-camera` video track.

- [ ] Request a viewer token when the dashboard video card mounts.
- [ ] Connect as a subscriber and render only the mobile camera track.
- [ ] Keep the current KPI, chart, and camera-status components independent from video connection errors.
- [ ] Show waiting, live, disconnected, and error states in the new card.
- [ ] Disconnect cleanly when the card unmounts.

### Task 4: Process the LiveKit camera track in the backend

**Files:**
- Create: `backend/src/livekit_worker.py`
- Modify: `backend/src/main.py`
- Modify: `backend/src/capture.py`

**Interfaces:**
- Produces: `LiveKitWorker.start()` and `LiveKitWorker.stop()` lifecycle methods.
- Consumes: decoded LiveKit camera frames and emits existing crossing dictionaries.

- [ ] Create a subscriber token for hidden identity `counter-worker` with subscribe-only access.
- [ ] Join `cormorant-mvp` during FastAPI lifespan without preventing API startup when LiveKit is unconfigured.
- [ ] Subscribe only to the `mobile-camera` video track.
- [ ] Convert each decoded frame to the image representation accepted by `FootfallCounter.process_frame`.
- [ ] Reuse the existing event insertion and WebSocket broadcast flow for every crossing.
- [ ] Mark the mobile source online while frames arrive and offline when the track ends.
- [ ] Stop the worker and close its room connection during application shutdown.

### Task 5: Document configuration and manually verify the POC

**Files:**
- Modify: `frontend/README.md`
- Create: `backend/.env.example`

**Interfaces:**
- Documents the exact environment variable names and public URLs required by Codespaces.

- [ ] Document `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, and `NEXT_PUBLIC_API_URL` without values.
- [ ] Document opening `/camera` on the phone and the dashboard on another network.
- [ ] Use the six-step manual verification sequence in the design spec; do not execute the automated test suite.

### Task 6: Calibrate the mobile entry line from the admin video

**Files:**
- Modify: `backend/src/database.py`
- Modify: `backend/src/routes.py`
- Modify: `backend/src/schemas.py`
- Modify: `frontend/src/components/live-camera.tsx`

**Interfaces:**
- Produces: `GET` and `PUT /api/cameras/mobile/calibration`.
- Produces: normalized line points `{ start: [x, y], end: [x, y] }`, where each coordinate is between `0` and `1`.

- [ ] Persist one mobile-camera line in SQLite.
- [ ] Render the saved line as an SVG overlay on the live video.
- [ ] Let the admin click two points to set the line and save it.
- [ ] Reuse the normalized points when the LiveKit frame worker is enabled.
