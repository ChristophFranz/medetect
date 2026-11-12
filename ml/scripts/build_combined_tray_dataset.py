"""Build a four-class old-plus-redesigned-tray YOLO dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OLD = Path("/Users/christophcuan/Desktop/medetect-api/Whole toolbox/Tools.v12i.yolov8")
DEFAULT_NEW = REPO_ROOT / "ml/annotation/local/new_tray_detection_candidates/yolo"
DEFAULT_OUTPUT = REPO_ROOT / "ml/data/local/tray_detection/combined_provisional_v1"
DEFAULT_SUMMARY = REPO_ROOT / "ml/data/combined_tray_provisional_v1.json"
CLASS_NAMES = ("chop phaco", "forceps macpherson", "forceps utrata", "hook sinskey")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_split(source: Path, output: Path, split: str, prefix: str) -> tuple[int, Counter[int]]:
    images = sorted(path for path in (source / split / "images").iterdir() if path.is_file())
    counts: Counter[int] = Counter()
    for image in images:
        label = source / split / "labels" / f"{image.stem}.txt"
        if not label.is_file():
            raise SystemExit(f"missing label for {image}")
        target_stem = f"{prefix}__{image.stem}"
        shutil.copy2(image, output / split / "images" / f"{target_stem}{image.suffix.lower()}")
        target_label = output / split / "labels" / f"{target_stem}.txt"
        shutil.copy2(label, target_label)
        for line in label.read_text().splitlines():
            if line.strip():
                class_id = int(line.split()[0])
                if class_id not in range(len(CLASS_NAMES)):
                    raise SystemExit(f"invalid class {class_id} in {label}")
                counts[class_id] += 1
    return len(images), counts


def write_domain_list(output: Path, domain: str, split: str) -> int:
    images = sorted((output / split / "images").glob(f"{domain}__*"))
    absolute = [path.resolve().as_posix() for path in images]
    (output / f"{domain}_{split}.txt").write_text("\n".join(absolute) + "\n")
    return len(images)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", type=Path, default=DEFAULT_OLD)
    parser.add_argument("--new", type=Path, default=DEFAULT_NEW)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    for split in ("train", "valid", "test"):
        (output / split / "images").mkdir(parents=True)
        (output / split / "labels").mkdir(parents=True)

    details: dict[str, object] = {}
    total_classes: Counter[int] = Counter()
    for split in ("train", "valid", "test"):
        details[split] = {}
        for domain, source in (("old", args.old.resolve()), ("new", args.new.resolve())):
            images, class_counts = copy_split(source, output, split, domain)
            total_classes.update(class_counts)
            details[split][domain] = {
                "images": images,
                "instances_by_class": {str(key): value for key, value in sorted(class_counts.items())},
            }
        details[split]["total_images"] = sum(details[split][d]["images"] for d in ("old", "new"))

    yaml_text = (
        f"path: {output.as_posix()}\n"
        "train: train/images\nval: valid/images\ntest: test/images\n\n"
        "names:\n" + "".join(f"  {i}: {name}\n" for i, name in enumerate(CLASS_NAMES))
    )
    (output / "data.yaml").write_text(yaml_text)
    for domain in ("old", "new"):
        for split in ("valid", "test"):
            write_domain_list(output, domain, split)
        (output / f"{domain}_test.yaml").write_text(
            f"path: {output.as_posix()}\n"
            f"train: {domain}_valid.txt\nval: {domain}_valid.txt\ntest: {domain}_test.txt\n\n"
            "names:\n" + "".join(f"  {i}: {name}\n" for i, name in enumerate(CLASS_NAMES))
        )

    records = []
    aggregate = hashlib.sha256()
    for path in sorted(p for p in output.rglob("*") if p.is_file()):
        relative = path.relative_to(output).as_posix()
        digest = sha256(path)
        size = path.stat().st_size
        aggregate.update(f"{relative}\0{size}\0{digest}\n".encode())
        records.append({"path": relative, "bytes": size, "sha256": digest})
    summary = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": "provisional_unreviewed_new_tray_boxes",
        "review_bypass_reason": "presentation urgency; review remains required before authoritative use",
        "old_source": args.old.resolve().as_posix(),
        "new_source": args.new.resolve().as_posix(),
        "local_path": output.relative_to(REPO_ROOT).as_posix(),
        "class_mapping": {str(i): name for i, name in enumerate(CLASS_NAMES)},
        "splits": details,
        "instances_by_class": {str(key): value for key, value in sorted(total_classes.items())},
        "tree_sha256": aggregate.hexdigest(),
        "files": records,
    }
    args.summary.resolve().write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"splits": details, "instances_by_class": summary["instances_by_class"]}, indent=2))


if __name__ == "__main__":
    main()
