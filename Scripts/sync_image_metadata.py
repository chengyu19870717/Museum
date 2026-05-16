#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

IGNORED_FILENAMES = {".DS_Store", "Thumbs.db"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync info.json image metadata with files on disk.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "MuseumData",
        help="Path to MuseumData directory.",
    )
    parser.add_argument("--write", action="store_true", help="Persist changes to info.json files.")
    parser.add_argument(
        "--delete-junk",
        action="store_true",
        help="Delete .DS_Store and Thumbs.db files under MuseumData images directories.",
    )
    return parser.parse_args()


def natural_sort_key(value: str) -> list[Any]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def list_disk_images(images_dir: Path, delete_junk: bool) -> list[str]:
    if not images_dir.exists():
        return []

    result: list[str] = []
    for path in images_dir.iterdir():
        if not path.is_file():
            continue
        if path.name in IGNORED_FILENAMES:
            if delete_junk:
                path.unlink(missing_ok=True)
            continue
        if path.suffix.lower() in IMAGE_SUFFIXES:
            result.append(path.name)
    return sorted(result, key=natural_sort_key)


def normalized_entry(museum_name: str, filename: str, existing: dict[str, Any] | None) -> dict[str, Any]:
    entry = dict(existing or {})
    entry["filename"] = filename
    entry["caption"] = entry.get("caption") or museum_name
    entry["credit"] = entry.get("credit") or None
    entry["license"] = entry.get("license") or None
    return entry


def sync_data(data_dir: Path, write: bool, delete_junk: bool) -> dict[str, Any]:
    changed_museums: list[dict[str, Any]] = []
    added_entries = 0
    removed_entries = 0

    for info_path in sorted(data_dir.glob("*/info.json")):
        museum = json.loads(info_path.read_text(encoding="utf-8"))
        museum_name = museum.get("name") or museum.get("id") or info_path.parent.name
        existing_images = museum.get("images", [])
        existing_by_filename = {
            image["filename"]: image
            for image in existing_images
            if image.get("filename")
        }

        disk_images = list_disk_images(info_path.parent / "images", delete_junk=delete_junk)
        synced_images = [
            normalized_entry(museum_name, filename, existing_by_filename.get(filename))
            for filename in disk_images
        ]

        previous_filenames = sorted(existing_by_filename.keys(), key=natural_sort_key)
        added = [name for name in disk_images if name not in existing_by_filename]
        removed = [name for name in previous_filenames if name not in set(disk_images)]

        if synced_images != existing_images:
            museum["images"] = synced_images
            changed_museums.append(
                {
                    "museum_id": museum["id"],
                    "added_filenames": added,
                    "removed_filenames": removed,
                    "image_count": len(synced_images),
                }
            )
            added_entries += len(added)
            removed_entries += len(removed)
            if write:
                info_path.write_text(
                    json.dumps(museum, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

    return {
        "museum_count_changed": len(changed_museums),
        "added_entries": added_entries,
        "removed_entries": removed_entries,
        "changed_museums": changed_museums,
        "write": write,
        "delete_junk": delete_junk,
    }


def main() -> int:
    args = parse_args()
    report = sync_data(args.data_dir, write=args.write, delete_junk=args.delete_junk)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
