from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from pycocotools import mask as mask_utils

from ml.scripts.predict_images import discover_images, safe_stem, write_raw_masks


def test_discover_images_finds_supported_files_recursively(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    Image.new("RGB", (4, 4)).save(tmp_path / "a.jpg")
    Image.new("RGB", (4, 4)).save(nested / "b.png")
    (nested / "ignored.txt").write_text("not an image")

    assert [path.name for path in discover_images([tmp_path])] == ["a.jpg", "b.png"]


def test_discover_images_rejects_empty_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no supported images"):
        discover_images([tmp_path])


def test_safe_stem_is_filename_safe() -> None:
    assert safe_stem(Path("patient 1 / tip (left).jpg")) == "tip-left"


def test_write_raw_masks_exports_instances_and_union(tmp_path: Path) -> None:
    mask = np.zeros((5, 6), dtype=np.uint8)
    mask[1:4, 2:5] = 1
    encoded = mask_utils.encode(np.asfortranarray(mask))
    prediction = {
        "model": "mask_rcnn",
        "masks": [
            {"size": encoded["size"], "counts": encoded["counts"].decode("ascii")}
        ],
    }

    outputs = write_raw_masks(prediction, tmp_path / "masks", (6, 5))

    assert outputs is not None
    assert Path(outputs["union"]).is_file()
    assert len(outputs["instances"]) == 1
    assert np.asarray(Image.open(outputs["union"])).max() == 255


def test_write_raw_masks_exports_empty_union_for_healthy_prediction(
    tmp_path: Path,
) -> None:
    outputs = write_raw_masks(
        {"model": "mask_rcnn", "masks": []}, tmp_path / "healthy", (6, 5)
    )

    assert outputs is not None
    union = np.asarray(Image.open(outputs["union"]))
    assert union.shape == (5, 6)
    assert union.max() == 0
