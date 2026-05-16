from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Iterable

import requests

from .models import MuseumSeed
from .utils import dump_jsonl


PROVINCES = [
    "北京市",
    "上海市",
    "天津市",
    "重庆市",
    "河北省",
    "山东省",
    "辽宁省",
    "吉林省",
    "黑龙江省",
    "甘肃省",
    "青海省",
    "河南省",
    "江苏省",
    "湖北省",
    "湖南省",
    "江西省",
    "浙江省",
    "广东省",
    "云南省",
    "福建省",
    "海南省",
    "山西省",
    "四川省",
    "陕西省",
    "贵州省",
    "安徽省",
    "广西壮族自治区",
    "内蒙古自治区",
    "西藏自治区",
    "新疆维吾尔自治区",
    "宁夏回族自治区",
    "澳门特别行政区",
    "香港特别行政区",
    "台湾省",
]


class NchaMuseumDirectoryClient:
    """国家文物局“全国博物馆名录查询”客户端。

    说明：
    - 官方页面带验证码，脚本支持先下载验证码，再由人工输入。
    - 该接口是否允许一次验证码覆盖多次分页查询，取决于服务端当前策略。
    """

    PAGE_URL = "https://app.gjzwfw.gov.cn/jmopen/webapp/html5/gjwwjqgbwgmlcxpc/index.html"
    CAPTCHA_URL = "https://app.gjzwfw.gov.cn/jmopen/verifyCode.do"
    CAPTCHA_CHECK_URL = "https://app.gjzwfw.gov.cn/jmopen/checkValiCode.do"
    QUERY_URL = "https://app.gjzwfw.gov.cn/jimps/link.do?EDI-password=289suh28xq"

    def __init__(self, user_agent: str) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Referer": self.PAGE_URL,
                "Origin": "https://app.gjzwfw.gov.cn",
                "X-Requested-With": "XMLHttpRequest",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )

    def fetch_captcha(self, output_path: Path) -> Path:
        self.session.get(self.PAGE_URL, timeout=20)
        response = self.session.get(
            f"{self.CAPTCHA_URL}?width=100&height=55&random={time.time()}",
            timeout=20,
        )
        response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)
        return output_path

    def validate_captcha(self, code: str) -> bool:
        response = self.session.post(
            self.CAPTCHA_CHECK_URL,
            data={"code": code},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        return bool(payload.get("success"))

    def _build_payload(self, province: str, start: int, limit: int, name: str = "") -> dict[str, object]:
        request_time = str(int(time.time() * 1000))
        sign = hashlib.md5(f"gjwwjqgbwgmlcx{request_time}".encode("utf-8")).hexdigest()
        header = (
            '{"EDI-interCode":"public_loader","EDI-appId":"20250305142054",'
            '"EDI-appSecret":"FwJNqkQ7Pl3RdOOOFtMzSxeBmZDF5jDsNcgqH2rI31M0BA9a89817BztqZbkKiUzH1vHNhVZsVabKdcBtTz98PGSLv18BUVRzIoBznqLKPxi3GnJiah0Z7Q1S7wWwWEWnlOYqEVnuCaSpMMR9yNgCIlX4ybl1y7gRlhPHVT5FK8",'
            '"EDI-userName":"GZFW","EDI-password":"289suh28xq","EDI-token":""}'
        )
        return {
            "from": "1",
            "key": "0ca940f4c43a4e23b863d44d97c97d89",
            "requestTime": request_time,
            "sign": sign,
            "appId": "2025030510121801",
            "appSecret": "705f3c7a3278db5b21ded3ef59fdbacc89df7da2",
            "appUsername": "PUBLICBASICADMIN",
            "appPassword": "89qy1hgs",
            "buttCode": "museum_list",
            "OrderBy": "",
            "QWBWGML_SCDWMC": name,
            "QWBWGML_XZQ": province,
            "QWBWGML_SCDWXZMC": "",
            "QWBWGML_SCDWZLDJMC": "",
            "limit": limit,
            "start": start,
            "header": header,
            "TIME_START": "",
            "TIME_END": "",
        }

    def query_page(self, province: str, start: int = 0, limit: int = 100, name: str = "") -> dict:
        payload = self._build_payload(province=province, start=start, limit=limit, name=name)
        response = self.session.post(self.QUERY_URL, data={"param": __import__("json").dumps(payload, ensure_ascii=False)}, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get("error_code"):
            raise RuntimeError(f"官方接口返回错误: {data}")
        return data

    def iter_museums(self, captcha_code: str, provinces: Iterable[str] | None = None) -> list[MuseumSeed]:
        if not self.validate_captcha(captcha_code):
            raise RuntimeError("验证码校验失败，请重新获取验证码图片并输入。")
        rows: list[MuseumSeed] = []
        for province in provinces or PROVINCES:
            start = 0
            total = None
            while total is None or start < total:
                data = self.query_page(province=province, start=start, limit=100)
                total = int(data.get("totalCount", 0))
                for row in data.get("rows", []):
                    rows.append(
                        MuseumSeed(
                            name=row.get("QWBWGML_SCDWMC", "").strip(),
                            province=row.get("QWBWGML_XZQ", province).strip(),
                            source="ncha",
                            metadata={
                                "museum_type": row.get("QWBWGML_SCDWXZMC", ""),
                                "quality_level": row.get("QWBWGML_SCDWZLDJMC", ""),
                                "free_open": row.get("QWBWGML_SFMFKF", ""),
                                "collection_count": row.get("QWBWGML_CPS", ""),
                                "precious_collection_count": row.get("QWBWGML_ZGWW", ""),
                                "exhibition_count": row.get("QWBWGML_ZL", ""),
                                "education_event_count": row.get("QWBWGML_JYHD", ""),
                                "annual_visitors_10k": row.get("QWBWGML_CGRS", ""),
                            },
                        )
                    )
                start += 100
                if not data.get("rows"):
                    break
        return rows

    @staticmethod
    def export_jsonl(output_path: Path, museums: list[MuseumSeed]) -> None:
        dump_jsonl(output_path, [museum.to_dict() for museum in museums])
