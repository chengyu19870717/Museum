from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)


@dataclass(slots=True)
class CrawlConfig:
    output_dir: Path
    request_timeout_seconds: int = 20
    crawl_delay_seconds: float = 1.0
    max_pages_per_museum: int = 60
    max_depth: int = 2
    max_search_results: int = 6
    max_images_per_page: int = 20
    max_image_bytes: int = 10 * 1024 * 1024
    min_text_chars: int = 120
    obey_robots_txt: bool = True
    download_images: bool = True
    allow_offsite_images: bool = False
    search_provider: str = "bing"
    user_agent: str = DEFAULT_USER_AGENT
    extra_allowed_domains: list[str] = field(default_factory=list)

    @classmethod
    def default(cls, output_dir: str | Path) -> "CrawlConfig":
        return cls(output_dir=Path(output_dir))
