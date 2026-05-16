from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .models import MuseumSeed
from .utils import dump_jsonl, sanitize_filename


def split_seeds_by_province(seeds: list[MuseumSeed]) -> dict[str, list[MuseumSeed]]:
    groups: dict[str, list[MuseumSeed]] = defaultdict(list)
    for seed in seeds:
        province = (seed.province or "未分省份").strip() or "未分省份"
        groups[province].append(seed)
    return dict(sorted(groups.items(), key=lambda item: item[0]))


def write_split_seed_files(output_dir: Path, groups: dict[str, list[MuseumSeed]]) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for province, seeds in groups.items():
        path = output_dir / f"{sanitize_filename(province)}.jsonl"
        dump_jsonl(path, [seed.to_dict() for seed in seeds])
        paths.append(path)
    return paths
