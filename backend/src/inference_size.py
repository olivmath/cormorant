"""Selectable inference resolution (imgsz) — lower values trade accuracy for speed."""

INFERENCE_SIZES = {"full": 640, "medium": 480, "fast": 320}
DEFAULT_INFERENCE_SIZE = "full"


def resolve_imgsz(name: str) -> int:
    return INFERENCE_SIZES.get(name, INFERENCE_SIZES[DEFAULT_INFERENCE_SIZE])
