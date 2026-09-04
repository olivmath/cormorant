"""Person tracking and directional line-crossing detection."""

try:  # Keep database/API startup usable when vision extras are not installed.
    from ultralytics import YOLO
    import supervision as sv
except ModuleNotFoundError:  # pragma: no cover - exercised through mocked integrations
    YOLO = None
    sv = None

from src.config import settings


class FootfallCounter:
    def __init__(self, line_start: tuple[int, int], line_end: tuple[int, int]) -> None:
        if YOLO is None or sv is None:
            raise RuntimeError("Install ultralytics and supervision to use FootfallCounter")
        self.model = YOLO(settings.yolo_model)
        self.tracker = sv.ByteTrack()
        point = getattr(sv, "Point", lambda x, y: (x, y))
        self.line_zone = sv.LineZone(start=point(*line_start), end=point(*line_end))
        self._in_count = 0
        self._out_count = 0

    def process_frame(self, frame) -> list[dict]:
        results = self.model(frame, verbose=False)
        detections = sv.Detections.from_ultralytics(results[0])
        class_ids = detections.class_id
        people = [value == 0 for value in class_ids] if isinstance(class_ids, list) else class_ids == 0
        detections = detections[people]
        confidences = detections.confidence
        confident = ([value >= settings.confidence_threshold for value in confidences]
                     if isinstance(confidences, list) else confidences >= settings.confidence_threshold)
        detections = detections[confident]
        detections = self.tracker.update_with_detections(detections)
        triggered = self.line_zone.trigger(detections)
        entered, exited = self._triggered_detections(detections, triggered)
        return [self._event("IN", detection) for detection in entered] + [
            self._event("OUT", detection) for detection in exited
        ]

    def _triggered_detections(self, detections, triggered):
        if isinstance(triggered, tuple) and len(triggered) == 2:
            incoming, outgoing = triggered
            if hasattr(incoming, "__len__") and len(incoming) == len(detections):
                return detections[incoming], detections[outgoing]
        current_in, current_out = self.line_zone.in_count, self.line_zone.out_count
        new_in, new_out = max(0, current_in - self._in_count), max(0, current_out - self._out_count)
        self._in_count, self._out_count = current_in, current_out
        return detections[:new_in], detections[:new_out]

    @staticmethod
    def _event(direction: str, detection) -> dict:
        return {"direction": direction, "tracker_id": int(detection.tracker_id[0]),
                "confidence": float(detection.confidence[0])}
