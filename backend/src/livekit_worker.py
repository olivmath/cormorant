"""Consumes the mobile LiveKit track and feeds frames into the footfall counter."""

import asyncio
import logging

import numpy as np
from livekit import rtc

from src.counter import FootfallCounter
from src.database import get_mobile_calibration, get_stats, insert_event, update_camera_status
from src.livekit_auth import create_room_token

MOBILE_CAMERA_ID = 100
logger = logging.getLogger(__name__)


class LiveKitWorker:
    def __init__(self, manager, url: str) -> None:
        self.manager, self.url, self.room, self.task = manager, url, rtc.Room(), None

    async def start(self) -> None:
        self.room.on("track_subscribed", self._track_subscribed)
        token = create_room_token("worker")
        logger.info("cormorant.livekit.worker_connecting room=%s", token.room)
        await self.room.connect(self.url, token.token)
        logger.info("cormorant.livekit.worker_connected room=%s", token.room)

    def _track_subscribed(self, track, _publication, participant) -> None:
        is_mobile_video = track.kind == rtc.TrackKind.KIND_VIDEO and participant.identity == "mobile-camera"
        logger.info(
            "cormorant.livekit.track_subscribed participant=%s kind=%s accepted=%s",
            participant.identity,
            track.kind,
            is_mobile_video,
        )
        if is_mobile_video:
            if self.task and not self.task.done():
                logger.info("cormorant.livekit.cancelling_previous_task")
                self.task.cancel()
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
                    if frame_number % 90 == 0:
                        logger.warning("cormorant.counting.waiting_for_calibration frames=%s", frame_number)
                    continue
                if counter is None:
                    line_start = (int(calibration.start[0] * frame.width), int(calibration.start[1] * frame.height))
                    line_end = (int(calibration.end[0] * frame.width), int(calibration.end[1] * frame.height))
                    counter = FootfallCounter(
                        line_start,
                        line_end,
                    )
                    logger.info(
                        "cormorant.counting.counter_ready frame_width=%s frame_height=%s line_start=%s line_end=%s",
                        frame.width,
                        frame.height,
                        line_start,
                        line_end,
                    )
                image = np.frombuffer(frame.data, dtype=np.uint8).reshape(frame.height, frame.width, 4)[:, :, :3]
                update_camera_status(MOBILE_CAMERA_ID, "Câmera móvel", True)
                crossings = await asyncio.to_thread(counter.process_frame, image)
                if frame_number % 90 == 0:
                    logger.info(
                        "cormorant.counting.heartbeat frames=%s people=%s tracked=%s crossings=%s",
                        frame_number,
                        counter.last_people_count,
                        counter.last_tracked_people_count,
                        len(crossings),
                    )
                for crossing in crossings:
                    event = insert_event(crossing["direction"], MOBILE_CAMERA_ID, crossing["tracker_id"], crossing["confidence"])
                    stats = get_stats()
                    logger.info(
                        "cormorant.counting.crossing direction=%s tracker_id=%s confidence=%.3f today_in=%s today_out=%s",
                        crossing["direction"],
                        crossing["tracker_id"],
                        crossing["confidence"],
                        stats.count_in,
                        stats.count_out,
                    )
                    await self.manager.broadcast({"type": "crossing", "direction": crossing["direction"], "camera_id": MOBILE_CAMERA_ID, "timestamp": event.timestamp.isoformat(), "today_in": stats.count_in, "today_out": stats.count_out})
        except Exception:
            logger.exception("cormorant.counting.stream_failed frames=%s", frame_number)
        finally:
            await stream.aclose()
            update_camera_status(MOBILE_CAMERA_ID, "Câmera móvel", False)
            logger.info("cormorant.counting.stream_stopped frames=%s", frame_number)

    async def stop(self) -> None:
        if self.task:
            self.task.cancel()
        await self.room.disconnect()
