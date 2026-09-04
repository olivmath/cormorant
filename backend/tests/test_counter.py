import importlib
import sys
import types

import pytest


class FakeDetections:
    def __init__(self):
        self.tracker_id = [31]
        self.confidence = ConfidenceValue()
        self.class_id = FilterValue()

    def __getitem__(self, _mask):
        return self

    def __len__(self):
        return 1


class FilterValue:
    def __eq__(self, _other):
        return True

    def __ge__(self, _other):
        return True


class ConfidenceValue(FilterValue):
    def __getitem__(self, _index):
        return 0.87


class FakeLineZone:
    next_counts = [(0, 0)]

    def __init__(self, *_args, **_kwargs):
        self.in_count = 0
        self.out_count = 0

    def trigger(self, _detections):
        self.in_count, self.out_count = self.next_counts.pop(0)


def install_vision_fakes(monkeypatch, counts):
    FakeLineZone.next_counts = list(counts)

    class FakeYOLO:
        def __init__(self, path):
            self.path = path

        def __call__(self, _frame, **_kwargs):
            return [object()]

    fake_sv = types.SimpleNamespace(
        ByteTrack=lambda: types.SimpleNamespace(update_with_detections=lambda detections: detections),
        LineZone=FakeLineZone,
        Point=lambda x, y: (x, y),
        Detections=types.SimpleNamespace(from_ultralytics=lambda _result: FakeDetections()),
    )
    monkeypatch.setitem(sys.modules, "ultralytics", types.SimpleNamespace(YOLO=FakeYOLO))
    monkeypatch.setitem(sys.modules, "supervision", fake_sv)
    sys.modules.pop("src.counter", None)
    return importlib.import_module("src.counter")


@pytest.mark.parametrize(
    ("counts", "expected_direction"),
    [([(0, 0), (1, 0)], "IN"), ([(0, 0), (0, 1)], "OUT")],
)
def test_new_line_zone_crossing_becomes_a_directional_event(monkeypatch, counts, expected_direction):
    counter_module = install_vision_fakes(monkeypatch, counts)
    counter = counter_module.FootfallCounter((0, 10), (100, 10))

    assert counter.process_frame(frame=object()) == []
    events = counter.process_frame(frame=object())

    assert events == [
        {"direction": expected_direction, "tracker_id": 31, "confidence": 0.87}
    ]
