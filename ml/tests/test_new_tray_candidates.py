"""Focused tests for redesigned-tray detection candidate helpers."""

from PIL import Image

from ml.scripts.build_new_tray_detection_candidates import detector_boxes, xyxy_to_yolo


def test_xyxy_to_yolo_preserves_inherited_hook_class_id() -> None:
    assert xyxy_to_yolo([10, 20, 90, 80], 100, 100) == (
        "3 0.50000000 0.50000000 0.80000000 0.60000000"
    )


def test_detector_fallback_returns_one_valid_box() -> None:
    image = Image.new("RGB", (1000, 600), "black")
    boxes, method = detector_boxes(image, tool_count=1)

    assert method == "fallback"
    assert len(boxes) == 1
    x1, y1, x2, y2 = boxes[0]
    assert 0 <= x1 < x2 <= image.width
    assert 0 <= y1 < y2 <= image.height
