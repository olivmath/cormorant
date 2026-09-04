"""Swappable object-detection backends (YOLO variants, RT-DETR) sharing one ultralytics-style call interface."""

try:
    from ultralytics import RTDETR, YOLO
except ModuleNotFoundError:  # pragma: no cover - exercised through mocked integrations
    YOLO = None
    RTDETR = None

DETECTOR_WEIGHTS = {
    "yolov8s": "yolov8s.pt",
    "yolov8l": "yolov8l.pt",
    "rtdetr": "rtdetr-l.pt",
}
DEFAULT_DETECTOR = "yolov8s"


def load_model(name: str):
    if name not in DETECTOR_WEIGHTS:
        raise ValueError(f"Unknown detector model: {name!r}. Options: {sorted(DETECTOR_WEIGHTS)}")
    if YOLO is None or RTDETR is None:
        raise RuntimeError("Install ultralytics to use a detector model")
    weights = DETECTOR_WEIGHTS[name]
    return RTDETR(weights) if name == "rtdetr" else YOLO(weights)
