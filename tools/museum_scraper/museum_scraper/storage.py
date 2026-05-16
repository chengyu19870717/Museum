from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .models import ImageCandidate, MuseumSeed, ParsedPage, SearchResult
from .utils import dump_json, sanitize_filename, sha1_text, sniff_extension


class MuseumStorage:
    def __init__(self, base_dir: Path, museum_name: str) -> None:
        safe_name = sanitize_filename(museum_name)
        self.root = base_dir / safe_name
        self.pages_dir = self.root / "pages"
        self.images_dir = self.root / "images"
        self.root.mkdir(parents=True, exist_ok=True)
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self._saved_pages: set[str] = set()
        self._saved_images: set[str] = set()

    def save_museum_metadata(
        self,
        seed: MuseumSeed,
        candidates: list[SearchResult],
        resolved_site: str,
    ) -> None:
        dump_json(
            self.root / "museum.json",
            {
                "seed": seed.to_dict(),
                "resolved_site": resolved_site,
                "candidates": [candidate.to_dict() for candidate in candidates],
            },
        )

    def save_page(self, page: ParsedPage) -> bool:
        page_key = sha1_text(page.url)
        if page_key in self._saved_pages:
            return False
        self._saved_pages.add(page_key)
        page_type_dir = self.pages_dir / page.page_type
        page_type_dir.mkdir(parents=True, exist_ok=True)
        base_name = f"{page_key[:10]}_{sanitize_filename(page.title, fallback='page')[:60]}"
        dump_json(page_type_dir / f"{base_name}.json", page.to_dict())
        markdown = f"# {page.title}\n\n- URL: {page.url}\n- 类型: {page.page_type}\n\n{page.text}\n"
        (page_type_dir / f"{base_name}.md").write_text(markdown, encoding="utf-8")
        return True

    def save_image_bytes(
        self,
        image: ImageCandidate,
        content: bytes,
        content_type: str,
    ) -> Path | None:
        if image.url in self._saved_images:
            return None
        self._saved_images.add(image.url)
        page_type_dir = self.images_dir / image.page_type
        page_type_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha1(image.url.encode("utf-8")).hexdigest()
        extension = sniff_extension(image.url, content_type)
        label = sanitize_filename(image.alt or image.title or digest[:10], fallback=digest[:10])
        path = page_type_dir / f"{digest[:10]}_{label[:60]}{extension}"
        path.write_bytes(content)
        return path

    def save_report(self, report: dict) -> None:
        dump_json(self.root / "crawl_report.json", report)

    def load_report(self) -> dict | None:
        report_path = self.root / "crawl_report.json"
        if not report_path.exists():
            return None
        return json.loads(report_path.read_text(encoding="utf-8"))
