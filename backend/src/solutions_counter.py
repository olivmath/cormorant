"""Line-crossing counter backed by ultralytics.solutions.ObjectCounter (maintained upstream)."""

import logging

import numpy as np

try:
    from ultralytics.solutions import ObjectCounter
except ModuleNotFoundError:  # pragma: no cover - exercised through mocked integrations
    ObjectCounter = None

from src.detector import DEFAULT_DETECTOR, DETECTOR_WEIGHTS

logger = logging.getLogger(__name__)

PERSON_CLASS_ID = 0
BAND_HALF_WIDTH_PX = 30  # widens the crossing line into a band, more forgiving with low-fps sampling


def _band_region(line_start: tuple[int, int], line_end: tuple[int, int]) -> list[tuple[int, int]]:
    """Turn a 2-point line into a 4-point rectangle straddling it, so a fast-moving person
    is more likely to land inside the region on at least one processed frame."""
    dx, dy = line_end[0] - line_start[0], line_end[1] - line_start[1]
    length = max((dx ** 2 + dy ** 2) ** 0.5, 1e-6)
    ox, oy = -dy / length * BAND_HALF_WIDTH_PX, dx / length * BAND_HALF_WIDTH_PX
    return [
        (int(line_start[0] + ox), int(line_start[1] + oy)),
        (int(line_end[0] + ox), int(line_end[1] + oy)),
        (int(line_end[0] - ox), int(line_end[1] - oy)),
        (int(line_start[0] - ox), int(line_start[1] - oy)),
    ]


class SolutionsCounter:
    """Adapts ObjectCounter's cumulative in/out totals to the same event-list interface as FootfallCounter."""

    def __init__(self, line_start: tuple[int, int], line_end: tuple[int, int],
                 detector_name: str = DEFAULT_DETECTOR) -> None:
        if ObjectCounter is None:
            raise RuntimeError("Install ultralytics to use SolutionsCounter")
        self._weights = DETECTOR_WEIGHTS.get(detector_name, DETECTOR_WEIGHTS[DEFAULT_DETECTOR])
        self.detector_name = detector_name
        self.line_start = line_start
        self.line_end = line_end
        self._counter = self._build_counter(line_start, line_end)
        self._prev_in = 0
        self._prev_out = 0
        self._next_id = 0
        self._frame_count = 0
        self.last_people_count = 0
        self.last_tracked_people_count = 0

    def _build_counter(self, line_start: tuple[int, int], line_end: tuple[int, int]) -> "ObjectCounter":
        return ObjectCounter(model=self._weights, region=_band_region(line_start, line_end),
                             classes=[PERSON_CLASS_ID], show=False, verbose=False)

    def update_line(self, line_start: tuple[int, int], line_end: tuple[int, int]) -> None:
        # Rebuilds the whole ObjectCounter, not just the region: its tracker keeps a
        # frame-size-dependent motion-compensation buffer that breaks silently
        # ("GMC failed, falling back to identity") if the source resolution changes mid-stream.
        logger.info("cormorant.solutions_counter.line_updated line_start=%s line_end=%s", line_start, line_end)
        self.line_start = line_start
        self.line_end = line_end
        self._counter = self._build_counter(line_start, line_end)
        self._prev_in = 0
        self._prev_out = 0

    def process_frame(self, frame) -> list[dict]:
        self._frame_count += 1
        results = self._counter.process(np.ascontiguousarray(frame))
        boxes = getattr(self._counter, "boxes", None)
        self.last_people_count = len(boxes) if boxes is not None else 0
        self.last_tracked_people_count = self.last_people_count
        if self.last_people_count > 0 and self._frame_count % 15 == 0:
            x1, y1, x2, y2 = (float(v) for v in boxes[0][:4])
            cx = (x1 + x2) / 2
            band_min_x = min(pt[0] for pt in self._counter.region)
            band_max_x = max(pt[0] for pt in self._counter.region)
            inside = "dentro da faixa ✅" if band_min_x <= cx <= band_max_x else "fora da faixa"
            logger.info(
                "🚶 [%s/solutions] pessoa vista: posição x=%.0f | faixa=[%.0f,%.0f] | %s",
                self.detector_name, cx, band_min_x, band_max_x, inside,
            )
        new_in = max(0, results.in_count - self._prev_in)
        new_out = max(0, results.out_count - self._prev_out)
        self._prev_in, self._prev_out = results.in_count, results.out_count
        events = self._synthetic_events("IN", new_in) + self._synthetic_events("OUT", new_out)
        if events:
            logger.info("✅ [solutions] cruzamentos detectados: in=%s out=%s (total: in=%s out=%s)",
                        new_in, new_out, results.in_count, results.out_count)
        return events

    def _synthetic_events(self, direction: str, count: int) -> list[dict]:
        events = []
        for _ in range(count):
            self._next_id += 1
            events.append({"direction": direction, "tracker_id": self._next_id, "confidence": 1.0})
        return events
