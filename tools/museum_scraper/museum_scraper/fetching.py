from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from .config import CrawlConfig
from .utils import registrable_domain


@dataclass(slots=True)
class FetchResult:
    url: str
    final_url: str
    status_code: int
    content_type: str
    text: str
    content: bytes


class WebFetcher:
    def __init__(self, config: CrawlConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": config.user_agent,
            }
        )
        self._robot_cache: dict[str, RobotFileParser] = {}
        self._last_request_at: dict[str, float] = {}

    def _sleep_if_needed(self, url: str) -> None:
        host = urlparse(url).netloc.lower()
        last = self._last_request_at.get(host)
        if last is not None:
            elapsed = time.monotonic() - last
            remaining = self.config.crawl_delay_seconds - elapsed
            if remaining > 0:
                time.sleep(remaining)
        self._last_request_at[host] = time.monotonic()

    def _robot_parser(self, url: str) -> RobotFileParser:
        parsed = urlparse(url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        if root not in self._robot_cache:
            parser = RobotFileParser()
            parser.set_url(f"{root}/robots.txt")
            try:
                parser.read()
            except Exception:
                parser = RobotFileParser()
            self._robot_cache[root] = parser
        return self._robot_cache[root]

    def allowed_by_robots(self, url: str) -> bool:
        if not self.config.obey_robots_txt:
            return True
        parser = self._robot_parser(url)
        try:
            return parser.can_fetch(self.config.user_agent, url)
        except Exception:
            return True

    def in_allowed_domains(self, url: str, allowed_domains: Iterable[str]) -> bool:
        host = urlparse(url).netloc.lower()
        host_root = registrable_domain(host)
        for allowed in allowed_domains:
            candidate = allowed.lower()
            if not candidate:
                continue
            if "://" in candidate:
                candidate = urlparse(candidate).netloc.lower()
            if host == candidate or host.endswith("." + candidate):
                return True
            if host_root == registrable_domain(candidate):
                return True
        return False

    def fetch(self, url: str, *, allow_binary: bool = False) -> FetchResult:
        self._sleep_if_needed(url)
        response = self.session.get(
            url,
            timeout=self.config.request_timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if not allow_binary and "html" not in content_type and "xml" not in content_type:
            raise ValueError(f"Unsupported content type: {content_type or 'unknown'}")
        if not response.encoding:
            response.encoding = response.apparent_encoding or "utf-8"
        text = response.text if not allow_binary else ""
        return FetchResult(
            url=url,
            final_url=response.url,
            status_code=response.status_code,
            content_type=content_type,
            text=text,
            content=response.content,
        )
