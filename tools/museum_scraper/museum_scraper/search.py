from __future__ import annotations

from abc import ABC, abstractmethod
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from .config import CrawlConfig
from .models import MuseumSeed, SearchResult
from .utils import clean_text


NEGATIVE_DOMAINS = {
    "baike.baidu.com",
    "map.baidu.com",
    "www.baidu.com",
    "weibo.com",
    "www.weibo.com",
    "www.mafengwo.cn",
    "www.ctrip.com",
    "you.ctrip.com",
    "www.douyin.com",
    "mp.weixin.qq.com",
}


class BaseSearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, limit: int) -> list[SearchResult]:
        raise NotImplementedError


class ManualOnlySearchProvider(BaseSearchProvider):
    def search(self, query: str, limit: int) -> list[SearchResult]:
        return []


class BingSearchProvider(BaseSearchProvider):
    def __init__(self, config: CrawlConfig) -> None:
        import requests

        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": config.user_agent,
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )

    def search(self, query: str, limit: int) -> list[SearchResult]:
        url = f"https://www.bing.com/search?q={quote_plus(query)}"
        response = self.session.get(url, timeout=self.config.request_timeout_seconds)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results: list[SearchResult] = []
        for item in soup.select("li.b_algo"):
            anchor = item.select_one("h2 a")
            if anchor is None:
                continue
            href = anchor.get("href", "").strip()
            title = clean_text(anchor.get_text(" ", strip=True))
            snippet = clean_text(item.select_one(".b_caption p").get_text(" ", strip=True)) if item.select_one(".b_caption p") else ""
            if not href:
                continue
            results.append(SearchResult(title=title, url=href, snippet=snippet, source="bing"))
            if len(results) >= limit:
                break
        return results


def build_search_provider(config: CrawlConfig) -> BaseSearchProvider:
    provider = (config.search_provider or "").lower()
    if provider == "bing":
        return BingSearchProvider(config)
    return ManualOnlySearchProvider()


def rank_search_results(seed: MuseumSeed, results: list[SearchResult]) -> list[SearchResult]:
    museum_name = seed.name.strip()
    ranked: list[SearchResult] = []
    for result in results:
        score = result.score
        blob = f"{result.title} {result.url} {result.snippet}"
        if museum_name and museum_name in blob:
            score += 8.0
        if "官网" in blob or "官方网站" in blob:
            score += 4.0
        if any(alias and alias in blob for alias in seed.aliases):
            score += 2.5
        domain = result.url.split("/")[2].lower() if "://" in result.url else result.url.lower()
        if domain.endswith((".gov.cn", ".org.cn", ".edu.cn")):
            score += 2.0
        if "museum" in domain or "bwg" in domain:
            score += 2.0
        if domain in NEGATIVE_DOMAINS:
            score -= 10.0
        result.score = score
        ranked.append(result)
    ranked.sort(key=lambda item: item.score, reverse=True)
    deduped: list[SearchResult] = []
    seen_urls: set[str] = set()
    for item in ranked:
        if item.url in seen_urls:
            continue
        seen_urls.add(item.url)
        deduped.append(item)
    return deduped
