"""Factory for the interchangeable counting engines (all share the same process_frame/update_line interface)."""

from src.centroid_counter import CentroidCounter
from src.counter import FootfallCounter
from src.dwell_debounce_counter import DwellDebounceCounter
from src.inference_size import DEFAULT_INFERENCE_SIZE
from src.iou_sort_counter import IouSortCounter
from src.polygon_zone_counter import PolygonZoneCounter
from src.solutions_counter import SolutionsCounter

COUNTING_ENGINES = {
    "custom": FootfallCounter,
    "ultralytics": SolutionsCounter,
    "centroid": CentroidCounter,
    "iou_sort": IouSortCounter,
    "polygon": PolygonZoneCounter,
    "dwell": DwellDebounceCounter,
}
DEFAULT_ENGINE = "custom"


def create_counter(line_start: tuple[int, int], line_end: tuple[int, int], detector_name: str,
                    engine: str = DEFAULT_ENGINE, inference_size: str = DEFAULT_INFERENCE_SIZE):
    engine_cls = COUNTING_ENGINES.get(engine, FootfallCounter)
    counter = engine_cls(line_start, line_end, detector_name=detector_name, inference_size=inference_size)
    counter.engine = engine
    return counter
