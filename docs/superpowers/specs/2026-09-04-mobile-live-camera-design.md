# Mobile Live Camera Design

## Goal

Let one mobile phone publish a low-latency camera stream from any network. Show that stream in the Cormorant admin dashboard and process its frames in the backend so the existing entry, exit, trend, and event views receive real counts.

## Scope

### Included in the POC

- One browser-based mobile camera at a time, opened directly at a public `/camera` URL.
- LiveKit Cloud for WebRTC transport, including TURN fallback for mobile networks.
- A fixed LiveKit room named `cormorant-mvp`.
- The mobile participant publishes camera video only.
- The dashboard subscribes to and renders that video.
- A backend worker subscribes to the same video, sends frames through the existing `FootfallCounter`, and persists resulting events through the existing database flow.
- Clear camera states: waiting, live, permission denied, disconnected, and reconnecting.

### Deliberately out of scope

- User accounts, pairing, multi-tenant rooms, recordings, audio, and multiple simultaneous mobile cameras.
- A physical camera adapter. The source contract is introduced now so a later adapter can support USB, RTSP, or ONVIF cameras without changing counting, persistence, or dashboard APIs.

## Architecture

```text
Mobile browser (/camera)
    | getUserMedia + publish video
    v
LiveKit Cloud room: cormorant-mvp
    |                         |
    | WebRTC subscriber        | WebRTC subscriber
    v                         v
Admin dashboard            Backend video worker
    |                         |
    | renders video            | frames -> FootfallCounter
    v                         v
Video panel              SQLite -> existing REST/WebSocket APIs
                              |
                              v
                         Existing KPI and trend components
```

LiveKit transports video only. Cormorant remains the system of record for crossings, camera state, and dashboard statistics.

## Components

| Component | Responsibility |
| --- | --- |
| Mobile camera page | Requests camera permission, obtains a publisher token, publishes the rear camera when available, and reports its connection state. |
| Token endpoint | Creates a short-lived LiveKit JWT with a fixed opaque identity and only the permissions needed by the caller. It never returns the LiveKit API secret. |
| Dashboard video component | Obtains a viewer token, subscribes to the mobile camera track, and renders it in a responsive card. |
| LiveKit video worker | Joins the fixed room as a subscriber, reads the camera video frames, samples them according to `process_every_n_frames`, and forwards them to `FootfallCounter`. |
| Camera source contract | Normalizes a video source into frames plus health state. The initial adapter is `LiveKitMobileSource`; later adapters are `UsbCameraSource` and `RtspCameraSource`. |
| Existing persistence flow | Receives detected crossings unchanged, saves them in SQLite, and broadcasts live counter updates through the existing WebSocket manager. |

## Token and Permissions Model

The browser never receives `LIVEKIT_API_SECRET`. The backend uses it to issue a short-lived token for each request.

| Caller | Identity | Publish | Subscribe |
| --- | --- | ---: | ---: |
| Mobile page | `mobile-camera` | yes | no |
| Admin dashboard | `admin-dashboard` | no | yes |
| Video worker | `counter-worker` | no | yes |

All three participants join `cormorant-mvp`. This is intentionally open only at the application URL level for the POC; the short token lifetime limits reuse.

## Configuration

The backend requires these environment variables:

```text
LIVEKIT_URL=wss://<project>.livekit.cloud
LIVEKIT_API_KEY=<server-side-key>
LIVEKIT_API_SECRET=<server-side-secret>
```

The frontend receives only:

```text
NEXT_PUBLIC_API_URL=https://<backend-host>
```

The token endpoint returns the LiveKit URL and an ephemeral JWT. No public frontend environment variable contains a LiveKit API key or secret.

## API Contract

```text
POST /api/livekit/token
body: { "role": "publisher" | "viewer" }

200: {
  "server_url": "wss://...",
  "token": "<ephemeral JWT>",
  "room": "cormorant-mvp"
}
```

`publisher` is used only by `/camera`; `viewer` is used only by the admin dashboard. The counter worker creates its token internally and does not use this public endpoint.

## Camera Source Contract

```text
CameraSource
  - id: string
  - label: string
  - start(): async iterator of decoded video frames
  - stop(): void
  - status: waiting | live | disconnected | error
```

`LiveKitMobileSource` implements the contract in this POC. Future adapters produce the same decoded frames:

```text
UsbCameraSource  -> OpenCV device index
RtspCameraSource -> RTSP URL
Onvif discovery  -> resolves a camera into an RTSP URL
```

## Error Handling

| Condition | Mobile page | Dashboard | Backend |
| --- | --- | --- |
| Camera permission denied | Shows recovery instructions. | Shows “waiting for camera”. | Does not start inference. |
| Mobile disconnects | Attempts LiveKit reconnection. | Shows “camera offline”. | Stops frame consumption and marks source offline. |
| LiveKit unavailable | Shows connection error and retry action. | Keeps KPIs usable; video card shows error. | Logs the source failure without stopping the API. |
| Inference failure | Continues publishing video. | Continues rendering video. | Marks counting unavailable and retries the worker without corrupting stored counts. |

## Verification

Manual POC verification is sufficient for this project phase:

1. Open `/camera` on the phone and grant camera permission.
2. Open the admin dashboard on a separate network.
3. Confirm the video card becomes live within a few seconds.
4. Cross the calibrated line in front of the phone camera.
5. Confirm an entry or exit is persisted and the dashboard updates.
6. Turn off mobile connectivity and confirm both mobile and dashboard show a disconnected state.
