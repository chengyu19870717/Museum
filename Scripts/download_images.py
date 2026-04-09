#!/usr/bin/env python3
"""
修复版图片下载脚本 - 使用 Wikimedia Commons API 获取图片
"""

import json
import ssl
import time
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "MuseumData"
WIKI_API = "https://zh.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 MuseumApp/1.0 (educational; contact@example.com)"
}


def api_get(url, params):
    params["format"] = "json"
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{query}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15, context=ssl_ctx) as resp:
        return json.loads(resp.read())


def wikimedia_image_url(filename):
    """根据文件名生成 Wikimedia Commons 图片 URL（使用 MD5 路径规则）"""
    name = filename.replace("File:", "").replace(" ", "_")
    md5 = hashlib.md5(name.encode()).hexdigest()
    return f"https://upload.wikimedia.org/wikipedia/commons/{md5[0]}/{md5[:2]}/{urllib.parse.quote(name)}"


def get_page_images(wiki_title, max_images=10):
    """获取 Wikipedia 页面的图片文件名列表"""
    data = api_get(WIKI_API, {
        "action": "query",
        "titles": wiki_title,
        "prop": "images",
        "imlimit": 50,
        "redirects": True,
    })
    pages = data.get("query", {}).get("pages", {})
    titles = []
    for page in pages.values():
        for img in page.get("images", []):
            t = img["title"]
            lower = t.lower()
            if not any(lower.endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                continue
            if any(skip in lower for skip in ["icon", "logo", "flag", "map",
                                               "locator", "stub", "edit", "commons"]):
                continue
            titles.append(t)
    return titles[:max_images]


def get_image_metadata(titles_batch):
    """批量获取图片元数据和 URL"""
    pipe_titles = "|".join(titles_batch)
    data = api_get(COMMONS_API, {
        "action": "query",
        "titles": pipe_titles,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size",
        "iiurlwidth": 1200,
        "redirects": True,
    })
    results = {}
    pages = data.get("query", {}).get("pages", {})
    import re
    for page in pages.values():
        title = page.get("title", "")
        info_list = page.get("imageinfo", [])
        if not info_list:
            continue
        info = info_list[0]
        url = info.get("thumburl") or info.get("url", "")
        # 如果 thumburl 失败，用规则生成 URL
        if not url or "403" in str(url):
            url = wikimedia_image_url(title)
        meta = info.get("extmetadata", {})
        caption = re.sub(r"<[^>]+>", "", meta.get("ImageDescription", {}).get("value", ""))[:100]
        credit = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", ""))[:80]
        license_name = meta.get("LicenseShortName", {}).get("value", "CC BY-SA")
        results[title] = {
            "url": url,
            "caption": caption.strip(),
            "credit": credit.strip(),
            "license": license_name,
        }
    return results


def download_image(url, dest_path):
    """使用 curl 下载图片（绕过 Python urllib 403 问题）"""
    import subprocess
    result = subprocess.run(
        ["curl", "-s", "-L", "--max-time", "30", "-o", str(dest_path), url],
        capture_output=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl 失败: {result.stderr.decode()[:100]}")
    size = dest_path.stat().st_size
    if size < 5000:
        dest_path.unlink(missing_ok=True)
        raise ValueError(f"文件太小({size}B)，可能是错误页")
    return size


MUSEUM_WIKI_MAP = {
    "palace_museum":      "故宫博物院",
    "national_museum_cn": "中国国家博物馆",
    "capital_museum":     "首都博物馆",
    "natural_history_bj": "中国自然博物馆",
    "military_museum":    "中国人民革命军事博物馆",
    "science_museum_bj":  "中国科学技术馆",
    "aviation_museum":    "中国航空博物馆",
    "shanghai_museum":    "上海博物馆",
    "shanghai_natural":   "上海自然博物馆",
    "shanghai_history":   "上海历史博物馆",
    "shanghai_science":   "上海科技馆",
    "china_art_museum":   "中华艺术宫",
    "powerstation_art":   "上海当代艺术博物馆",
    "shaanxi_history":    "陕西历史博物馆",
    "terracotta_army":    "秦始皇帝陵博物院",
    "xian_museum":        "西安博物院",
    "han_yangling":       "汉阳陵",
    "nanjing_museum":     "南京博物院",
    "nanjing_massacre":   "侵华日军南京大屠杀遇难同胞纪念馆",
    "suzhou_museum":      "苏州博物馆",
    "zhejiang_museum":    "浙江省博物馆",
    "liangzhu_museum":    "良渚博物院",
    "china_silk_museum":  "中国丝绸博物馆",
    "china_tea_museum":   "中国茶叶博物馆",
    "hunan_museum":       "湖南省博物馆",
    "hubei_museum":       "湖北省博物馆",
    "sichuan_museum":     "四川博物院",
    "sanxingdui_museum":  "三星堆博物馆",
    "jinsha_museum":      "金沙遗址博物馆",
    "henan_museum":       "河南博物院",
    "guangdong_museum":   "广东省博物馆",
    "guangzhou_museum":   "广州博物馆",
    "nanyue_museum":      "南越王博物院",
    "liaoning_museum":    "辽宁省博物馆",
    "shandong_museum":    "山东博物馆",
    "yunnan_museum":      "云南省博物馆",
    "yunnan_ethnic":      "云南民族博物馆",
    "gansu_museum":       "甘肃省博物馆",
    "dunhuang_museum":    "莫高窟",
    "shanxi_museum":      "山西博物院",
    "hebei_museum":       "河北博物院",
    "anhui_museum":       "安徽博物院",
    "fujian_museum":      "福建博物院",
    "jiangxi_museum":     "江西省博物馆",
    "jingdezhen_museum":  "景德镇中国陶瓷博物馆",
    "jilin_museum":       "吉林省博物院",
    "heilongjiang_museum":"黑龙江省博物馆",
    "xinjiang_museum":    "新疆维吾尔自治区博物馆",
    "tibet_museum":       "西藏博物馆",
    "neimenggu_museum":   "内蒙古博物院",
    "ningxia_museum":     "宁夏回族自治区博物馆",
    "guizhou_museum":     "贵州省博物馆",
    "guangxi_museum":     "广西壮族自治区博物馆",
    "hainan_museum":      "海南省博物馆",
    "chongqing_museum":   "重庆中国三峡博物馆",
    "hk_history_museum":  "香港历史博物馆",
    "hk_palace_museum":   "香港故宫文化博物馆",
    "macau_museum":       "澳门博物馆",
    "npm_taipei":         "国立故宫博物院",
    "npm_southern":       "国立故宫博物院南院",
    "nanjing_city_museum":"南京市博物馆",
    "linzi_museum":       "淄博市博物馆",
    "palace_museum_bj":   "颐和园",
}


def process_museum_images(museum_id):
    museum_dir = DATA_DIR / museum_id
    info_path = museum_dir / "info.json"
    images_dir = museum_dir / "images"
    images_dir.mkdir(exist_ok=True)

    if not info_path.exists():
        print(f"  跳过 {museum_id}：无 info.json")
        return

    with open(info_path) as f:
        info = json.load(f)

    # 检查已有图片数量
    existing = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
    if len(existing) >= 3:
        print(f"  [跳过] {info['name']} 已有 {len(existing)} 张图片")
        return

    wiki_title = MUSEUM_WIKI_MAP.get(museum_id, info["name"])
    print(f"  获取图片列表: {wiki_title}")

    image_titles = get_page_images(wiki_title, max_images=15)
    time.sleep(0.5)

    if not image_titles:
        print(f"  无图片")
        return

    # 批量获取元数据
    meta = get_image_metadata(image_titles)
    time.sleep(0.5)

    images_meta = list(info.get("images", []))
    downloaded = len(existing)

    for i, (title, data) in enumerate(meta.items()):
        if downloaded >= 10:
            break
        if not data["url"]:
            continue
        ext = ".jpg"
        if ".png" in data["url"].lower():
            ext = ".png"
        filename = f"{downloaded+1:02d}{ext}"
        dest = images_dir / filename
        if dest.exists():
            downloaded += 1
            continue
        try:
            size = download_image(data["url"], dest)
            images_meta.append({
                "filename": filename,
                "caption": data["caption"] or wiki_title,
                "credit": data["credit"] or None,
                "license": data["license"] or "CC BY-SA",
            })
            downloaded += 1
            print(f"    ✓ {filename} ({size//1024}KB)")
            time.sleep(0.4)
        except Exception as e:
            print(f"    ✗ {title[:40]}: {e}")

    # 更新 info.json
    info["images"] = images_meta
    with open(info_path, "w") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(f"  ✓ {info['name']}: {downloaded} 张图片")


def main():
    museum_ids = sorted(MUSEUM_WIKI_MAP.keys())
    print(f"共 {len(museum_ids)} 家博物馆\n")
    for i, mid in enumerate(museum_ids, 1):
        print(f"[{i}/{len(museum_ids)}] {mid}")
        try:
            process_museum_images(mid)
        except Exception as e:
            print(f"  错误: {e}")
        time.sleep(0.8)
    print("\n✅ 图片下载完成！")


if __name__ == "__main__":
    main()
