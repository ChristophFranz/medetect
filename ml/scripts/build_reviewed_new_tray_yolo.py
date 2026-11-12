"""Convert reviewed new-tray Hook boxes into a one-class YOLO dataset."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COCO = REPO_ROOT / "ml/annotation/local/new_tray_detection_reviewed/annotations/instances_default.json"
RAW = REPO_ROOT / "ml/data/local/hook_sinskey/new_tray_v2/raw"
OUTPUT = REPO_ROOT / "ml/data/local/tray_detection/new_tray_reviewed_v2"
RECORD = REPO_ROOT / "ml/data/tray_detection_new_tray_reviewed_v2.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"refusing to overwrite reviewed tray dataset: {OUTPUT}")
    payload = json.loads(COCO.read_text())
    annotations: dict[int, list[dict]] = defaultdict(list)
    for annotation in payload["annotations"]:
        annotations[int(annotation["image_id"])].append(annotation)
    counts: Counter[str] = Counter()
    records = []
    for split in ("train", "valid", "test"):
        (OUTPUT / split / "images").mkdir(parents=True)
        (OUTPUT / split / "labels").mkdir(parents=True)
    for image in sorted(payload["images"], key=lambda item: int(item["id"])):
        split = str(image["split"])
        source = RAW / image["source_relative_path"]
        if not source.is_file():
            raise FileNotFoundError(source)
        target_name = Path(image["source_relative_path"]).name
        target = OUTPUT / split / "images" / target_name
        shutil.copy2(source, target)
        lines = []
        image_annotations = annotations[int(image["id"])]
        for annotation in image_annotations:
            if int(annotation["category_id"]) != 4:
                raise ValueError("reviewed new-tray data contains a non-Hook class")
            x, y, width, height = map(float, annotation["bbox"])
            lines.append(
                f"0 {(x + width / 2) / image['width']:.8f} "
                f"{(y + height / 2) / image['height']:.8f} "
                f"{width / image['width']:.8f} {height / image['height']:.8f}"
            )
        label = OUTPUT / split / "labels" / f"{Path(target_name).stem}.txt"
        label.write_text("\n".join(lines) + "\n")
        counts[f"{split}_images"] += 1
        counts[f"{split}_boxes"] += len(lines)
        records.append(
            {
                "split": split,
                "source_relative_path": image["source_relative_path"],
                "image": target.relative_to(REPO_ROOT).as_posix(),
                "image_sha256": sha256(target),
                "label": label.relative_to(REPO_ROOT).as_posix(),
                "label_sha256": sha256(label),
                "boxes": len(lines),
                "capture_group": image["capture_group"],
            }
        )
    (OUTPUT / "data.yaml").write_text(
        f"path: {OUTPUT.as_posix()}\ntrain: train/images\nval: valid/images\n"
        "test: test/images\n\nnames:\n  0: hook_sinskey\n"
    )
    digest = hashlib.sha256()
    for path in sorted(item for item in OUTPUT.rglob("*") if item.is_file()):
        relative = path.relative_to(OUTPUT).as_posix()
        digest.update(f"{relative}\0{path.stat().st_size}\0{sha256(path)}\n".encode())
    result = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "dataset_version": "hook_sinskey_tray_detection_new_tray_reviewed_v2",
        "status": "human_reviewed_frozen",
        "reviewer": "Christoph",
        "reviewed_on": "2026-10-20",
        "source_coco": COCO.relative_to(REPO_ROOT).as_posix(),
        "source_coco_sha256": sha256(COCO),
        "local_path": OUTPUT.relative_to(REPO_ROOT).as_posix(),
        "counts": dict(sorted(counts.items())),
        "tree_sha256": digest.hexdigest(),
        "test_split_frozen": True,
        "records": records,
    }
    RECORD.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"counts": result["counts"], "tree_sha256": result["tree_sha256"]}, indent=2))


if __name__ == "__main__":
    main()

