from ml.scripts.build_endpoint_selector_dataset import endpoint_crop_box


def test_endpoint_crops_are_symmetric_and_in_bounds() -> None:
    box = [100.0, 50.0, 900.0, 150.0]
    left = endpoint_crop_box(box, (1000, 200), "left")
    right = endpoint_crop_box(box, (1000, 200), "right")
    assert left == (70, 40, 596, 160)
    assert right == (404, 40, 930, 160)
    assert left[2] - left[0] == right[2] - right[0]


def test_endpoint_crop_rejects_unknown_side() -> None:
    try:
        endpoint_crop_box([0.0, 0.0, 100.0, 20.0], (100, 20), "top")
    except ValueError as error:
        assert "invalid endpoint side" in str(error)
    else:
        raise AssertionError("unknown endpoint side was accepted")
