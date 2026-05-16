from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from museum_scraper.dataset import DatasetBuilder
from museum_scraper.models import MuseumSeed
from museum_scraper.seeds import split_seeds_by_province
from museum_scraper.utils import dump_json


class DatasetAndSeedsTests(unittest.TestCase):
    def test_split_seeds_by_province(self) -> None:
        groups = split_seeds_by_province(
            [
                MuseumSeed(name="馆A", province="北京市"),
                MuseumSeed(name="馆B", province="北京市"),
                MuseumSeed(name="馆C", province="上海市"),
            ]
        )
        self.assertEqual(sorted(groups.keys()), ["上海市", "北京市"])
        self.assertEqual(len(groups["北京市"]), 2)

    def test_dataset_builder_exports_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "dataset"
            museum_dir = input_dir / "示例博物馆"
            pages_dir = museum_dir / "pages" / "overview"
            images_dir = museum_dir / "images" / "overview"
            pages_dir.mkdir(parents=True)
            images_dir.mkdir(parents=True)

            dump_json(
                museum_dir / "museum.json",
                {
                    "seed": {
                        "name": "示例博物馆",
                        "province": "北京市",
                        "city": "北京市",
                        "official_site": "https://example.cn/",
                        "source": "test",
                        "metadata": {"quality_level": "一级"},
                    },
                    "resolved_site": "https://example.cn/",
                    "candidates": [],
                },
            )
            dump_json(
                museum_dir / "crawl_report.json",
                {"museum_name": "示例博物馆", "page_count": 1, "image_count": 1, "failures": []},
            )
            dump_json(
                pages_dir / "aaaaaaaaaa_页面.json",
                {
                    "url": "https://example.cn/about",
                    "title": "示例博物馆简介",
                    "page_type": "overview",
                    "summary": "示例博物馆是一家以陶瓷与青铜器常设展为特色的综合博物馆，长期开放公共教育与数字导览服务。",
                    "text": "示例博物馆位于北京市东城区示例路 8 号。开放时间为周二至周日。",
                    "depth": 0,
                    "metadata": {
                        "address": "北京市东城区示例路 8 号",
                        "opening_hours": "周二至周日",
                        "email": "hello@example.cn",
                    },
                    "images": [
                        {
                            "url": "https://example.cn/image.jpg",
                            "alt": "外景",
                            "title": "",
                            "source_page": "https://example.cn/about",
                            "page_type": "overview",
                        }
                    ],
                },
            )
            (pages_dir / "aaaaaaaaaa_页面.md").write_text("# 示例", encoding="utf-8")
            (images_dir / "ce8fbb9e0d_外景.jpg").write_bytes(b"img")

            summary = DatasetBuilder(input_dir, output_dir).build()
            self.assertEqual(summary["museum_count"], 1)
            museums_path = output_dir / "museums.jsonl"
            self.assertTrue(museums_path.exists())
            museum_row = json.loads(museums_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(museum_row["name"], "示例博物馆")
            self.assertEqual(museum_row["address"], "北京市东城区示例路 8 号")
            self.assertEqual(museum_row["email"], "hello@example.cn")
            self.assertIn("陶瓷与青铜器常设展", museum_row["overview"])

    def test_dataset_audit_reports_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "dataset"

            complete_dir = input_dir / "完整博物馆"
            complete_pages = complete_dir / "pages" / "overview"
            complete_images = complete_dir / "images" / "overview"
            complete_pages.mkdir(parents=True)
            complete_images.mkdir(parents=True)
            dump_json(
                complete_dir / "museum.json",
                {
                    "seed": {"name": "完整博物馆", "province": "北京市", "official_site": "https://complete.example.cn/", "source": "test"},
                    "resolved_site": "https://complete.example.cn/",
                    "candidates": [],
                },
            )
            dump_json(
                complete_pages / "page.json",
                {
                    "url": "https://complete.example.cn/about",
                    "title": "完整博物馆简介",
                    "page_type": "overview",
                    "summary": "完整博物馆是一家长期开放的综合博物馆，面向公众提供馆藏展示、教育活动与数字导览服务。",
                    "text": "完整博物馆位于北京市东城区完整路 1 号。",
                    "depth": 0,
                    "metadata": {
                        "address": "北京市东城区完整路 1 号",
                        "phone": "010-12345678",
                        "email": "contact@complete.example.cn",
                        "opening_hours": "周二至周日 09:00-17:00",
                    },
                    "images": [],
                },
            )
            (complete_pages / "page.md").write_text("# 完整", encoding="utf-8")

            incomplete_dir = input_dir / "缺失博物馆"
            incomplete_pages = incomplete_dir / "pages" / "overview"
            incomplete_pages.mkdir(parents=True)
            dump_json(
                incomplete_dir / "museum.json",
                {
                    "seed": {"name": "缺失博物馆", "province": "上海市", "official_site": "https://missing.example.cn/", "source": "test"},
                    "resolved_site": "https://missing.example.cn/",
                    "candidates": [],
                },
            )
            dump_json(
                incomplete_pages / "page.json",
                {
                    "url": "https://missing.example.cn/about",
                    "title": "缺失博物馆简介",
                    "page_type": "overview",
                    "summary": "",
                    "text": "这是一段很短的说明。",
                    "depth": 0,
                    "metadata": {"phone": "021-76543210"},
                    "images": [],
                },
            )
            (incomplete_pages / "page.md").write_text("# 缺失", encoding="utf-8")

            builder = DatasetBuilder(input_dir, output_dir)
            report = builder.audit()
            self.assertEqual(report["museum_count"], 2)
            self.assertEqual(report["complete_count"], 1)
            self.assertEqual(report["missing_required_counts"]["overview"], 1)
            self.assertEqual(report["missing_required_counts"]["address"], 1)
            self.assertEqual(report["missing_required_counts"]["opening_hours"], 1)
            self.assertEqual(report["missing_optional_counts"]["email"], 1)
            self.assertEqual(report["museum_reports"][0]["name"], "缺失博物馆")
            self.assertEqual(report["museum_reports"][0]["missing_required_count"], 3)


if __name__ == "__main__":
    unittest.main()
