from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class MuseumSeed:
    name: str
    province: str = ""
    city: str = ""
    official_site: str = ""
    aliases: list[str] = field(default_factory=list)
    source: str = "manual"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    score: float = 0.0
    source: str = "search"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ImageCandidate:
    url: str
    alt: str = ""
    title: str = ""
    source_page: str = ""
    page_type: str = "other"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ParsedPage:
    url: str
    title: str
    page_type: str
    summary: str
    text: str
    depth: int
    metadata: dict[str, Any] = field(default_factory=dict)
    next_links: list[str] = field(default_factory=list)
    images: list[ImageCandidate] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["images"] = [image.to_dict() for image in self.images]
        return data


@dataclass(slots=True)
class CrawlSummary:
    museum_name: str
    province: str = ""
    source: str = ""
    resolved_site: str = ""
    page_count: int = 0
    image_count: int = 0
    status: str = "completed"
    skipped_existing: bool = False
    discovered_candidates: list[dict[str, Any]] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
