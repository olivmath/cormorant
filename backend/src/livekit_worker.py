"""Consumes the mobile LiveKit track and feeds frames into the footfall counter."""

import asyncio

import numpy as np
from livekit import rtc

from src.counter import FootfallCounter
from src.database import get_mobile_calibration, get_stats, insert_event, update_camera_status
from src.livekit_auth import create_room_token

MOBILE_CAMERA_ID = 100


class LiveKitWorker:
    def __init__(self, manager, url: str) -> None:
        self.manager, self.url, self.room, self.task = manager, url, rtc.Room(), None

    async def start(self) -> None:
        self.room.on("track_subscribed", self._track_subscribed)
        token = create_room_token("worker")
        await self.room.connect(self.url, token.token)

    def _track_subscribed(self, track, _publication, participant) -> None:
        if track.kind == rtc.TrackKind.KIND_VIDEO and participant.identity == "mobile-camera":
            self.task = asyncio.create_task(self._consume(track))

    async def _consume(self, track) -> None:
        stream = rtc.VideoStream(track, format=rtc.VideoBufferType.RGBA)
        counter = None
        frame_number = 0
        try:
            async for event in stream:
                frame_number += 1
                if frame_number % 3:
                    continue
                frame = event.frame
                calibration = get_mobile_calibration()
                if calibration is None:
                    continue
                if counter is None:
                    counter = FootfallCounter(
                        (int(calibration.start[0] * frame.width), int(calibration.start[1] * frame.height)),
                        (int(calibration.end[0] * frame.width), int(calibration.end[1] * frame.height)),
                    )
                image = np.frombuffer(frame.data, dtype=np.uint8).reshape(frame.height, frame.width, 4)[:, :, :3]
                update_camera_status(MOBILE_CAMERA_ID, "Câmera móvel", True)
                for crossing in await asyncio.to_thread(counter.process_frame, image):
                    event = insert_event(crossing["direction"], MOBILE_CAMERA_ID, crossing["tracker_id"], crossing["confidence"])
                    stats = get_stats()
                    await self.manager.broadcast({"type": "crossing", "direction": crossing["direction"], "camera_id": MOBILE_CAMERA_ID, "timestamp": event.timestamp.isoformat(), "today_in": stats.count_in, "today_out": stats.count_out})
        finally:
            await stream.aclose()
            update_camera_status(MOBILE_CAMERA_ID, "Câmera móvel", False)

    async def stop(self) -> None:
        if self.task:
            self.task.cancel()
        await self.room.disconnect()
