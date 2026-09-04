import importlib
import sys
import types


class FakeCapture:
    def __init__(self, frames):
        self.frames = iter(frames)
        self.released = False

    def isOpened(self):
        return True

    def read(self):
        return next(self.frames, (False, None))

    def release(self):
        self.released = True


def test_worker_skips_frames_persists_crossings_broadcasts_and_marks_disconnect(monkeypatch):
    fake_capture = FakeCapture([(True, "first"), (True, "second"), (False, None)])
    fake_cv2 = types.SimpleNamespace(
        CAP_AVFOUNDATION=99,
        VideoCapture=lambda _index, _api: fake_capture,
    )
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    sys.modules.pop("src.capture", None)
    capture = importlib.import_module("src.capture")

    statuses, persisted, broadcasts = [], [], []
    monkeypatch.setattr(capture, "FootfallCounter", lambda *_args: types.SimpleNamespace(
        process_frame=lambda frame: [{"direction": "IN", "tracker_id": 12, "confidence": 0.93}]
        if frame == "second" else []
    ))
    monkeypatch.setattr(capture, "update_camera_status", lambda *args: statuses.append(args))
    from src.schemas import EventResponse, StatsResponse

    def save_event(*args, **kwargs):
        persisted.append((args, kwargs))
        return EventResponse(
            id=99, timestamp="2026-09-03T12:00:00+00:00", direction="IN", camera_id=2,
            confidence=0.93,
        )

    monkeypatch.setattr(capture, "insert_event", save_event)
    monkeypatch.setattr(capture, "get_stats", lambda: StatsResponse(
        period="today", count_in=5, count_out=2, net=3,
        from_time="2026-09-03T00:00:00+00:00", to_time="2026-09-03T12:00:00+00:00",
    ))

    class Manager:
        async def broadcast(self, payload):
            broadcasts.append(payload)

    from src.config import CameraConfig, settings

    monkeypatch.setattr(settings, "process_every_n_frames", 2)
    worker = capture.CameraWorker(CameraConfig(camera_id=2, index=4, label="Door"), Manager())
    monkeypatch.setattr(capture.time, "sleep", lambda _seconds: worker.stop())
    worker.run()

    assert persisted == [((), {"camera_id": 2, "direction": "IN", "tracker_id": 12, "confidence": 0.93})]
    assert len(broadcasts) == 1
    assert broadcasts[0]["direction"] == "IN"
    assert broadcasts[0]["camera_id"] == 2
    assert statuses[0][:3] == (2, "Door", True)
    assert statuses[-1][:3] == (2, "Door", False)
    assert fake_capture.released
