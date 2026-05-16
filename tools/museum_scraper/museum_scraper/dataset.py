from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .utils import clean_text, dump_json, dump_jsonl, registrable_domain, sha1_text


PAGE_TYPE_PRIORITY = ["overview", "visit", "venue", "collection", "exhibition", "other"]
OVERVIEW_PAGE_PRIORITY = ["overview", "venue", "collection", "exhibition", "visit", "other"]
FIELD_PAGE_PRIORITY = {
    "address": ["visit", "overview", "venue", "collection", "exhibition", "other"],
    "phone": ["visit", "overview", "venue", "collection", "exhibition", "other"],
    "email": ["visit", "overview", "venue", "collection", "exhibition", "other"],
    "opening_hours": ["visit", "overview", "venue", "collection", "exhibition", "other"],
}
REQUIRED_MUSEUM_FIELDS = ("overview", "address", "phone", "opening_hours")
OPTIONAL_MUSEUM_FIELDS = ("email",)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _museum_dirs(input_dir: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in input_dir.iterdir()
            if path.is_dir() and (path / "museum.json").exists()
        ],
        key=lambda path: path.name,
    )


class DatasetBuilder:
    def __init__(self, input_dir: Path, output_dir: Path) -> None:
        self.input_dir = input_dir
        self.output_dir = output_dir

    def build(self) -> dict[str, Any]:
        museum_rows, page_rows, image_rows, summary = self.collect()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        dump_jsonl(self.output_dir / "museums.jsonl", museum_rows)
        dump_jsonl(self.output_dir / "pages.jsonl", page_rows)
        dump_jsonl(self.output_dir / "images.jsonl", image_rows)
        dump_json(self.output_dir / "dataset_summary.json", summary)
        return summary

    def collect(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        museum_rows: list[dict[str, Any]] = []
        page_rows: list[dict[str, Any]] = []
        image_rows: list[dict[str, Any]] = []
        type_counter: Counter[str] = Counter()

        for museum_dir in _museum_dirs(self.input_dir):
            museum_record, museum_pages, museum_images = self._build_museum_record(museum_dir)
            museum_rows.append(museum_record)
            page_rows.extend(museum_pages)
            image_rows.extend(museum_images)
            for page in museum_pages:
                type_counter[page["page_type"]] += 1

        summary = {
            "museum_count": len(museum_rows),
            "page_count": len(page_rows),
            "image_count": len(image_rows),
            "page_type_distribution": dict(type_counter),
        }
        return museum_rows, page_rows, image_rows, summary

    def audit(self) -> dict[str, Any]:
        museum_rows, _, _, _ = self.collect()
        domain_counter: dict[str, dict[str, Any]] = {}
        museum_reports: list[dict[str, Any]] = []
        required_missing_counter: Counter[str] = Counter()
        optional_missing_counter: Counter[str] = Counter()
        complete_count = 0

        for row in museum_rows:
            missing_required = [field for field in REQUIRED_MUSEUM_FIELDS if not clean_text(str(row.get(field, "")))]
            missing_optional = [field for field in OPTIONAL_MUSEUM_FIELDS if not clean_text(str(row.get(field, "")))]
            if not missing_required:
                complete_count += 1
            for field in missing_required:
                required_missing_counter[field] += 1
            for field in missing_optional:
                optional_missing_counter[field] += 1

            domain = ""
            resolved_site = clean_text(row.get("resolved_site", ""))
            official_site = clean_text(row.get("official_site", ""))
            if resolved_site or official_site:
                domain = registrable_domain(resolved_site or official_site)
            domain = domain or "unknown"
            bucket = domain_counter.setdefault(
                domain,
                {
                    "domain": domain,
                    "museum_count": 0,
                    "missing_required_counts": Counter(),
                    "missing_optional_counts": Counter(),
                    "museum_names": [],
                },
            )
            bucket["museum_count"] += 1
            bucket["museum_names"].append(row["name"])
            for field in missing_required:
                bucket["missing_required_counts"][field] += 1
            for field in missing_optional:
                bucket["missing_optional_counts"][field] += 1

            museum_reports.append(
                {
                    "name": row["name"],
                    "province": row.get("province", ""),
                    "resolved_site": resolved_site,
                    "missing_required_fields": missing_required,
                    "missing_optional_fields": missing_optional,
                    "missing_required_count": len(missing_required),
                    "missing_optional_count": len(missing_optional),
                    "page_count": row.get("page_count", 0),
                    "image_count": row.get("image_count", 0),
                    "root_dir": row.get("root_dir", ""),
                }
            )

        domain_reports = []
        for bucket in domain_counter.values():
            domain_reports.append(
                {
                    "domain": bucket["domain"],
                    "museum_count": bucket["museum_count"],
                    "missing_required_counts": dict(bucket["missing_required_counts"]),
                    "missing_optional_counts": dict(bucket["missing_optional_counts"]),
                    "museum_names": sorted(bucket["museum_names"]),
                }
            )

        audit_report = {
            "museum_count": len(museum_rows),
            "required_fields": list(REQUIRED_MUSEUM_FIELDS),
            "optional_fields": list(OPTIONAL_MUSEUM_FIELDS),
            "complete_count": complete_count,
            "complete_rate": round(complete_count / len(museum_rows), 4) if museum_rows else 0.0,
            "missing_required_counts": dict(required_missing_counter),
            "missing_optional_counts": dict(optional_missing_counter),
            "coverage": {
                field: round((len(museum_rows) - required_missing_counter.get(field, 0)) / len(museum_rows), 4) if museum_rows else 0.0
                for field in (*REQUIRED_MUSEUM_FIELDS, *OPTIONAL_MUSEUM_FIELDS)
            },
            "domain_reports": sorted(
                domain_reports,
                key=lambda row: (-sum(row["missing_required_counts"].values()), row["domain"]),
            ),
            "museum_reports": sorted(
                museum_reports,
                key=lambda row: (-row["missing_required_count"], -row["missing_optional_count"], row["name"]),
            ),
        }
        return audit_report

    def _build_museum_record(self, museum_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
        museum_json = _read_json(museum_dir / "museum.json")
        crawl_report_path = museum_dir / "crawl_report.json"
        crawl_report = _read_json(crawl_report_path) if crawl_report_path.exists() else {}
        seed = museum_json.get("seed", {})
        pages = self._load_pages(museum_dir, seed)
        images = self._load_images(museum_dir, seed, pages)

        chosen = self._choose_metadata(pages)
        museum_id = sha1_text(f"{seed.get('province', '')}|{seed.get('name', museum_dir.name)}")
        museum_record = {
            "museum_id": museum_id,
            "name": seed.get("name", museum_dir.name),
            "province": seed.get("province", ""),
            "city": seed.get("city", ""),
            "official_site": seed.get("official_site", ""),
            "resolved_site": museum_json.get("resolved_site", ""),
            "source": seed.get("source", ""),
            "seed_metadata": seed.get("metadata", {}),
            "address": chosen.get("address", ""),
            "phone": chosen.get("phone", ""),
            "email": chosen.get("email", ""),
            "opening_hours": chosen.get("opening_hours", ""),
            "overview": self._choose_overview(pages),
            "page_count": len(pages),
            "image_count": len(images),
            "status": crawl_report.get("status", "completed"),
            "root_dir": museum_dir.name,
            "page_titles": {
                page_type: [page["title"] for page in pages if page["page_type"] == page_type]
                for page_type in PAGE_TYPE_PRIORITY
                if any(page["page_type"] == page_type for page in pages)
            },
        }
        return museum_record, pages, images

    def _load_pages(self, museum_dir: Path, seed: dict[str, Any]) -> list[dict[str, Any]]:
        pages: list[dict[str, Any]] = []
        museum_id = sha1_text(f"{seed.get('province', '')}|{seed.get('name', museum_dir.name)}")
        for json_path in sorted((museum_dir / "pages").rglob("*.json")):
            page = _read_json(json_path)
            page_id = sha1_text(page.get("url", str(json_path)))
            pages.append(
                {
                    "museum_id": museum_id,
                    "page_id": page_id,
                    "museum_name": seed.get("name", museum_dir.name),
                    "page_type": page.get("page_type", "other"),
                    "title": page.get("title", ""),
                    "url": page.get("url", ""),
                    "summary": page.get("summary", ""),
                    "text": page.get("text", ""),
                    "depth": page.get("depth", 0),
                    "metadata": page.get("metadata", {}),
                    "local_json_path": str(json_path.relative_to(self.input_dir)),
                    "local_md_path": str(json_path.with_suffix(".md").relative_to(self.input_dir)),
                }
            )
        return pages

    def _load_images(self, museum_dir: Path, seed: dict[str, Any], pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        museum_id = sha1_text(f"{seed.get('province', '')}|{seed.get('name', museum_dir.name)}")
        image_lookup: dict[str, dict[str, Any]] = {}
        for page in pages:
            page_payload = _read_json(self.input_dir / page["local_json_path"])
            for image in page_payload.get("images", []):
                digest_prefix = sha1_text(image.get("url", ""))[:10]
                image_lookup[digest_prefix] = {
                    "image_url": image.get("url", ""),
                    "alt": image.get("alt", ""),
                    "title": image.get("title", ""),
                    "source_page": image.get("source_page", page["url"]),
                    "page_type": image.get("page_type", page["page_type"]),
                }

        rows: list[dict[str, Any]] = []
        for image_path in sorted((museum_dir / "images").rglob("*")):
            if not image_path.is_file():
                continue
            prefix = image_path.name.split("_", 1)[0]
            meta = image_lookup.get(prefix, {})
            rows.append(
                {
                    "museum_id": museum_id,
                    "museum_name": seed.get("name", museum_dir.name),
                    "page_type": meta.get("page_type", image_path.parent.name),
                    "image_id": sha1_text(str(image_path.relative_to(self.input_dir))),
                    "image_url": meta.get("image_url", ""),
                    "alt": meta.get("alt", ""),
                    "title": meta.get("title", ""),
                    "source_page": meta.get("source_page", ""),
                    "local_path": str(image_path.relative_to(self.input_dir)),
                    "size_bytes": image_path.stat().st_size,
                    "extension": image_path.suffix.lower(),
                }
            )
        return rows

    def _choose_metadata(self, pages: list[dict[str, Any]]) -> dict[str, str]:
        chosen: dict[str, str] = {}
        for field in ("address", "phone", "email", "opening_hours"):
            value = self._choose_field_value(pages, field)
            if value:
                chosen[field] = value
        return chosen

    def _choose_field_value(self, pages: list[dict[str, Any]], field: str) -> str:
        page_priority = FIELD_PAGE_PRIORITY.get(field, PAGE_TYPE_PRIORITY)
        candidates: list[tuple[int, int, str]] = []
        for page in pages:
            value = clean_text(str((page.get("metadata") or {}).get(field, "")))
            if not value:
                continue
            page_type = page.get("page_type", "other")
            priority = page_priority.index(page_type) if page_type in page_priority else len(page_priority)
            quality = self._metadata_quality(field, value)
            candidates.append((priority, -quality, value))
        if not candidates:
            return ""
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        return candidates[0][2]

    def _metadata_quality(self, field: str, value: str) -> int:
        score = len(value)
        if field == "opening_hours":
            if any(marker in value for marker in ("旺季", "淡季")):
                score += 30
            if "停止入馆" in value:
                score += 12
            if "周一闭馆" in value:
                score += 8
            if "：" in value or ":" in value:
                score += 6
        elif field == "address":
            if any(marker in value for marker in ("北京市", "上海市", "区", "路", "街", "号")):
                score += 12
            if "邮编" in value or "电话" in value:
                score -= 20
        elif field == "phone":
            if value.startswith("400"):
                score += 6
        elif field == "email":
            if value.endswith(".cn"):
                score += 4
        return score

    def _choose_overview(self, pages: list[dict[str, Any]]) -> str:
        ordered = sorted(
            pages,
            key=self._overview_sort_key,
        )
        for page in ordered:
            summary = clean_text(page.get("summary", ""))
            if len(summary) >= 40:
                return summary[:400]
            text = clean_text(page.get("text", ""))
            if len(text) >= 40:
                return text[:400]
        return ""

    def _overview_sort_key(self, page: dict[str, Any]) -> tuple[int, int, str]:
        priority = OVERVIEW_PAGE_PRIORITY.index(page["page_type"]) if page["page_type"] in OVERVIEW_PAGE_PRIORITY else len(OVERVIEW_PAGE_PRIORITY)
        blob = clean_text(f"{page.get('title', '')} {page.get('url', '')} {page.get('summary', '')}").lower()
        score = 0
        if any(keyword in blob for keyword in ("简介", "概况", "介绍", "/gbgk/gbjj", "/about")):
            score += 40
        if "官方网站" in page.get("title", ""):
            score -= 18
        if len(clean_text(page.get("text", ""))) < 80:
            score -= 8
        return (priority, -score, page.get("title", ""))
