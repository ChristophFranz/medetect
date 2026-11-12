from ml.scripts.build_augmented_defect_dataset import stable_seed


def test_augmentation_seed_is_stable_and_image_specific() -> None:
    assert stable_seed(42, "sample-a") == stable_seed(42, "sample-a")
    assert stable_seed(42, "sample-a") != stable_seed(42, "sample-b")
    assert stable_seed(42, "sample-a") != stable_seed(43, "sample-a")
