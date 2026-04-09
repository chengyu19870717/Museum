#!/usr/bin/env python3
"""为无图片博物馆从英文 Wikipedia 补充图片"""

import json, ssl, time, subprocess, urllib.request, urllib.parse, re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "MuseumData"
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
HEADERS = {"User-Agent": "Mozilla/5.0 MuseumApp/1.0 (educational)"}

EN_WIKI_MAP = {
    "hk_palace_museum":  "Hong Kong Palace Museum",
    "jingdezhen_museum": "Jingdezhen China Ceramics Museum",
    "macau_museum":      "Macau Museum",
    "natural_history_bj":"Beijing Museum of Natural History",
    "npm_southern":      "National Palace Museum Southern Branch",
}

def api_get(url, params):
    params["format"] = "json"
    req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15, context=ssl_ctx) as r:
        return json.loads(r.read())

def get_en_images(title, max_images=15):
    data = api_get("https://en.wikipedia.org/w/api.php", {
        "action": "query", "titles": title, "prop": "images",
        "imlimit": 50, "redirects": True,
    })
    titles = []
    for page in data.get("query", {}).get("pages", {}).values():
        for img in page.get("images", []):
            t = img["title"]
            if not any(t.lower().endswith(e) for e in [".jpg",".jpeg",".png"]): continue
            if any(s in t.lower() for s in ["icon","logo","flag","map","locator","stub"]): continue
            titles.append(t)
    return titles[:max_images]

def get_image_url(title):
    data = api_get("https://commons.wikimedia.org/w/api.php", {
        "action": "query", "titles": title, "prop": "imageinfo",
        "iiprop": "url|extmetadata", "iiurlwidth": "1200", "redirects": True,
    })
    for page in data.get("query", {}).get("pages", {}).values():
        info = page.get("imageinfo", [{}])[0]
        url = info.get("url", "")
        meta = info.get("extmetadata", {})
        caption = re.sub(r"<[^>]+>", "", meta.get("ImageDescription", {}).get("value", ""))[:100]
        license_name = meta.get("LicenseShortName", {}).get("value", "CC BY-SA")
        return url, caption.strip(), license_name
    return None, "", "CC BY-SA"

def download(url, dest):
    r = subprocess.run(["curl", "-s", "-L", "--max-time", "30", "-o", str(dest), url], capture_output=True)
    if r.returncode != 0 or dest.stat().st_size < 5000:
        dest.unlink(missing_ok=True)
        raise RuntimeError("下载失败或文件太小")
    return dest.stat().st_size

for museum_id, en_title in EN_WIKI_MAP.items():
    museum_dir = DATA_DIR / museum_id
    info_path = museum_dir / "info.json"
    if not info_path.exists():
        print(f"跳过 {museum_id}: 无 info.json"); continue

    images_dir = museum_dir / "images"
    images_dir.mkdir(exist_ok=True)
    existing = list(images_dir.glob("*.[jp][pn]g"))
    if len(existing) >= 3:
        print(f"跳过 {museum_id}: 已有 {len(existing)} 张"); continue

    print(f"处理 {museum_id} ({en_title})...")
    titles = get_en_images(en_title); time.sleep(0.5)

    with open(info_path) as f: info = json.load(f)
    images_meta = list(info.get("images", []))
    downloaded = len(existing)

    for t in titles:
        if downloaded >= 10: break
        url, caption, license_name = get_image_url(t); time.sleep(0.3)
        if not url: continue
        ext = ".png" if ".png" in url.lower() else ".jpg"
        dest = images_dir / f"{downloaded+1:02d}{ext}"
        try:
            size = download(url, dest)
            images_meta.append({"filename": dest.name, "caption": caption or en_title,
                                 "credit": None, "license": license_name})
            downloaded += 1
            print(f"  ✓ {dest.name} ({size//1024}KB)")
            time.sleep(0.3)
        except Exception as e:
            print(f"  ✗ {t[:40]}: {e}")

    info["images"] = images_meta
    info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2))
    print(f"  完成: {downloaded} 张图片")

print("\n✅ 补充完成")
