#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

IGNORED_FILENAMES = {".DS_Store", "Thumbs.db"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
IMAGE_SIZE_LIMIT_BYTES = 500 * 1024
REQUIRED_FIELDS = [
    "englishName",
    "founded",
    "area",
    "annualVisitors",
    "address",
    "website",
    "phone",
    "openingHours",
    "summary",
    "grade",
    "highlights",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit MuseumData completeness and image consistency.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "MuseumData",
        help="Path to MuseumData directory.",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    return parser.parse_args()


def natural_sort_key(value: str) -> list[Any]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def image_files(images_dir: Path) -> list[str]:
    if not images_dir.exists():
        return []
    files = [
        path.name
        for path in images_dir.iterdir()
        if path.is_file()
        and path.name not in IGNORED_FILENAMES
        and path.suffix.lower() in IMAGE_SUFFIXES
    ]
    return sorted(files, key=natural_sort_key)


def image_file_paths(images_dir: Path) -> list[Path]:
    if not images_dir.exists():
        return []
    files = [
        path
        for path in images_dir.iterdir()
        if path.is_file()
        and path.name not in IGNORED_FILENAMES
        and path.suffix.lower() in IMAGE_SUFFIXES
    ]
    return sorted(files, key=lambda path: natural_sort_key(path.name))


def is_missing(value: Any) -> bool:
    return value is None or value == "" or value == []


def audit_data(data_dir: Path) -> dict[str, Any]:
    missing_counts: Counter[str] = Counter()
    missing_museums: dict[str, list[str]] = {field: [] for field in REQUIRED_FIELDS}
    image_mismatches: list[dict[str, Any]] = []
    museum_count = 0
    image_total_json = 0
    image_total_disk = 0
    location_missing_museums: list[str] = []
    category_counts: Counter[str] = Counter()
    image_license_counts: Counter[str] = Counter()
    images_missing_license: list[str] = []
    images_missing_credit: list[str] = []
    oversized_images: list[dict[str, Any]] = []

    for info_path in sorted(data_dir.glob("*/info.json")):
        museum_count += 1
        museum = load_json(info_path)
        museum_id = museum["id"]
        category_counts[museum.get("category") or ""] += 1

        for field in REQUIRED_FIELDS:
            if is_missing(museum.get(field)):
                missing_counts[field] += 1
                missing_museums[field].append(museum_id)

        if museum.get("latitude") is None or museum.get("longitude") is None:
            missing_counts["location"] += 1
            location_missing_museums.append(museum_id)

        json_files = sorted(
            [image["filename"] for image in museum.get("images", []) if image.get("filename")],
            key=natural_sort_key,
        )
        images_dir = info_path.parent / "images"
        disk_files = image_files(images_dir)
        image_total_json += len(json_files)
        image_total_disk += len(disk_files)

        for image in museum.get("images", []):
            image_key = f"{museum_id}/{image.get('filename', '')}"
            license_name = (image.get("license") or "").strip()
            credit = (image.get("credit") or "").strip()
            if license_name:
                image_license_counts[license_name] += 1
            else:
                images_missing_license.append(image_key)
            if not credit:
                images_missing_credit.append(image_key)

        for image_path in image_file_paths(images_dir):
            size_bytes = image_path.stat().st_size
            if size_bytes > IMAGE_SIZE_LIMIT_BYTES:
                oversized_images.append(
                    {
                        "museum_id": museum_id,
                        "filename": image_path.name,
                        "size_bytes": size_bytes,
                    }
                )

        extra_on_disk = [name for name in disk_files if name not in json_files]
        missing_on_disk = [name for name in json_files if name not in disk_files]
        if extra_on_disk or missing_on_disk:
            image_mismatches.append(
                {
                    "museum_id": museum_id,
                    "json_image_count": len(json_files),
                    "disk_image_count": len(disk_files),
                    "extra_on_disk": extra_on_disk,
                    "missing_on_disk": missing_on_disk,
                }
            )

    return {
        "museum_count": museum_count,
        "image_total_json": image_total_json,
        "image_total_disk": image_total_disk,
        "image_mismatch_count": len(image_mismatches),
        "image_mismatches": image_mismatches,
        "missing_field_counts": dict(sorted(missing_counts.items())),
        "missing_field_museums": {
            field: museums
            for field, museums in missing_museums.items()
            if museums
        },
        "location_missing_museums": location_missing_museums,
        "category_counts": dict(sorted(category_counts.items())),
        "image_license_counts": dict(
            sorted(image_license_counts.items(), key=lambda item: (-item[1], item[0]))
        ),
        "images_missing_license_count": len(images_missing_license),
        "images_missing_license": images_missing_license,
        "images_missing_credit_count": len(images_missing_credit),
        "images_missing_credit": images_missing_credit,
        "image_size_limit_bytes": IMAGE_SIZE_LIMIT_BYTES,
        "oversized_image_count": len(oversized_images),
        "oversized_images_top": sorted(
            oversized_images,
            key=lambda item: item["size_bytes"],
            reverse=True,
        )[:20],
    }


def main() -> int:
    args = parse_args()
    report = audit_data(args.data_dir)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
