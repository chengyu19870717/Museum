from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from .config import CrawlConfig
from .crawler import MuseumCrawler
from .dataset import DatasetBuilder
from .models import MuseumSeed
from .official_sources import NchaMuseumDirectoryClient
from .seeds import split_seeds_by_province, write_split_seed_files


def load_seeds(path: Path) -> list[MuseumSeed]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return [
                MuseumSeed(
                    name=(row.get("name") or "").strip(),
                    province=(row.get("province") or "").strip(),
                    city=(row.get("city") or "").strip(),
                    official_site=(row.get("official_site") or "").strip(),
                    source=(row.get("source") or "csv").strip(),
                )
                for row in reader
                if (row.get("name") or "").strip()
            ]
    if suffix in {".jsonl", ".json"}:
        rows: list[dict] = []
        if suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as handle:
                rows = [json.loads(line) for line in handle if line.strip()]
        else:
            rows = json.loads(path.read_text(encoding="utf-8"))
        return [
            MuseumSeed(
                name=(row.get("name") or "").strip(),
                province=(row.get("province") or "").strip(),
                city=(row.get("city") or "").strip(),
                official_site=(row.get("official_site") or "").strip(),
                aliases=row.get("aliases") or [],
                source=(row.get("source") or "json").strip(),
                metadata=row.get("metadata") or {},
            )
            for row in rows
            if (row.get("name") or "").strip()
        ]
    raise ValueError(f"不支持的种子文件类型: {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="全国博物馆素材采集工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    captcha_parser = subparsers.add_parser("official-captcha", help="获取国家文物局名录验证码图片")
    captcha_parser.add_argument("--output", required=True, type=Path, help="验证码图片保存路径")

    export_parser = subparsers.add_parser("official-export", help="导出国家文物局博物馆名录为 JSONL")
    export_parser.add_argument("--captcha", required=True, help="人工识别后的验证码")
    export_parser.add_argument("--output", required=True, type=Path, help="导出 JSONL 路径")
    export_parser.add_argument("--province", default="", help="只导出指定省份")

    split_parser = subparsers.add_parser("seed-split", help="按省份拆分种子文件")
    split_parser.add_argument("--seed-file", required=True, type=Path, help="CSV/JSON/JSONL 种子文件")
    split_parser.add_argument("--output-dir", required=True, type=Path, help="拆分后的 JSONL 输出目录")

    crawl_parser = subparsers.add_parser("crawl", help="从种子文件批量爬取")
    crawl_parser.add_argument("--seed-file", required=True, type=Path, help="CSV/JSON/JSONL 种子文件")
    crawl_parser.add_argument("--output", required=True, type=Path, help="素材输出目录")
    crawl_parser.add_argument("--search-provider", default="bing", choices=["bing", "manual"], help="官网发现策略")
    crawl_parser.add_argument("--max-museums", type=int, default=0, help="最多采集多少家，0 表示全部")
    crawl_parser.add_argument("--max-pages", type=int, default=60, help="每馆最大页面数")
    crawl_parser.add_argument("--max-depth", type=int, default=2, help="站内最大深度")
    crawl_parser.add_argument("--no-images", action="store_true", help="只抓文本不下载图片")
    crawl_parser.add_argument("--allow-offsite-images", action="store_true", help="允许下载 CDN 等站外图片")
    crawl_parser.add_argument("--ignore-robots", action="store_true", help="忽略 robots.txt 限制")
    crawl_parser.add_argument("--resume", action="store_true", help="存在 crawl_report.json 时跳过")

    batch_parser = subparsers.add_parser("crawl-batch", help="按省份分批爬取并生成批处理报告")
    batch_parser.add_argument("--seed-file", required=True, type=Path, help="CSV/JSON/JSONL 种子文件")
    batch_parser.add_argument("--output", required=True, type=Path, help="素材输出目录")
    batch_parser.add_argument("--search-provider", default="bing", choices=["bing", "manual"], help="官网发现策略")
    batch_parser.add_argument("--max-pages", type=int, default=60, help="每馆最大页面数")
    batch_parser.add_argument("--max-depth", type=int, default=2, help="站内最大深度")
    batch_parser.add_argument("--no-images", action="store_true", help="只抓文本不下载图片")
    batch_parser.add_argument("--allow-offsite-images", action="store_true", help="允许下载 CDN 等站外图片")
    batch_parser.add_argument("--ignore-robots", action="store_true", help="忽略 robots.txt 限制")
    batch_parser.add_argument("--resume", action="store_true", help="存在 crawl_report.json 时跳过")
    batch_parser.add_argument("--province", default="", help="只跑指定省份")
    batch_parser.add_argument("--max-museums-per-province", type=int, default=0, help="每省最多跑多少家，0 表示全部")
    batch_parser.add_argument("--report-path", type=Path, default=None, help="批处理报告输出路径")

    single_parser = subparsers.add_parser("crawl-one", help="手工指定一个博物馆做单馆采集")
    single_parser.add_argument("--name", required=True, help="博物馆名称")
    single_parser.add_argument("--province", default="", help="省份")
    single_parser.add_argument("--official-site", default="", help="已知官网，填了就优先使用")
    single_parser.add_argument("--output", required=True, type=Path, help="素材输出目录")
    single_parser.add_argument("--search-provider", default="bing", choices=["bing", "manual"], help="官网发现策略")
    single_parser.add_argument("--max-pages", type=int, default=60, help="每馆最大页面数")
    single_parser.add_argument("--max-depth", type=int, default=2, help="站内最大深度")
    single_parser.add_argument("--no-images", action="store_true", help="只抓文本不下载图片")
    single_parser.add_argument("--allow-offsite-images", action="store_true", help="允许下载站外图片")
    single_parser.add_argument("--ignore-robots", action="store_true", help="忽略 robots.txt 限制")

    dataset_parser = subparsers.add_parser("dataset-build", help="把采集结果汇总成标准数据集")
    dataset_parser.add_argument("--input", required=True, type=Path, help="素材输出目录")
    dataset_parser.add_argument("--output", required=True, type=Path, help="标准数据集输出目录")

    audit_parser = subparsers.add_parser("crawl-audit", help="审计采集结果的字段完整度")
    audit_parser.add_argument("--input", required=True, type=Path, help="素材输出目录")
    audit_parser.add_argument("--output", required=True, type=Path, help="审计报告输出 JSON 路径")

    return parser


def make_config(args: argparse.Namespace) -> CrawlConfig:
    return CrawlConfig(
        output_dir=args.output,
        max_pages_per_museum=args.max_pages,
        max_depth=args.max_depth,
        download_images=not getattr(args, "no_images", False),
        allow_offsite_images=getattr(args, "allow_offsite_images", False),
        search_provider=args.search_provider,
        obey_robots_txt=not getattr(args, "ignore_robots", False),
    )


def cmd_official_captcha(args: argparse.Namespace) -> int:
    client = NchaMuseumDirectoryClient(user_agent=CrawlConfig.default(".").user_agent)
    output = client.fetch_captcha(args.output)
    print(output)
    return 0


def cmd_official_export(args: argparse.Namespace) -> int:
    client = NchaMuseumDirectoryClient(user_agent=CrawlConfig.default(".").user_agent)
    provinces = [args.province] if args.province else None
    museums = client.iter_museums(captcha_code=args.captcha, provinces=provinces)
    client.export_jsonl(args.output, museums)
    print(json.dumps({"count": len(museums), "output": str(args.output)}, ensure_ascii=False))
    return 0


def cmd_seed_split(args: argparse.Namespace) -> int:
    seeds = load_seeds(args.seed_file)
    groups = split_seeds_by_province(seeds)
    paths = write_split_seed_files(args.output_dir, groups)
    print(
        json.dumps(
            {
                "province_count": len(groups),
                "file_count": len(paths),
                "output_dir": str(args.output_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_crawl(args: argparse.Namespace) -> int:
    seeds = load_seeds(args.seed_file)
    config = make_config(args)
    crawler = MuseumCrawler(config)
    limit = args.max_museums if args.max_museums > 0 else None
    summaries = crawler.crawl_from_seeds(seeds, max_museums=limit, resume=args.resume)
    print(json.dumps([summary.to_dict() for summary in summaries], ensure_ascii=False, indent=2))
    return 0


def cmd_crawl_batch(args: argparse.Namespace) -> int:
    seeds = load_seeds(args.seed_file)
    groups = split_seeds_by_province(seeds)
    if args.province:
        groups = {args.province: groups.get(args.province, [])}
    config = make_config(args)
    crawler = MuseumCrawler(config)
    batch_report: dict[str, object] = {
        "seed_file": str(args.seed_file),
        "output": str(args.output),
        "province_reports": [],
    }
    for province, province_seeds in groups.items():
        if not province_seeds:
            continue
        limit = args.max_museums_per_province if args.max_museums_per_province > 0 else None
        summaries = crawler.crawl_from_seeds(province_seeds, max_museums=limit, resume=args.resume)
        batch_report["province_reports"].append(
            {
                "province": province,
                "museum_count": len(province_seeds if limit is None else province_seeds[:limit]),
                "completed_count": sum(1 for summary in summaries if summary.status == "completed"),
                "skipped_count": sum(1 for summary in summaries if summary.skipped_existing),
                "failure_count": sum(1 for summary in summaries if summary.failures),
                "summaries": [summary.to_dict() for summary in summaries],
            }
        )
    report_path = args.report_path or (args.output / "_batch_reports" / "crawl_batch_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(batch_report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report_path": str(report_path), "province_count": len(batch_report["province_reports"])}, ensure_ascii=False, indent=2))
    return 0


def cmd_crawl_one(args: argparse.Namespace) -> int:
    config = make_config(args)
    crawler = MuseumCrawler(config)
    summary = crawler.crawl_one(
        MuseumSeed(
            name=args.name,
            province=args.province,
            official_site=args.official_site,
            source="manual-cli",
        )
    )
    print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_dataset_build(args: argparse.Namespace) -> int:
    builder = DatasetBuilder(args.input, args.output)
    summary = builder.build()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def cmd_crawl_audit(args: argparse.Namespace) -> int:
    builder = DatasetBuilder(args.input, args.input)
    report = builder.audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "museum_count": report["museum_count"],
                "complete_count": report["complete_count"],
                "missing_required_counts": report["missing_required_counts"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command_map = {
        "official-captcha": cmd_official_captcha,
        "official-export": cmd_official_export,
        "seed-split": cmd_seed_split,
        "crawl": cmd_crawl,
        "crawl-batch": cmd_crawl_batch,
        "crawl-one": cmd_crawl_one,
        "dataset-build": cmd_dataset_build,
        "crawl-audit": cmd_crawl_audit,
    }
    return command_map[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
