from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse, urlunparse


INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\r\n]+')
WHITESPACE_RE = re.compile(r"\s+")


def clean_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value or "").strip()


def sanitize_filename(value: str, fallback: str = "untitled") -> str:
    normalized = unicodedata.normalize("NFKC", value or "").strip()
    normalized = INVALID_FILENAME_CHARS.sub("_", normalized)
    normalized = normalized.strip(" ._")
    return normalized or fallback


def normalize_url(url: str, base_url: str | None = None) -> str:
    full = urljoin(base_url or "", url.strip())
    parsed = urlparse(full)
    cleaned = parsed._replace(fragment="")
    return urlunparse(cleaned)


def get_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def get_scheme_and_host(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def same_host(url_a: str, url_b: str) -> bool:
    return get_domain(url_a) == get_domain(url_b)


def registrable_domain(host_or_url: str) -> str:
    host = host_or_url.lower()
    if "://" in host:
        host = get_domain(host)
    parts = [part for part in host.split(".") if part]
    if len(parts) <= 2:
        return host
    if host.endswith((".gov.cn", ".com.cn", ".org.cn", ".net.cn", ".edu.cn")):
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def sha1_text(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def dump_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def dump_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def sniff_extension(url: str, content_type: str = "") -> str:
    lower_url = url.lower()
    for extension in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"):
        if extension in lower_url:
            return extension
    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
    }
    return mapping.get(content_type.lower(), ".bin")
