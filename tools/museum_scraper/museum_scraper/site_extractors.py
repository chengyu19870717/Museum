from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .models import ImageCandidate
from .utils import clean_text


EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
PHONE_RE = re.compile(
    r"(?:参观咨询热线|咨询热线|热线电话|咨询电话|联系电话|电话)[：:\s]*"
    r"((?:400[-\s]?\d{3,4}[-\s]?\d{3,4})|(?:0\d{2,3}[-\s]?\d{7,8})|(?:1[3-9]\d{9}))"
)
ADDRESS_PATTERNS = (
    re.compile(r"(?:通讯地址|地址|馆址)[：:\s]*([^。；\n]{6,120})"),
    re.compile(r"中国国家博物馆\s*((?:北京市|北京)[^。；\n]{6,80})"),
)
OPENING_SENTENCE_RE = re.compile(
    r"本馆每日\s*([0-9]{1,2}:\d{2})[—-]([0-9]{1,2}:\d{2})"
    r"（([0-9]{1,2}:\d{2})停止入馆）[，,]?\s*(周一闭馆（法定节假日除外）)"
)
OPENING_TIME_RE = re.compile(r"([0-9]{1,2}:\d{2})\s*(开馆时间|停止入馆|观众退场|闭馆时间)")
MONDAY_CLOSED_RE = re.compile(r"(?:每周一例行闭馆，?国家法定节假日除外|周一闭馆（法定节假日除外）)")
DPM_CONTACT_PHONE_RE = re.compile(r"(?:咨询电话|参观咨询)[：:；;\s]*((?:400[-\s]?\d{3,4}[-\s]?\d{3,4})|(?:0\d{2,3}[-\s]?\d{7,8}))")
DPM_CONTACT_ADDRESS_RE = re.compile(r"地址[：:\s]*((?:北京市|北京)[^。；\n]{6,80})")
DPM_PRIMARY_EMAIL_RE = re.compile(r"(?:电子邮件地址|联系方式)[：:\s]*([\w.+-]+@dpm\.org\.cn)", re.IGNORECASE)
DPM_WARM_SEASON_RE = re.compile(
    r"旺季\s*4\.1-10\.31"
    r".*?开放入馆时间[:：]\s*([0-9]{1,2}:\d{2})"
    r".*?停止入馆时间[:：]\s*([0-9]{1,2}:\d{2})"
    r".*?珍宝馆、钟表馆停止入馆时间[:：]\s*([0-9]{1,2}:\d{2})"
    r".*?闭馆时间[:：]\s*([0-9]{1,2}:\d{2})",
    re.S,
)
DPM_COLD_SEASON_RE = re.compile(
    r"(?:11\.1-3\.31\s*淡季|淡季\s*11\.1-3\.31)"
    r".*?开放入馆时间[:：]\s*([0-9]{1,2}:\d{2})"
    r".*?停止入馆时间[:：]\s*([0-9]{1,2}:\d{2})"
    r".*?珍宝馆、钟表馆停止入馆时间[:：]\s*([0-9]{1,2}:\d{2})"
    r".*?闭馆时间[:：]\s*([0-9]{1,2}:\d{2})",
    re.S,
)
DPM_MONDAY_RE = re.compile(r"周一(?:全天)?闭馆")


@dataclass(slots=True)
class SiteExtractionResult:
    title: str = ""
    text: str = ""
    summary: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


class BaseSiteExtractor:
    def matches(self, url: str) -> bool:
        raise NotImplementedError

    def extract(self, url: str, soup: BeautifulSoup, fallback_text: str) -> SiteExtractionResult:
        return SiteExtractionResult()

    def score_image(self, image: ImageCandidate) -> int:
        return 0


class ChinaNationalMuseumExtractor(BaseSiteExtractor):
    DOMAIN = "chnmuseum.cn"

    def matches(self, url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return host == self.DOMAIN or host.endswith(f".{self.DOMAIN}")

    def extract(self, url: str, soup: BeautifulSoup, fallback_text: str) -> SiteExtractionResult:
        path = urlparse(url).path.lower()
        result = SiteExtractionResult()

        article_title = self._select_first_text(soup, [".cj_xw_tt", ".fw_tit", "h1"])
        article_text = self._joined_text(soup, [".TRS_Editor"])
        service_text = self._joined_text(soup, [".fw_shmmlisjk", ".TRS_Editor"])
        contact_text = self._joined_text(soup, [".cj_xw_cong .TRS_Editor", ".TRS_Editor"])

        if "/gbgk/gbjj" in path:
            result.title = article_title
            result.text = article_text
        elif any(segment in path for segment in ("/lxwm/", "/rxdh/")):
            result.title = article_title
            result.text = contact_text
        elif path.rstrip("/") == "/cg":
            result.text = service_text

        text_for_metadata = clean_text(" ".join(part for part in (service_text, contact_text, fallback_text) if part))
        metadata = self._extract_metadata(text_for_metadata)
        if metadata:
            result.metadata.update(metadata)

        chosen_text = result.text or fallback_text
        if chosen_text:
            result.summary = clean_text(chosen_text[:200])
        return result

    def score_image(self, image: ImageCandidate) -> int:
        blob = f"{image.url} {image.alt} {image.title}".lower()
        score = 0
        if "/rqtp/" in blob:
            score += 20
        if any(segment in blob for segment in ("/upload/", "/uploadfile/", "/2020images/")):
            score += 6
        if any(segment in blob for segment in ("/bg/", "/logo", "/icon", "/nav/", "topbg", "bottombg")):
            score -= 10
        return score

    def _extract_metadata(self, text: str) -> dict[str, str]:
        metadata: dict[str, str] = {}
        compact_text = clean_text(text)

        phone_match = PHONE_RE.search(compact_text)
        if phone_match:
            metadata["phone"] = clean_text(phone_match.group(1))

        email_match = EMAIL_RE.search(compact_text)
        if email_match:
            metadata["email"] = clean_text(email_match.group(0))

        address = self._extract_address(compact_text)
        if address:
            metadata["address"] = address

        opening_hours = self._extract_opening_hours(compact_text)
        if opening_hours:
            metadata["opening_hours"] = opening_hours
        return metadata

    def _extract_address(self, text: str) -> str:
        for pattern in ADDRESS_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            value = match.group(1) if match.lastindex else match.group(0)
            normalized = clean_text(value)
            for marker in (
                "邮编",
                "电子邮箱",
                "邮箱",
                "参观咨询热线",
                "咨询热线",
                "热线电话",
                "联系电话",
                "电话",
                "本馆每日",
                "开放时间",
                "参观时间",
                "开馆时间",
                "闭馆时间",
                "停止入馆",
                "公交线路",
                "地铁线路",
                "预约须知",
                "文明参观",
            ):
                if marker in normalized:
                    normalized = normalized.split(marker, 1)[0].rstrip("，,、;；:： ")
            normalized = re.sub(r"^中国国家博物馆\s*", "", normalized)
            normalized = re.sub(r"\s*中国国家博物馆\s*$", "", normalized)
            normalized = normalized.strip("，,、;；:： ")
            if normalized.startswith("北京东城区"):
                normalized = "北京市东城区" + normalized[len("北京东城区") :]
            return normalized
        return ""

    def _extract_opening_hours(self, text: str) -> str:
        sentence_match = OPENING_SENTENCE_RE.search(text)
        if sentence_match:
            start_time, end_time, stop_entry, monday_note = sentence_match.groups()
            return f"{start_time}-{end_time}（{stop_entry}停止入馆），{monday_note}"

        time_lookup = {label: time for time, label in OPENING_TIME_RE.findall(text)}
        monday_match = MONDAY_CLOSED_RE.search(text)
        if not time_lookup:
            return ""

        segments: list[str] = []
        if time_lookup.get("开馆时间") and time_lookup.get("闭馆时间"):
            segments.append(f"{time_lookup['开馆时间']}-{time_lookup['闭馆时间']}")
        detail_bits: list[str] = []
        if time_lookup.get("停止入馆"):
            detail_bits.append(f"{time_lookup['停止入馆']}停止入馆")
        if time_lookup.get("观众退场"):
            detail_bits.append(f"{time_lookup['观众退场']}观众退场")
        if detail_bits:
            base = segments[0] if segments else ""
            if base:
                segments[0] = f"{base}（{'，'.join(detail_bits)}）"
            else:
                segments.append("，".join(detail_bits))
        if monday_match:
            segments.append("周一闭馆（法定节假日除外）")
        return "，".join(segment for segment in segments if segment)

    def _select_first_text(self, soup: BeautifulSoup, selectors: list[str]) -> str:
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                text = clean_text(node.get_text(" ", strip=True))
                if text:
                    return text
        return ""

    def _joined_text(self, soup: BeautifulSoup, selectors: list[str]) -> str:
        chunks: list[str] = []
        seen: set[str] = set()
        for selector in selectors:
            for node in soup.select(selector):
                text = clean_text(node.get_text(" ", strip=True))
                if not text or text in seen:
                    continue
                seen.add(text)
                chunks.append(text)
        return clean_text(" ".join(chunks))


class PalaceMuseumExtractor(BaseSiteExtractor):
    DOMAIN = "dpm.org.cn"

    def matches(self, url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return host == self.DOMAIN or host.endswith(f".{self.DOMAIN}")

    def extract(self, url: str, soup: BeautifulSoup, fallback_text: str) -> SiteExtractionResult:
        path = urlparse(url).path.lower()
        page_title = self._select_first_text(soup, ["title"])
        meta_description = self._meta_content(soup)
        footer_text = self._joined_text(soup, [".footer", ".footer1"])

        result = SiteExtractionResult()
        if path in {"/about.html", "/about"} or "/about/about_view" in path:
            result.title = "故宫博物院总说"
            result.text = self._joined_text(soup, [".always-wrap", ".x-container"])
        elif path == "/visit.html":
            result.title = "故宫博物院导览"
            result.text = self._joined_text(soup, [".visit2", ".visit5 .p", ".visit6"])
        elif "联系我们" in page_title or "/singles_detail/" in path:
            if "联系我们" in page_title:
                result.title = "联系我们"
                result.text = meta_description or self._joined_text(soup, [".article", ".x-container", ".always-wrap"])

        text_for_metadata = clean_text(" ".join(part for part in (result.text, meta_description, footer_text, fallback_text) if part))
        metadata = self._extract_metadata(path, text_for_metadata)
        if metadata:
            result.metadata.update(metadata)

        chosen_text = result.text or fallback_text
        if chosen_text:
            result.summary = clean_text(chosen_text[:220])
        return result

    def score_image(self, image: ImageCandidate) -> int:
        blob = f"{image.url} {image.alt} {image.title}".lower()
        score = 0
        if any(segment in blob for segment in ("/static/themes/", "/static/themes_wap/")):
            score -= 18
        if any(keyword in blob for keyword in ("学习强国", "视频号", "小程序", "微信", "微博", "抖音")):
            score -= 16
        if "/uploads/picture/" in blob:
            score -= 6
        if "/uploads/image/" in blob:
            score += 4
        if any(keyword in blob for keyword in ("故宫博物院", "数字文物库", "展览", "藏品", "导览")):
            score += 6
        return score

    def _extract_metadata(self, path: str, text: str) -> dict[str, str]:
        metadata: dict[str, str] = {}
        compact_text = clean_text(text)

        phone_match = DPM_CONTACT_PHONE_RE.search(compact_text) or PHONE_RE.search(compact_text)
        if phone_match:
            metadata["phone"] = clean_text(phone_match.group(1))

        primary_email_match = DPM_PRIMARY_EMAIL_RE.search(compact_text)
        if primary_email_match:
            metadata["email"] = clean_text(primary_email_match.group(1))
        else:
            all_emails = EMAIL_RE.findall(compact_text)
            preferred = next((email for email in all_emails if email.lower() == "gugong@dpm.org.cn"), "")
            if preferred:
                metadata["email"] = preferred
            elif all_emails:
                metadata["email"] = clean_text(all_emails[0])

        address_match = DPM_CONTACT_ADDRESS_RE.search(compact_text)
        if address_match:
            metadata["address"] = self._clean_dpm_address(address_match.group(1))

        if path == "/visit.html":
            opening_hours = self._extract_dpm_opening_hours(compact_text)
            if opening_hours:
                metadata["opening_hours"] = opening_hours
        return metadata

    def _extract_dpm_opening_hours(self, text: str) -> str:
        seasons: list[str] = []
        warm_match = DPM_WARM_SEASON_RE.search(text)
        if warm_match:
            start_time, stop_entry, treasure_stop, close_time = warm_match.groups()
            seasons.append(f"旺季4.1-10.31 {start_time}-{close_time}（{stop_entry}停止入馆，珍宝馆/钟表馆{treasure_stop}停止入馆）")
        cold_match = DPM_COLD_SEASON_RE.search(text)
        if cold_match:
            start_time, stop_entry, treasure_stop, close_time = cold_match.groups()
            seasons.append(f"淡季11.1-3.31 {start_time}-{close_time}（{stop_entry}停止入馆，珍宝馆/钟表馆{treasure_stop}停止入馆）")
        if not seasons:
            return ""
        if DPM_MONDAY_RE.search(text):
            seasons.append("周一闭馆（法定节假日除外）")
        return "；".join(seasons)

    def _clean_dpm_address(self, value: str) -> str:
        normalized = clean_text(value)
        for marker in ("邮编", "电子邮件地址", "咨询电话", "故宫博物院"):
            if marker in normalized:
                normalized = normalized.split(marker, 1)[0].rstrip("，,、;；:： ")
        return normalized.strip("，,、;；:： ")

    def _meta_content(self, soup: BeautifulSoup) -> str:
        for selector in ("meta[name='description']", "meta[name='Description']", "meta[property='og:description']"):
            node = soup.select_one(selector)
            if node and node.get("content"):
                return clean_text(node["content"])
        return ""

    def _select_first_text(self, soup: BeautifulSoup, selectors: list[str]) -> str:
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                text = clean_text(node.get_text(" ", strip=True))
                if text:
                    return text
        return ""

    def _joined_text(self, soup: BeautifulSoup, selectors: list[str]) -> str:
        chunks: list[str] = []
        seen: set[str] = set()
        for selector in selectors:
            for node in soup.select(selector):
                text = clean_text(node.get_text(" ", strip=True))
                if not text or text in seen:
                    continue
                seen.add(text)
                chunks.append(text)
        return clean_text(" ".join(chunks))


SITE_EXTRACTORS: tuple[BaseSiteExtractor, ...] = (
    ChinaNationalMuseumExtractor(),
    PalaceMuseumExtractor(),
)


def get_site_extractor(url: str) -> BaseSiteExtractor | None:
    for extractor in SITE_EXTRACTORS:
        if extractor.matches(url):
            return extractor
    return None
