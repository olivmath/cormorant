#!/usr/bin/env python3
"""Interactive tool to calibrate counting line position per camera."""
import sys

import cv2

clicks: list[tuple[int, int]] = []


def on_mouse(event: int, x: int, y: int, _flags: int, _param: object) -> None:
    if event == cv2.EVENT_LBUTTONDOWN and len(clicks) < 2:
        clicks.append((x, y))
        print(f"Point {len(clicks)}: ({x}, {y})")


def calibrate_camera(index: int, label: str) -> tuple[tuple[int, int], tuple[int, int]] | None:
    cap = cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        print(f"Cannot open camera {index} ({label})")
        return None

    window = f"Calibrate: {label} (click 2 points, Enter to confirm, Q to skip)"
    cv2.namedWindow(window)
    cv2.setMouseCallback(window, on_mouse)
    clicks.clear()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (1280, 720))

        for i, pt in enumerate(clicks):
            cv2.circle(frame, pt, 6, (0, 255, 0), -1)
            cv2.putText(frame, f"P{i+1}", (pt[0] + 10, pt[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if len(clicks) == 2:
            cv2.line(frame, clicks[0], clicks[1], (0, 0, 255), 2)
            cv2.putText(frame, "Press ENTER to confirm", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow(window, frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 13 and len(clicks) == 2:  # Enter
            cap.release()
            cv2.destroyWindow(window)
            return (clicks[0], clicks[1])
        elif key == ord("q"):
            break
        elif key == ord("r"):
            clicks.clear()

    cap.release()
    cv2.destroyWindow(window)
    return None


def main() -> None:
    cameras = [
        (0, "Mac Built-in"),
        (1, "iPhone (Continuity)"),
    ]

    results: dict[int, tuple[tuple[int, int], tuple[int, int]]] = {}
    for index, label in cameras:
        print(f"\n--- Calibrating {label} (index {index}) ---")
        print("Click 2 points to define the counting line. R=reset, Q=skip, Enter=confirm")
        line = calibrate_camera(index, label)
        if line:
            results[index] = line
            print(f"  Line: {line[0]} -> {line[1]}")
        else:
            print(f"  Skipped")

    cv2.destroyAllWindows()

    if results:
        print("\n=== Results (add to .env or config) ===")
        for idx, (start, end) in results.items():
            print(f"Camera {idx}: line_start=({start[0]},{start[1]}) line_end=({end[0]},{end[1]})")


if __name__ == "__main__":
    main()
