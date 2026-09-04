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
    # capture.py transitively imports the whole engine stack (src.counting -> every
    # *_counter module), which would otherwise trigger a real `import ultralytics`/
    # `import supervision` — both of which import the real cv2 internally and would
    # crash against the fake cv2 module above. Fake them out too, same as test_counter.py.
    monkeypatch.setitem(sys.modules, "ultralytics", types.SimpleNamespace(
        YOLO=lambda *_a, **_k: None, RTDETR=lambda *_a, **_k: None,
        solutions=types.SimpleNamespace(ObjectCounter=object),
    ))
    monkeypatch.setitem(sys.modules, "supervision", types.SimpleNamespace(
        ByteTrack=lambda **_kwargs: None, LineZone=lambda **_kwargs: None,
        Point=lambda x, y: (x, y), Detections=types.SimpleNamespace(from_ultralytics=lambda _r: None),
    ))
    # Only clear modules that actually bind against ultralytics/supervision at import
    # time — NOT src.config/src.database/etc., whose module-level singletons (e.g.
    # `settings`) other test files hold direct references to from collection time.
    for module_name in (
        "src.capture", "src.counting", "src.detector", "src.counter",
        "src.solutions_counter", "src.centroid_counter", "src.iou_sort_counter",
        "src.polygon_zone_counter", "src.dwell_debounce_counter",
    ):
        monkeypatch.delitem(sys.modules, module_name, raising=False)
    capture = importlib.import_module("src.capture")

    statuses, persisted, broadcasts = [], [], []
    fake_counter = types.SimpleNamespace(
        detector_name="yolov8s", engine="custom", inference_size="full",
        line_start=(0, 0), line_end=(1, 1),
        process_frame=lambda frame: [{"direction": "IN", "tracker_id": 12, "confidence": 0.93}]
        if frame == "second" else []
    )
    monkeypatch.setattr(capture, "create_counter", lambda *_args, **_kwargs: fake_counter)
    monkeypatch.setattr(capture, "get_detector_model", lambda: "yolov8s")
    monkeypatch.setattr(capture, "get_counting_engine", lambda: "custom")
    monkeypatch.setattr(capture, "get_inference_size", lambda: "full")
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

    assert persisted == [(("IN", 2, 12, 0.93), {})]
    assert len(broadcasts) == 1
    assert broadcasts[0]["direction"] == "IN"
    assert broadcasts[0]["camera_id"] == 2
    assert statuses[0][:3] == (2, "Door", True)
    assert statuses[-1][:3] == (2, "Door", False)
    assert fake_capture.released
