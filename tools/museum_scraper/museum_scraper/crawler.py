from __future__ import annotations

from collections import deque
from pathlib import Path
from urllib.parse import urlparse

from .config import CrawlConfig
from .fetching import WebFetcher
from .models import CrawlSummary, MuseumSeed, SearchResult
from .parsing import MuseumPageParser
from .search import BaseSearchProvider, build_search_provider, rank_search_results
from .storage import MuseumStorage
from .utils import get_scheme_and_host, normalize_url, registrable_domain


class MuseumCrawler:
    def __init__(
        self,
        config: CrawlConfig,
        *,
        search_provider: BaseSearchProvider | None = None,
    ) -> None:
        self.config = config
        self.search_provider = search_provider or build_search_provider(config)
        self.fetcher = WebFetcher(config)
        self.parser = MuseumPageParser(config)

    def crawl_from_seeds(
        self,
        seeds: list[MuseumSeed],
        max_museums: int | None = None,
        *,
        resume: bool = False,
    ) -> list[CrawlSummary]:
        summaries: list[CrawlSummary] = []
        for index, seed in enumerate(seeds):
            if max_museums is not None and index >= max_museums:
                break
            summaries.append(self.crawl_one(seed, resume=resume))
        return summaries

    def crawl_one(self, seed: MuseumSeed, *, resume: bool = False) -> CrawlSummary:
        storage = MuseumStorage(self.config.output_dir, seed.name)
        if resume:
            previous = storage.load_report()
            if previous:
                return CrawlSummary(
                    museum_name=previous.get("museum_name", seed.name),
                    province=previous.get("province", seed.province),
                    source=previous.get("source", seed.source),
                    resolved_site=previous.get("resolved_site", ""),
                    page_count=int(previous.get("page_count", 0)),
                    image_count=int(previous.get("image_count", 0)),
                    status="skipped_existing",
                    skipped_existing=True,
                    discovered_candidates=previous.get("discovered_candidates", []),
                    failures=previous.get("failures", []),
                )
        candidates = self._discover_candidates(seed)
        resolved_site = self._resolve_site(seed, candidates)
        summary = CrawlSummary(
            museum_name=seed.name,
            province=seed.province,
            source=seed.source,
            resolved_site=resolved_site,
            discovered_candidates=[candidate.to_dict() for candidate in candidates],
        )
        storage.save_museum_metadata(seed, candidates, resolved_site)
        if not resolved_site:
            summary.failures.append("未能发现可爬取的官网候选站点")
            storage.save_report(summary.to_dict())
            return summary

        allowed_domains = {
            urlparse(resolved_site).netloc.lower(),
            registrable_domain(resolved_site),
            *[domain.lower() for domain in self.config.extra_allowed_domains],
        }
        queue: deque[tuple[str, int]] = deque()
        root_url = normalize_url(f"{get_scheme_and_host(resolved_site)}/")
        seed_urls = list(dict.fromkeys([normalize_url(resolved_site), root_url]))
        for url in seed_urls:
            queue.append((url, 0))
        visited: set[str] = set()
        crawled_pages: set[str] = set()
        downloaded_images: set[str] = set()

        while queue and summary.page_count < self.config.max_pages_per_museum:
            url, depth = queue.popleft()
            if url in visited or depth > self.config.max_depth:
                continue
            visited.add(url)
            if not self.fetcher.in_allowed_domains(url, allowed_domains):
                continue
            if not self.fetcher.allowed_by_robots(url):
                summary.failures.append(f"robots.txt 拒绝访问: {url}")
                continue
            try:
                result = self.fetcher.fetch(url)
            except Exception as exc:
                summary.failures.append(f"抓取失败 {url}: {exc}")
                continue
            if result.final_url in crawled_pages:
                continue
            redirect_target = self.parser.extract_client_redirect(result.final_url, result.text)
            if redirect_target and redirect_target not in visited:
                if self.fetcher.in_allowed_domains(redirect_target, allowed_domains):
                    queue.appendleft((redirect_target, depth))
                    continue
            try:
                page = self.parser.parse(result.final_url, result.text, depth)
            except Exception as exc:
                summary.failures.append(f"解析失败 {result.final_url}: {exc}")
                continue
            saved = storage.save_page(page)
            crawled_pages.add(result.final_url)
            if not saved:
                continue
            summary.page_count += 1

            if self.config.download_images:
                for image in page.images:
                    if image.url in downloaded_images:
                        continue
                    if not self.config.allow_offsite_images and not self.fetcher.in_allowed_domains(image.url, allowed_domains):
                        continue
                    try:
                        binary = self.fetcher.fetch(image.url, allow_binary=True)
                    except Exception as exc:
                        summary.failures.append(f"图片下载失败 {image.url}: {exc}")
                        continue
                    if len(binary.content) > self.config.max_image_bytes:
                        summary.failures.append(f"图片过大已跳过 {image.url}")
                        continue
                    stored = storage.save_image_bytes(image, binary.content, binary.content_type)
                    if stored is not None:
                        downloaded_images.add(image.url)
                        summary.image_count += 1

            for next_link in page.next_links:
                if next_link in visited:
                    continue
                if not self.fetcher.in_allowed_domains(next_link, allowed_domains):
                    continue
                queue.append((next_link, depth + 1))

        storage.save_report(summary.to_dict())
        return summary

    def _discover_candidates(self, seed: MuseumSeed) -> list[SearchResult]:
        candidates: list[SearchResult] = []
        if seed.official_site:
            candidates.append(
                SearchResult(
                    title=f"{seed.name}（种子提供）",
                    url=seed.official_site,
                    snippet="来自种子文件的官方站点",
                    score=100.0,
                    source="seed",
                )
            )
            return candidates
        query = f"{seed.name} 官网"
        if seed.province:
            query = f"{seed.province} {query}"
        try:
            search_results = self.search_provider.search(query, self.config.max_search_results)
        except Exception:
            search_results = []
        candidates.extend(rank_search_results(seed, search_results))
        deduped: list[SearchResult] = []
        seen: set[str] = set()
        for candidate in candidates:
            normalized = normalize_url(candidate.url)
            if normalized in seen:
                continue
            candidate.url = normalized
            seen.add(normalized)
            deduped.append(candidate)
        return deduped

    def _resolve_site(self, seed: MuseumSeed, candidates: list[SearchResult]) -> str:
        if seed.official_site:
            return normalize_url(seed.official_site)
        return candidates[0].url if candidates else ""
