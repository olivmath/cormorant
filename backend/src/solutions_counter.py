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


class SolutionsCounter:
    """Adapts ObjectCounter's cumulative in/out totals to the same event-list interface as FootfallCounter."""

    def __init__(self, line_start: tuple[int, int], line_end: tuple[int, int],
                 detector_name: str = DEFAULT_DETECTOR) -> None:
        if ObjectCounter is None:
            raise RuntimeError("Install ultralytics to use SolutionsCounter")
        weights = DETECTOR_WEIGHTS.get(detector_name, DETECTOR_WEIGHTS[DEFAULT_DETECTOR])
        self.detector_name = detector_name
        self.line_start = line_start
        self.line_end = line_end
        self._counter = ObjectCounter(model=weights, region=[line_start, line_end],
                                       classes=[PERSON_CLASS_ID], show=False, verbose=False)
        self._prev_in = 0
        self._prev_out = 0
        self._next_id = 0
        self.last_people_count = 0
        self.last_tracked_people_count = 0

    def update_line(self, line_start: tuple[int, int], line_end: tuple[int, int]) -> None:
        logger.info("cormorant.solutions_counter.line_updated line_start=%s line_end=%s", line_start, line_end)
        self.line_start = line_start
        self.line_end = line_end
        self._counter.region = [line_start, line_end]
        self._counter.initialize_region()
        self._counter.in_count = 0
        self._counter.out_count = 0
        self._counter.counted_ids.clear()
        self._prev_in = 0
        self._prev_out = 0

    def process_frame(self, frame) -> list[dict]:
        results = self._counter.process(np.ascontiguousarray(frame))
        self.last_people_count = len(getattr(self._counter, "boxes", []) or [])
        self.last_tracked_people_count = self.last_people_count
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
