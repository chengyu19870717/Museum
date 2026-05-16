from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .config import CrawlConfig
from .models import ImageCandidate, ParsedPage
from .site_extractors import BaseSiteExtractor, get_site_extractor
from .utils import clean_text, normalize_url


STRIP_TAGS = ["script", "style", "noscript", "svg", "canvas", "iframe", "footer"]
CONTENT_SELECTORS = [
    "article",
    "main",
    "[role=main]",
    ".article",
    ".article-content",
    ".content",
    ".detail",
    ".details",
    ".news-content",
    ".post-content",
    ".entry-content",
    ".rich_media_content",
    ".TRS_Editor",
    ".x-container",
    ".always-wrap",
    ".s-wrap",
    ".visit2",
    ".visit6",
]
LINK_KEYWORDS = (
    "简介",
    "概况",
    "介绍",
    "关于",
    "联系",
    "服务",
    "电话",
    "预约",
    "展馆",
    "展厅",
    "馆区",
    "场馆",
    "分馆",
    "馆藏",
    "藏品",
    "珍品",
    "文物",
    "展览",
    "陈列",
    "参观",
    "开放",
    "导览",
    "visit",
    "about",
    "contact",
    "guide",
    "ticket",
    "collection",
    "collections",
    "exhibition",
    "museum",
)
NEGATIVE_LINK_KEYWORDS = (
    "登录",
    "注册",
    "隐私政策",
    "版权声明",
    "网站地图",
    "留言板",
    "无障碍",
)
NEGATIVE_LINK_PATTERNS = (
    "/passport/",
    "/login",
    "type=register",
    "/privacy/",
    "/sitemap",
    "/copyright",
)
LINK_PRIORITY_KEYWORDS: tuple[tuple[str, int], ...] = (
    ("国博简介", 30),
    ("简介", 24),
    ("概况", 22),
    ("介绍", 20),
    ("关于", 18),
    ("联系我们", 52),
    ("热线电话", 28),
    ("联系电话", 26),
    ("开放时间", 28),
    ("参观时间", 26),
    ("预约入口", 24),
    ("参观须知", 24),
    ("讲解导览", 22),
    ("观众服务", 18),
    ("交通地理", 18),
    ("展馆", 18),
    ("展厅", 18),
    ("馆藏", 20),
    ("藏品", 20),
    ("保管", 20),
    ("征集", 18),
    ("基本陈列", 18),
    ("专题展览", 18),
    ("临时展览", 18),
)
PHONE_PATTERNS = [
    re.compile(r"(?:热线电话|咨询电话|联系电话|电话)[：:\s]*((?:400[-\s]?\d{3,4}[-\s]?\d{3,4})|(?:0\d{2,3}[-\s]?\d{7,8})|(?:1[3-9]\d{9}))"),
    re.compile(r"\b(400[-\s]?\d{3,4}[-\s]?\d{3,4}|0\d{2,3}[-\s]?\d{7,8}|1[3-9]\d{9})\b"),
]
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
ADDRESS_RE = re.compile(r"(?:地址|馆址|位于|坐落于)(?:为|是)?[：:\s]*([^。；\n]{6,80})")
OPENING_RE = re.compile(r"(?:开放时间|参观时间|开馆时间|闭馆时间|周一闭馆)(?:为|是)?[：:\s]*([^。；\n]{2,120})")
CLIENT_REDIRECT_PATTERNS = [
    re.compile(r"window\.location(?:\.href)?\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE),
    re.compile(r"location\.replace\(\s*['\"]([^'\"]+)['\"]\s*\)", re.IGNORECASE),
    re.compile(r"http-equiv=['\"]refresh['\"][^>]*content=['\"][^;]+;\s*url=([^'\">]+)", re.IGNORECASE),
]
NEGATIVE_REDIRECT_TARGETS = ("/member/logout", "/passport/login", "/login", "javascript:")
NEGATIVE_IMAGE_KEYWORDS = (
    "logo",
    "header",
    "search",
    "download",
    "icon",
    "menu",
    "nav",
    "banner-title",
    "weixin",
    "weibo",
    "douyin",
    "xiaohongshu",
    "qrcode",
    "qr",
    "servicehao",
    "dingyuehao",
    "app",
    "videohao",
    "xiaochengxu",
    "xuexiqiangguo",
    "微博",
    "微信",
    "抖音",
    "小红书",
    "服务号",
    "订阅号",
    "学习强国",
    "视频号",
    "小程序",
    "官方app",
    "app下载",
    "搜索",
    "下载",
    "联系我们",
    "英文网站",
)
POSITIVE_IMAGE_KEYWORDS = (
    "馆藏",
    "藏品",
    "文物",
    "展览",
    "展厅",
    "展馆",
    "保管",
    "征集",
    "珍品",
    "陈列",
    "外景",
    "海报",
    "公告",
    "介绍",
)
LOCATION_HINT_RE = re.compile(r"(?:省|市|区|县|镇|乡|街|路|道|巷|里|号|村|弄|大厦|广场|景区|馆)")
OPENING_HINT_RE = re.compile(r"(?:\d{1,2}[:：]\d{2}|周[一二三四五六日天]|每日|每天|旺季|淡季|闭馆|停止入馆)")
BAD_METADATA_HINTS = ("密码", "注册", "登录", "邮箱地址", "长度为", "特殊符号", "不允许有空格")


def detect_page_type(url: str, title: str, text: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.lower().rstrip("/")
    title_blob = title.lower()
    body_blob = text[:180].lower()
    strong_blob = f"{path} {title_blob}"
    full_blob = f"{strong_blob} {body_blob}"
    if path in {"", "/", "/index", "/index.html", "/index.htm", "/home", "/home.html"}:
        return "overview"
    if any(segment in path for segment in ("/zp", "/zj", "/collection", "/collections", "/relic", "/cangpin", "/wenwu")):
        return "collection"
    if any(segment in path for segment in ("/zl", "/exhibition", "/display")):
        return "exhibition"
    if any(segment in path for segment in ("/fw", "/cg", "/visit", "/ticket", "/yuyue", "/guide", "/contact", "/lxwm", "/rxdh")):
        return "visit"
    if any(segment in path for segment in ("/venue", "/hall", "/gallery", "/changguan", "/zhanting")):
        return "venue"
    if any(segment in path for segment in ("/gbgk", "/about", "/gaikuang", "/jianjie")):
        return "overview"
    if "官方网站" in title and not any(keyword in strong_blob for keyword in ("馆藏", "藏品", "展览", "展馆", "参观", "征集", "保管")):
        return "overview"
    if any(keyword in strong_blob for keyword in ("馆藏", "藏品", "文物", "征集", "保管", "collection", "relic")):
        return "collection"
    if any(keyword in strong_blob for keyword in ("展馆", "展厅", "馆区", "场馆", "venue", "hall")):
        return "venue"
    if any(keyword in strong_blob for keyword in ("展览", "陈列", "特展", "exhibition", "display")):
        return "exhibition"
    if any(keyword in strong_blob for keyword in ("参观", "开放", "预约", "购票", "visit", "ticket")):
        return "visit"
    if any(keyword in strong_blob for keyword in ("简介", "概况", "介绍", "关于", "about")):
        return "overview"
    if any(keyword in full_blob for keyword in ("馆藏", "藏品", "文物", "collection", "relic")):
        return "collection"
    if any(keyword in full_blob for keyword in ("展馆", "展厅", "馆区", "场馆", "venue", "hall")):
        return "venue"
    if any(keyword in full_blob for keyword in ("展览", "陈列", "特展", "exhibition", "display")):
        return "exhibition"
    if any(keyword in full_blob for keyword in ("参观", "开放", "预约", "购票", "visit", "ticket")):
        return "visit"
    if any(keyword in full_blob for keyword in ("简介", "概况", "介绍", "关于", "about")):
        return "overview"
    return "other"


class MuseumPageParser:
    def __init__(self, config: CrawlConfig) -> None:
        self.config = config

    def parse(self, url: str, html: str, depth: int) -> ParsedPage:
        soup = BeautifulSoup(html, "html.parser")
        for tag_name in STRIP_TAGS:
            for node in soup.find_all(tag_name):
                node.decompose()

        title = self._extract_title(soup)
        text = self._extract_text(soup)
        extractor = get_site_extractor(url)
        if extractor is not None:
            site_result = extractor.extract(url, soup, text)
            if site_result.title:
                title = site_result.title
            if site_result.text:
                text = site_result.text
        else:
            site_result = None
        page_type = detect_page_type(url, title, text)
        summary = site_result.summary if site_result and site_result.summary else self._extract_summary(soup, text)
        metadata = self._extract_metadata(text)
        if site_result:
            metadata.update({key: value for key, value in site_result.metadata.items() if value})
        links = self._extract_links(soup, url)
        images = self._extract_images(soup, url, page_type, extractor)
        return ParsedPage(
            url=url,
            title=title,
            page_type=page_type,
            summary=summary,
            text=text,
            depth=depth,
            metadata=metadata,
            next_links=links,
            images=images,
        )

    def extract_client_redirect(self, url: str, html: str) -> str:
        html = html or ""
        matches: list[str] = []
        for pattern in CLIENT_REDIRECT_PATTERNS:
            matches.extend(clean_text(match.group(1)) for match in pattern.finditer(html) if clean_text(match.group(1)))
        if not matches:
            return ""
        unique_matches = list(dict.fromkeys(matches))
        if len(unique_matches) != 1:
            return ""
        target = unique_matches[0]
        lower_target = target.lower()
        if any(marker in lower_target for marker in NEGATIVE_REDIRECT_TARGETS):
            return ""
        soup = BeautifulSoup(html, "html.parser")
        for tag_name in STRIP_TAGS:
            for node in soup.find_all(tag_name):
                node.decompose()
        visible_text = clean_text((soup.body or soup).get_text(" ", strip=True))
        if len(visible_text) > max(120, self.config.min_text_chars):
            return ""
        if target:
            return normalize_url(target, url)
        return ""

    def _extract_title(self, soup: BeautifulSoup) -> str:
        for selector in ("meta[property='og:title']", "meta[name='twitter:title']"):
            node = soup.select_one(selector)
            if node and node.get("content"):
                return clean_text(node["content"])
        for selector in ("h1", "title"):
            node = soup.select_one(selector)
            if node:
                text = clean_text(node.get_text(" ", strip=True))
                if text:
                    return text
        return "未命名页面"

    def _extract_text(self, soup: BeautifulSoup) -> str:
        candidates: list[str] = []
        for selector in CONTENT_SELECTORS:
            for node in soup.select(selector):
                text = clean_text(node.get_text(" ", strip=True))
                if len(text) >= self.config.min_text_chars:
                    candidates.append(text)
        if candidates:
            return max(candidates, key=len)
        body = soup.body or soup
        return clean_text(body.get_text(" ", strip=True))

    def _extract_summary(self, soup: BeautifulSoup, text: str) -> str:
        for selector in ("meta[name='description']", "meta[property='og:description']"):
            node = soup.select_one(selector)
            if node and node.get("content"):
                return clean_text(node["content"])
        if len(text) <= 200:
            return text
        return clean_text(text[:200])

    def _extract_metadata(self, text: str) -> dict[str, str]:
        metadata: dict[str, str] = {}
        compact_text = clean_text(text)
        for pattern in PHONE_PATTERNS:
            phone_match = pattern.search(compact_text)
            if phone_match:
                metadata["phone"] = clean_text(phone_match.group(1) if phone_match.lastindex else phone_match.group(0))
                break
        email_match = EMAIL_RE.search(compact_text)
        if email_match:
            metadata["email"] = clean_text(email_match.group(0))
        address_match = ADDRESS_RE.search(compact_text)
        if address_match and self._looks_like_address(address_match.group(1) if address_match.lastindex else address_match.group(0)):
            metadata["address"] = self._trim_value(clean_text(address_match.group(0)))
        opening_match = OPENING_RE.search(compact_text)
        opening_value = clean_text(opening_match.group(0)) if opening_match else ""
        if opening_value and self._looks_like_opening_hours(opening_value):
            metadata["opening_hours"] = self._trim_value(clean_text(opening_match.group(0)))
        return metadata

    def _looks_like_address(self, value: str) -> bool:
        normalized = clean_text(value)
        if not normalized:
            return False
        if any(marker in normalized for marker in BAD_METADATA_HINTS):
            return False
        return bool(LOCATION_HINT_RE.search(normalized))

    def _looks_like_opening_hours(self, value: str) -> bool:
        normalized = clean_text(value)
        if not normalized:
            return False
        if any(marker in normalized for marker in BAD_METADATA_HINTS):
            return False
        return bool(OPENING_HINT_RE.search(normalized))

    def _trim_value(self, value: str) -> str:
        for marker in (
            "开放时间",
            "参观时间",
            "开馆时间",
            "闭馆时间",
            "热线电话",
            "咨询电话",
            "联系电话",
            "电话",
            "地址",
            "馆址",
            "融媒矩阵",
            "网站地图",
            "友情链接",
            "版权声明",
            "隐私安全声明",
        ):
            if marker in value[1:]:
                value = value.split(marker, 1)[0].rstrip("，,、;；:： ")
        return value

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        links: list[tuple[int, str]] = []
        seen: set[str] = set()
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "").strip()
            text = clean_text(anchor.get_text(" ", strip=True))
            if not href or href.startswith(("javascript:", "mailto:", "tel:")):
                continue
            absolute = normalize_url(href, base_url)
            parsed = urlparse(absolute)
            if parsed.scheme not in {"http", "https"}:
                continue
            if text and any(keyword in text for keyword in NEGATIVE_LINK_KEYWORDS):
                continue
            lower_absolute = absolute.lower()
            if any(pattern in lower_absolute for pattern in NEGATIVE_LINK_PATTERNS):
                continue
            blob = f"{text} {absolute}".lower()
            if LINK_KEYWORDS and not any(keyword in blob for keyword in LINK_KEYWORDS):
                continue
            if absolute in seen:
                continue
            seen.add(absolute)
            score = self._score_link(text, absolute)
            links.append((score, absolute))
        links.sort(key=lambda item: (-item[0], item[1]))
        return [url for _, url in links[:120]]

    def _extract_images(
        self,
        soup: BeautifulSoup,
        base_url: str,
        page_type: str,
        extractor: BaseSiteExtractor | None = None,
    ) -> list[ImageCandidate]:
        images: list[tuple[int, ImageCandidate]] = []
        seen: set[str] = set()
        meta_image = soup.select_one("meta[property='og:image']")
        if meta_image and meta_image.get("content"):
            url = normalize_url(meta_image["content"], base_url)
            candidate = ImageCandidate(url=url, source_page=base_url, page_type=page_type)
            if self._should_keep_image(candidate):
                images.append((self._score_image(candidate, extractor), candidate))
                seen.add(url)
        for img in soup.find_all("img", src=True):
            src = normalize_url(img.get("src", "").strip(), base_url)
            if not src or src in seen:
                continue
            candidate = ImageCandidate(
                url=src,
                alt=clean_text(img.get("alt", "")),
                title=clean_text(img.get("title", "")),
                source_page=base_url,
                page_type=page_type,
            )
            if not self._should_keep_image(candidate):
                continue
            seen.add(src)
            images.append((self._score_image(candidate, extractor), candidate))
        images.sort(key=lambda item: (-item[0], item[1].url))
        return [candidate for _, candidate in images[: self.config.max_images_per_page]]

    def _score_link(self, text: str, absolute: str) -> int:
        score = 0
        blob = f"{text} {absolute}"
        lower_url = absolute.lower()
        parsed = urlparse(absolute)
        path = parsed.path.lower().rstrip("/")
        path_key = path.removesuffix(".html").removesuffix(".htm")
        path_parts = [part for part in path.split("/") if part]
        for keyword, weight in LINK_PRIORITY_KEYWORDS:
            if keyword in blob:
                score += weight
        if any(segment in lower_url for segment in ("/gbgk", "/about", "/gaikuang", "/jianjie")):
            score += 20
        if any(segment in lower_url for segment in ("/contact", "/lxwm", "/rxdh")):
            score += 40
        if any(segment in lower_url for segment in ("/cg", "/visit", "/ticket", "/guide", "/fw")):
            score += 18
        if any(segment in lower_url for segment in ("/zp", "/zj", "/collection", "/relic")):
            score += 16
        if any(segment in lower_url for segment in ("/zl", "/exhibition", "/display")):
            score += 14
        if path_key in {"/gbgk/gbjj", "/about"}:
            score += 70
        if path_key in {"/cg", "/visit", "/fw"}:
            score += 78
        if path_key in {"/zp", "/zj", "/zl"}:
            score += 28
        if path.endswith(".shtml"):
            score -= 10
        if 1 <= len(path_parts) <= 2:
            score += 8
        if absolute.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx")):
            score -= 20
        if any(marker in lower_url for marker in ("#/", "javascript:", "mailto:", "tel:")):
            score -= 30
        return score

    def _should_keep_image(self, image: ImageCandidate) -> bool:
        blob = f"{image.url} {image.alt} {image.title}".lower()
        if any(keyword in blob for keyword in NEGATIVE_IMAGE_KEYWORDS):
            if not any(keyword in f"{image.alt} {image.title}" for keyword in POSITIVE_IMAGE_KEYWORDS):
                return False
        if image.url.lower().endswith(("/blue.png", "/gray.png", "/grey.png")):
            return False
        if image.url.lower().endswith(".svg"):
            return False
        return True

    def _score_image(self, image: ImageCandidate, extractor: BaseSiteExtractor | None = None) -> int:
        blob = f"{image.url} {image.alt} {image.title}".lower()
        score = 0
        for keyword in POSITIVE_IMAGE_KEYWORDS:
            if keyword.lower() in blob:
                score += 8
        if image.alt or image.title:
            score += 3
        if image.page_type in {"collection", "exhibition", "venue"}:
            score += 6
        if any(keyword in blob for keyword in NEGATIVE_IMAGE_KEYWORDS):
            score -= 12
        if extractor is not None:
            score += extractor.score_image(image)
        return score
