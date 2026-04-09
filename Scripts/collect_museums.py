#!/usr/bin/env python3
"""
中国博物馆数据收集脚本
从 Wikipedia / Wikimedia Commons 抓取博物馆简介和图片
用法: python3 collect_museums.py
"""

import os
import json
import time
import ssl
import urllib.request
import urllib.parse
from pathlib import Path

# macOS Homebrew Python SSL 证书修复
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

DATA_DIR = Path(__file__).parent.parent / "MuseumData"
WIKI_API = "https://zh.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "MuseumApp/1.0 (iOS museum guide; contact@example.com)"}

# ── 博物馆列表 ──────────────────────────────────────────────────────────────
MUSEUMS = [
    # 北京
    {"id": "palace_museum",      "wiki": "故宫博物院",     "province": "北京", "city": "北京"},
    {"id": "national_museum_cn", "wiki": "中国国家博物馆", "province": "北京", "city": "北京"},
    {"id": "capital_museum",     "wiki": "首都博物馆",     "province": "北京", "city": "北京"},
    {"id": "natural_history_bj", "wiki": "中国自然博物馆", "province": "北京", "city": "北京"},
    {"id": "military_museum",    "wiki": "中国人民革命军事博物馆", "province": "北京", "city": "北京"},
    {"id": "science_museum_bj",  "wiki": "中国科学技术馆", "province": "北京", "city": "北京"},
    {"id": "aviation_museum",    "wiki": "中国航空博物馆", "province": "北京", "city": "北京"},
    {"id": "palace_museum_bj",   "wiki": "颐和园",         "province": "北京", "city": "北京"},
    # 上海
    {"id": "shanghai_museum",    "wiki": "上海博物馆",     "province": "上海", "city": "上海"},
    {"id": "shanghai_natural",   "wiki": "上海自然博物馆", "province": "上海", "city": "上海"},
    {"id": "shanghai_history",   "wiki": "上海历史博物馆", "province": "上海", "city": "上海"},
    {"id": "shanghai_science",   "wiki": "上海科技馆",     "province": "上海", "city": "上海"},
    {"id": "china_art_museum",   "wiki": "中华艺术宫",     "province": "上海", "city": "上海"},
    {"id": "powerstation_art",   "wiki": "上海当代艺术博物馆", "province": "上海", "city": "上海"},
    # 陕西
    {"id": "shaanxi_history",    "wiki": "陕西历史博物馆", "province": "陕西", "city": "西安"},
    {"id": "terracotta_army",    "wiki": "秦始皇帝陵博物院", "province": "陕西", "city": "西安"},
    {"id": "xian_museum",        "wiki": "西安博物院",     "province": "陕西", "city": "西安"},
    {"id": "han_yangling",       "wiki": "汉阳陵",         "province": "陕西", "city": "咸阳"},
    # 江苏
    {"id": "nanjing_museum",     "wiki": "南京博物院",     "province": "江苏", "city": "南京"},
    {"id": "nanjing_massacre",   "wiki": "侵华日军南京大屠杀遇难同胞纪念馆", "province": "江苏", "city": "南京"},
    {"id": "suzhou_museum",      "wiki": "苏州博物馆",     "province": "江苏", "city": "苏州"},
    {"id": "nanjing_city_museum","wiki": "南京市博物馆",   "province": "江苏", "city": "南京"},
    # 浙江
    {"id": "zhejiang_museum",    "wiki": "浙江省博物馆",   "province": "浙江", "city": "杭州"},
    {"id": "liangzhu_museum",    "wiki": "良渚博物院",     "province": "浙江", "city": "杭州"},
    {"id": "china_silk_museum",  "wiki": "中国丝绸博物馆", "province": "浙江", "city": "杭州"},
    {"id": "china_tea_museum",   "wiki": "中国茶叶博物馆", "province": "浙江", "city": "杭州"},
    # 湖南
    {"id": "hunan_museum",       "wiki": "湖南省博物馆",   "province": "湖南", "city": "长沙"},
    # 湖北
    {"id": "hubei_museum",       "wiki": "湖北省博物馆",   "province": "湖北", "city": "武汉"},
    # 四川
    {"id": "sichuan_museum",     "wiki": "四川博物院",     "province": "四川", "city": "成都"},
    {"id": "sanxingdui_museum",  "wiki": "三星堆博物馆",   "province": "四川", "city": "广汉"},
    {"id": "jinsha_museum",      "wiki": "金沙遗址博物馆", "province": "四川", "city": "成都"},
    # 河南
    {"id": "henan_museum",       "wiki": "河南博物院",     "province": "河南", "city": "郑州"},
    # 广东
    {"id": "guangdong_museum",   "wiki": "广东省博物馆",   "province": "广东", "city": "广州"},
    {"id": "guangzhou_museum",   "wiki": "广州博物馆",     "province": "广东", "city": "广州"},
    {"id": "nanyue_museum",      "wiki": "南越王博物院",   "province": "广东", "city": "广州"},
    # 辽宁
    {"id": "liaoning_museum",    "wiki": "辽宁省博物馆",   "province": "辽宁", "city": "沈阳"},
    # 山东
    {"id": "shandong_museum",    "wiki": "山东博物馆",     "province": "山东", "city": "济南"},
    {"id": "linzi_museum",       "wiki": "淄博市博物馆",   "province": "山东", "city": "淄博"},
    # 云南
    {"id": "yunnan_museum",      "wiki": "云南省博物馆",   "province": "云南", "city": "昆明"},
    {"id": "yunnan_ethnic",      "wiki": "云南民族博物馆", "province": "云南", "city": "昆明"},
    # 甘肃
    {"id": "gansu_museum",       "wiki": "甘肃省博物馆",   "province": "甘肃", "city": "兰州"},
    {"id": "dunhuang_museum",    "wiki": "莫高窟",         "province": "甘肃", "city": "敦煌"},
    # 山西
    {"id": "shanxi_museum",      "wiki": "山西博物院",     "province": "山西", "city": "太原"},
    # 河北
    {"id": "hebei_museum",       "wiki": "河北博物院",     "province": "河北", "city": "石家庄"},
    # 安徽
    {"id": "anhui_museum",       "wiki": "安徽博物院",     "province": "安徽", "city": "合肥"},
    # 福建
    {"id": "fujian_museum",      "wiki": "福建博物院",     "province": "福建", "city": "福州"},
    # 江西
    {"id": "jiangxi_museum",     "wiki": "江西省博物馆",   "province": "江西", "city": "南昌"},
    {"id": "jingdezhen_museum",  "wiki": "景德镇中国陶瓷博物馆", "province": "江西", "city": "景德镇"},
    # 吉林
    {"id": "jilin_museum",       "wiki": "吉林省博物院",   "province": "吉林", "city": "长春"},
    # 黑龙江
    {"id": "heilongjiang_museum","wiki": "黑龙江省博物馆", "province": "黑龙江","city": "哈尔滨"},
    # 新疆
    {"id": "xinjiang_museum",    "wiki": "新疆维吾尔自治区博物馆", "province": "新疆", "city": "乌鲁木齐"},
    # 西藏
    {"id": "tibet_museum",       "wiki": "西藏博物馆",     "province": "西藏", "city": "拉萨"},
    # 内蒙古
    {"id": "neimenggu_museum",   "wiki": "内蒙古博物院",   "province": "内蒙古","city": "呼和浩特"},
    # 宁夏
    {"id": "ningxia_museum",     "wiki": "宁夏回族自治区博物馆", "province": "宁夏", "city": "银川"},
    # 贵州
    {"id": "guizhou_museum",     "wiki": "贵州省博物馆",   "province": "贵州", "city": "贵阳"},
    # 广西
    {"id": "guangxi_museum",     "wiki": "广西壮族自治区博物馆", "province": "广西", "city": "南宁"},
    # 海南
    {"id": "hainan_museum",      "wiki": "海南省博物馆",   "province": "海南", "city": "海口"},
    # 重庆
    {"id": "chongqing_museum",   "wiki": "重庆中国三峡博物馆", "province": "重庆", "city": "重庆"},
    # 香港
    {"id": "hk_history_museum",  "wiki": "香港历史博物馆", "province": "香港", "city": "香港"},
    {"id": "hk_palace_museum",   "wiki": "香港故宫文化博物馆", "province": "香港", "city": "香港"},
    # 澳门
    {"id": "macau_museum",       "wiki": "澳门博物馆",     "province": "澳门", "city": "澳门"},
    # 台湾
    {"id": "npm_taipei",         "wiki": "国立故宫博物院", "province": "台湾", "city": "台北"},
    {"id": "npm_southern",       "wiki": "国立故宫博物院南院", "province": "台湾", "city": "嘉义"},
]


def api_get(url, params):
    params["format"] = "json"
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{query}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15, context=ssl_ctx) as resp:
        return json.loads(resp.read())


def get_wiki_summary(title):
    """获取 Wikipedia 摘要"""
    data = api_get(WIKI_API, {
        "action": "query",
        "titles": title,
        "prop": "extracts|coordinates|categories",
        "exintro": True,
        "explaintext": True,
        "exsectionformat": "plain",
        "cllimit": 20,
        "redirects": True,
    })
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        extract = page.get("extract", "")
        coords = page.get("coordinates", [{}])
        lat = coords[0].get("lat") if coords else None
        lon = coords[0].get("lon") if coords else None
        return extract[:2000], lat, lon  # 截取前 2000 字
    return "", None, None


def get_commons_images(wiki_title, max_images=10):
    """从 Wikimedia Commons 获取图片列表"""
    # 先获取 Wikipedia 页面上的图片
    data = api_get(WIKI_API, {
        "action": "query",
        "titles": wiki_title,
        "prop": "images",
        "imlimit": 30,
        "redirects": True,
    })
    pages = data.get("query", {}).get("pages", {})
    image_titles = []
    for page in pages.values():
        for img in page.get("images", []):
            t = img["title"]
            if any(t.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                if not any(skip in t.lower() for skip in ["icon", "logo", "flag", "map", "locator"]):
                    image_titles.append(t)

    return image_titles[:max_images]


def get_image_url(image_title):
    """获取图片的直链 URL 和元数据"""
    data = api_get(COMMONS_API, {
        "action": "query",
        "titles": image_title,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": 1200,
        "redirects": True,
    })
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        info_list = page.get("imageinfo", [])
        if not info_list:
            continue
        info = info_list[0]
        url = info.get("thumburl") or info.get("url")
        meta = info.get("extmetadata", {})
        caption = meta.get("ImageDescription", {}).get("value", "").strip()
        credit = meta.get("Artist", {}).get("value", "").strip()
        license_name = meta.get("LicenseShortName", {}).get("value", "").strip()
        # 清除 HTML 标签
        import re
        caption = re.sub(r"<[^>]+>", "", caption)[:100]
        credit = re.sub(r"<[^>]+>", "", credit)[:80]
        return url, caption, credit, license_name
    return None, "", "", ""


def download_image(url, dest_path):
    """下载图片到指定路径"""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20, context=ssl_ctx) as resp:
        data = resp.read()
    dest_path.write_bytes(data)


def process_museum(m):
    museum_dir = DATA_DIR / m["id"]
    info_path = museum_dir / "info.json"

    if info_path.exists():
        print(f"  [跳过] {m['wiki']} (已存在)")
        return

    print(f"  [处理] {m['wiki']}...")
    museum_dir.mkdir(parents=True, exist_ok=True)
    (museum_dir / "images").mkdir(exist_ok=True)

    # 获取简介
    summary, lat, lon = get_wiki_summary(m["wiki"])
    time.sleep(0.5)

    # 获取图片
    image_titles = get_commons_images(m["wiki"])
    time.sleep(0.5)

    images_meta = []
    for i, title in enumerate(image_titles):
        img_url, caption, credit, license_name = get_image_url(title)
        time.sleep(0.3)
        if not img_url:
            continue
        ext = ".jpg" if ".jpg" in img_url.lower() else ".png"
        filename = f"{i+1:02d}{ext}"
        dest = museum_dir / "images" / filename
        try:
            download_image(img_url, dest)
            images_meta.append({
                "filename": filename,
                "caption": caption or m["wiki"],
                "credit": credit or None,
                "license": license_name or "CC BY-SA"
            })
            print(f"    ✓ 图片 {filename}")
            time.sleep(0.3)
        except Exception as e:
            print(f"    ✗ 下载失败: {e}")

    # 写入 info.json
    info = {
        "id": m["id"],
        "name": m["wiki"],
        "englishName": "",
        "city": m["city"],
        "province": m["province"],
        "category": "综合",
        "founded": None,
        "area": None,
        "annualVisitors": None,
        "freeEntry": False,
        "address": "",
        "website": None,
        "phone": None,
        "openingHours": "请查看官网",
        "summary": summary,
        "highlights": [],
        "images": images_meta,
        "latitude": lat,
        "longitude": lon,
        "grade": None
    }
    info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2))
    print(f"    ✓ 保存 info.json ({len(images_meta)} 张图片)")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"数据目录: {DATA_DIR}")
    print(f"共 {len(MUSEUMS)} 家博物馆\n")

    for i, m in enumerate(MUSEUMS, 1):
        print(f"[{i}/{len(MUSEUMS)}] {m['wiki']}")
        try:
            process_museum(m)
        except Exception as e:
            print(f"  ✗ 错误: {e}")
        time.sleep(1)

    print("\n✅ 完成！")


if __name__ == "__main__":
    main()
