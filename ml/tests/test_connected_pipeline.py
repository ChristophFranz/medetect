import numpy as np

from ml.scripts.evaluate_connected_pipeline import (
    box_iou,
    greedy_matches,
    project_crop_mask,
)


def test_greedy_matches_are_one_to_one_and_thresholded() -> None:
    predictions = [[0, 0, 10, 10], [20, 20, 30, 30], [50, 50, 55, 55]]
    truth = [[1, 1, 11, 11], [20, 20, 30, 30]]
    matches = greedy_matches(predictions, truth, 0.5)
    assert {(prediction, target) for prediction, target, _ in matches} == {(0, 0), (1, 1)}
    assert box_iou(predictions[2], truth[1]) == 0.0


def test_project_crop_mask_undoes_mirroring() -> None:
    crop = np.array([[True, False], [False, False]])
    projected = project_crop_mask(crop, [1, 1, 3, 3], (4, 4), mirrored=True)
    expected = np.zeros((4, 4), dtype=bool)
    expected[1, 2] = True
    assert np.array_equal(projected, expected)
