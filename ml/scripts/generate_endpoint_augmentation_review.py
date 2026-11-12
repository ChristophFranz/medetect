"""Render deterministic examples of the endpoint selector's train-only augmentations."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "ml/data/endpoint_selector_v1.json"
OUTPUT = REPO_ROOT / "ml/runs/endpoint_selector/v1/augmentation_review.jpg"


def variants(image: Image.Image, seed: int) -> list[tuple[str, Image.Image]]:
    rng = np.random.default_rng(seed)
    gaussian = np.asarray(image).astype(np.float32)
    gaussian = np.clip(gaussian + rng.normal(0, 0.015 * 255, gaussian.shape), 0, 255).astype(np.uint8)
    salt_pepper = np.asarray(image).copy()
    count = max(1, round(image.width * image.height * 0.002))
    rows = rng.integers(0, image.height, count)
    columns = rng.integers(0, image.width, count)
    values = rng.choice([0, 255], count)
    salt_pepper[rows, columns] = values[:, None]
    jittered = ImageEnhance.Brightness(image).enhance(1.15)
    jittered = ImageEnhance.Contrast(jittered).enhance(1.15)
    return [
        ("original", image),
        ("rotate +10°", image.rotate(10, resample=Image.Resampling.BILINEAR, fillcolor=(124, 116, 104))),
        ("horizontal flip", ImageOps.mirror(image)),
        ("brightness + contrast", jittered),
        ("Gaussian blur", image.filter(ImageFilter.GaussianBlur(radius=1.0))),
        ("sharpen", ImageEnhance.Sharpness(image).enhance(1.5)),
        ("Gaussian noise", Image.fromarray(gaussian)),
        ("salt-and-pepper", Image.fromarray(salt_pepper)),
    ]


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    examples = []
    seen_labels = set()
    for record in manifest["records"]:
        if record["split"] == "train" and record["label"] not in seen_labels:
            examples.append(record)
            seen_labels.add(record["label"])
        if len(examples) == 2:
            break
    cell_width, cell_height = 360, 230
    sheet = Image.new("RGB", (cell_width * 4, cell_height * 4), "white")
    draw = ImageDraw.Draw(sheet)
    for example_index, record in enumerate(examples):
        image = Image.open(REPO_ROOT / record["image_path"]).convert("RGB")
        for variant_index, (name, altered) in enumerate(variants(image, 42 + example_index)):
            altered.thumbnail((cell_width - 8, cell_height - 42), Image.Resampling.LANCZOS)
            row = example_index * 2 + variant_index // 4
            column = variant_index % 4
            x = column * cell_width + (cell_width - altered.width) // 2
            y = row * cell_height + 38
            sheet.paste(altered, (x, y))
            draw.text(
                (column * cell_width + 6, row * cell_height + 5),
                f"{record['label']} — {name}",
                fill="black",
            )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUTPUT, quality=92)
    print(OUTPUT.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
