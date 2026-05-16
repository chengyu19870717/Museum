#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "MuseumAppDataBot/1.0 (local data enrichment)"

MUNICIPALITIES = {"北京", "天津", "上海", "重庆", "香港", "澳门"}

SIMPLIFIED_TRANSLATION = str.maketrans(
    {
        "臺": "台",
        "台": "台",
        "灣": "湾",
        "門": "门",
        "館": "馆",
        "國": "国",
        "歷": "历",
        "史": "史",
        "藝": "艺",
        "術": "术",
        "戰": "战",
        "爭": "争",
        "與": "与",
        "資": "资",
        "訊": "讯",
        "賽": "赛",
        "馬": "马",
        "電": "电",
        "鐵": "铁",
        "鐘": "钟",
        "錶": "表",
        "貝": "贝",
        "殼": "壳",
        "運": "运",
        "動": "动",
        "紀": "纪",
        "會": "会",
        "學": "学",
        "醫": "医",
        "陳": "陈",
        "鄉": "乡",
        "飲": "饮",
        "區": "区",
        "縣": "县",
        "廣": "广",
        "東": "东",
        "濟": "济",
        "陽": "阳",
        "蘇": "苏",
        "州": "州",
        "劇": "剧",
        "號": "号",
        "艦": "舰",
        "隊": "队",
        "華": "华",
        "婦": "妇",
        "兒": "儿",
        "童": "童",
        "禮": "礼",
        "畫": "画",
        "視": "视",
        "覺": "觉",
        "龍": "龙",
        "灣": "湾",
        "嶺": "岭",
        "當": "当",
        "業": "业",
        "積": "积",
        "遜": "逊",
        "歸": "归",
        "賀": "贺",
        "車": "车",
        "棟": "栋",
        "孫": "孙",
        "貢": "贡",
        "許": "许",
        "質": "质",
        "兩": "两",
        "偽": "伪",
        "滿": "满",
        "鄭": "郑",
        "則": "则",
        "漢": "汉",
        "蠟": "蜡",
        "環": "环",
        "韻": "韵",
        "錄": "录",
        "發": "发",
        "幣": "币",
        "書": "书",
        "樂": "乐",
        "園": "园",
        "貿": "贸",
        "體": "体",
        "揚": "扬",
        "宮": "宫",
        "處": "处",
        "場": "场",
        "號": "号",
    }
)

PROVINCE_NAMES = {
    "北京市": "北京",
    "天津市": "天津",
    "上海市": "上海",
    "重庆市": "重庆",
    "河北省": "河北",
    "山西省": "山西",
    "辽宁省": "辽宁",
    "吉林省": "吉林",
    "黑龙江省": "黑龙江",
    "江苏省": "江苏",
    "浙江省": "浙江",
    "安徽省": "安徽",
    "福建省": "福建",
    "江西省": "江西",
    "山东省": "山东",
    "河南省": "河南",
    "湖北省": "湖北",
    "湖南省": "湖南",
    "广东省": "广东",
    "海南省": "海南",
    "四川省": "四川",
    "贵州省": "贵州",
    "云南省": "云南",
    "陕西省": "陕西",
    "甘肃省": "甘肃",
    "青海省": "青海",
    "台湾省": "台湾",
    "内蒙古自治区": "内蒙古",
    "广西壮族自治区": "广西",
    "西藏自治区": "西藏",
    "宁夏回族自治区": "宁夏",
    "新疆维吾尔自治区": "新疆",
    "香港特别行政区": "香港",
    "澳门特别行政区": "澳门",
}

SHORT_PROVINCE_ALIASES = {
    "北京": "北京",
    "天津": "天津",
    "上海": "上海",
    "重庆": "重庆",
    "河北": "河北",
    "山西": "山西",
    "辽宁": "辽宁",
    "吉林": "吉林",
    "黑龙江": "黑龙江",
    "江苏": "江苏",
    "浙江": "浙江",
    "安徽": "安徽",
    "福建": "福建",
    "江西": "江西",
    "山东": "山东",
    "河南": "河南",
    "湖北": "湖北",
    "湖南": "湖南",
    "广东": "广东",
    "海南": "海南",
    "四川": "四川",
    "贵州": "贵州",
    "云南": "云南",
    "陕西": "陕西",
    "甘肃": "甘肃",
    "青海": "青海",
    "台湾": "台湾",
    "内蒙古": "内蒙古",
    "广西": "广西",
    "西藏": "西藏",
    "宁夏": "宁夏",
    "新疆": "新疆",
    "香港": "香港",
    "澳门": "澳门",
    "澳門": "澳门",
    "臺灣": "台湾",
    "台灣": "台湾",
    "廣東": "广东",
    "山東": "山东",
    "遼寧": "辽宁",
    "陝西": "陕西",
    "雲南": "云南",
    "貴州": "贵州",
    "廣西": "广西",
    "寧夏": "宁夏",
    "內蒙古": "内蒙古",
}

CATEGORY_KEYWORDS = [
    ("革命纪念", ["革命", "烈士", "抗战", "抗日", "抗美援朝", "起义", "会址", "红色", "长征", "周恩来", "邓颖超", "毛泽东", "雷锋", "孙中山", "九一八", "九·一八", "路矿工人", "中共", "resistance", "war of resistance"]),
    ("军事", ["军事", "军博", "战役", "国防", "兵器", "海军", "陆军", "空军", "航空母舰"]),
    ("自然", ["自然", "地质", "恐龙", "动物", "植物", "海洋", "生态", "古生物", "化石", "贝壳", "natural history", "paleozoological"]),
    ("科技", ["科技", "科学", "航天", "航空", "铁路", "铁道", "工业", "电信", "通讯", "通信", "计算机", "天文", "医学", "railway", "science", "technology", "aerospace"]),
    ("艺术", ["艺术", "美术", "画院", "书画", "油画", "雕塑", "当代", "徐悲鸿", "八大山人", "梅兰芳", "戏曲", "art", "visual arts"]),
    ("民俗", ["民俗", "民族", "非遗", "民间", "民居", "习俗"]),
    ("专题", ["丝绸", "茶", "陶瓷", "陶艺", "瓷", "邮政", "钱币", "电影", "文字", "运河", "海事", "航海", "警察", "警队", "园林", "昆曲", "建筑", "钟表", "印刷", "体育", "饮食", "海关", "汽车", "赛车", "赛马", "葡萄酒", "蜡像", "官窑", "典当", "回归贺礼", "film", "printing", "maritime"]),
    ("历史", ["历史", "遗址", "考古", "古墓", "陵", "故居", "古城", "石窟", "文化遗产", "文物", "半坡", "汉墓", "杜甫", "武侯祠", "孔庙", "老子", "林则徐", "伪满皇宫"]),
]

CITY_PROVINCE_HINTS = {
    "北京": "北京",
    "天津": "天津",
    "上海": "上海",
    "重庆": "重庆",
    "香港": "香港",
    "澳门": "澳门",
    "深圳": "广东",
    "广州": "广东",
    "成都": "四川",
    "苏州": "江苏",
    "无锡": "江苏",
    "扬州": "江苏",
    "南通": "江苏",
    "桂林": "广西",
    "唐山": "河北",
    "大连": "辽宁",
    "旅顺": "辽宁",
    "沈阳": "辽宁",
    "丹东": "辽宁",
    "洛阳": "河南",
    "郑州": "河南",
    "昆明": "云南",
    "济南": "山东",
    "临沂": "山东",
    "自贡": "四川",
    "韶山": "湖南",
    "长沙": "湖南",
    "荆州": "湖北",
    "萍乡": "江西",
    "杭州": "浙江",
    "乌镇": "浙江",
    "桐乡": "浙江",
    "西安": "陕西",
}

MANUAL_DUPLICATE_NAMES = {
    "秦始皇兵马俑",
}

MUSEUM_NAME_KEYWORDS = [
    "博物",
    "纪念",
    "陈列",
    "展示",
    "展览",
    "美术",
    "艺术",
    "科技馆",
    "科学馆",
    "历史馆",
    "文化馆",
    "资料馆",
    "档案馆",
    "故居",
    "遗址",
    "墓",
    "陵",
    "窟",
    "草堂",
    "祠",
    "苑",
]

HIGHLIGHTS_BY_CATEGORY = {
    "历史": ["地方历史文化陈列", "馆藏文物精品", "专题展览"],
    "艺术": ["馆藏艺术作品", "专题艺术展览", "公共教育活动"],
    "科技": ["科学互动展项", "科普教育活动", "专题展览"],
    "自然": ["自然标本陈列", "生态与地质展示", "科普教育活动"],
    "军事": ["军事历史陈列", "装备与文献展品", "国防教育展示"],
    "革命纪念": ["革命历史陈列", "文献与实物展品", "红色文化教育"],
    "民俗": ["民俗文化陈列", "非遗与生活器物", "地方文化展览"],
    "专题": ["专题收藏陈列", "主题文物展示", "公共教育活动"],
    "综合": ["综合历史陈列", "馆藏文物精品", "公共教育活动"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add a batch of Chinese museums from Wikidata.")
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent.parent / "MuseumData")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--query-limit", type=int, default=1000)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def request_json(url: str, timeout: int = 45, retries: int = 6) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code == 429:
                retry_after = error.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else 4.0 * (attempt + 1)
                time.sleep(delay)
                continue
            time.sleep(1.5 * (attempt + 1))
        except Exception as error:  # noqa: BLE001 - CLI should retry transient API failures.
            last_error = error
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Request failed after {retries} attempts: {url}") from last_error


def chunked(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def query_museum_qids(limit: int) -> list[str]:
    query = f"""
    SELECT DISTINCT ?item WHERE {{
      ?item wdt:P31/wdt:P279* wd:Q33506.
      ?item wdt:P17 wd:Q148.
    }}
    LIMIT {limit}
    """
    url = SPARQL_ENDPOINT + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    data = request_json(url, timeout=60)
    qids: list[str] = []
    for binding in data["results"]["bindings"]:
        qids.append(binding["item"]["value"].rsplit("/", 1)[-1])
    return qids


def fetch_entities(qids: list[str], props: str = "labels|descriptions|claims|sitelinks") -> dict[str, Any]:
    entities: dict[str, Any] = {}
    for group in chunked(qids, 25):
        url = WIKIDATA_API + "?" + urllib.parse.urlencode(
            {
                "action": "wbgetentities",
                "ids": "|".join(group),
                "props": props,
                "languages": "zh|zh-hans|zh-cn|en",
                "sitefilter": "zhwiki",
                "format": "json",
            }
        )
        data = request_json(url)
        entities.update(data.get("entities", {}))
        time.sleep(0.25)
    return entities


def localized_text(values: dict[str, Any], *languages: str) -> str | None:
    for language in languages:
        value = values.get(language, {}).get("value")
        if value:
            return value
    for value in values.values():
        if isinstance(value, dict) and value.get("value"):
            return value["value"]
    return None


def simplify_chinese(text: str) -> str:
    return text.translate(SIMPLIFIED_TRANSLATION)


def clean_name(text: str) -> str:
    text = simplify_chinese(text)
    text = re.sub(r"\s*\(([^)]+)\)", r"（\1）", text)
    return re.sub(r"\s+", "", text).strip()


def is_museum_like_name(text: str) -> bool:
    text = simplify_chinese(text)
    return any(keyword in text for keyword in MUSEUM_NAME_KEYWORDS)


def preferred_chinese_name(entity: dict[str, Any]) -> str | None:
    label = localized_text(entity.get("labels", {}), "zh", "zh-hans", "zh-cn")
    if not label:
        return None
    label = clean_name(label)
    title = entity.get("sitelinks", {}).get("zhwiki", {}).get("title")
    if isinstance(title, str):
        title = clean_name(title)
        if is_museum_like_name(title) and not is_museum_like_name(label):
            return title
    return label


def claim_datavalues(entity: dict[str, Any], property_id: str) -> list[Any]:
    values: list[Any] = []
    for claim in entity.get("claims", {}).get(property_id, []):
        datavalue = claim.get("mainsnak", {}).get("datavalue")
        if datavalue and "value" in datavalue:
            values.append(datavalue["value"])
    return values


def first_string_claim(entity: dict[str, Any], property_id: str) -> str | None:
    for value in claim_datavalues(entity, property_id):
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            text = value.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()
    return None


def first_entity_claims(entity: dict[str, Any], property_id: str) -> list[str]:
    ids: list[str] = []
    for value in claim_datavalues(entity, property_id):
        if isinstance(value, dict) and value.get("id"):
            ids.append(value["id"])
    return ids


def first_coord(entity: dict[str, Any]) -> tuple[float, float] | tuple[None, None]:
    for value in claim_datavalues(entity, "P625"):
        if isinstance(value, dict) and "latitude" in value and "longitude" in value:
            return round(float(value["latitude"]), 6), round(float(value["longitude"]), 6)
    return None, None


def first_year(entity: dict[str, Any]) -> int | None:
    for value in claim_datavalues(entity, "P571"):
        if not isinstance(value, dict):
            continue
        raw = value.get("time", "")
        match = re.match(r"^[+-](\d{1,4})-", raw)
        if match:
            year = int(match.group(1))
            if 1000 <= year <= 2100:
                return year
    return None


def collect_admin_entities(museums: dict[str, Any]) -> dict[str, Any]:
    admin_entities: dict[str, Any] = {}
    frontier: set[str] = set()
    for entity in museums.values():
        frontier.update(first_entity_claims(entity, "P131"))

    for _ in range(5):
        frontier -= set(admin_entities)
        if not frontier:
            break
        fetched = fetch_entities(sorted(frontier), props="labels|claims")
        admin_entities.update(fetched)
        next_frontier: set[str] = set()
        for entity in fetched.values():
            next_frontier.update(first_entity_claims(entity, "P131"))
        frontier = next_frontier
    return admin_entities


def admin_chain(entity: dict[str, Any], admin_entities: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    frontier = first_entity_claims(entity, "P131")
    for _ in range(6):
        next_frontier: list[str] = []
        for qid in frontier:
            if qid in seen:
                continue
            seen.add(qid)
            admin_entity = admin_entities.get(qid)
            if not admin_entity:
                continue
            label = localized_text(admin_entity.get("labels", {}), "zh", "zh-hans", "zh-cn", "en")
            if label:
                labels.append(simplify_chinese(label))
            next_frontier.extend(first_entity_claims(admin_entity, "P131"))
        frontier = next_frontier
        if not frontier:
            break
    return labels


def infer_province(labels: list[str], museum_name: str) -> str:
    joined = simplify_chinese(" ".join(labels + [museum_name]))
    for full_name, short_name in PROVINCE_NAMES.items():
        if full_name in joined:
            return short_name
    for alias, short_name in sorted(SHORT_PROVINCE_ALIASES.items(), key=lambda item: -len(item[0])):
        if simplify_chinese(alias) in joined:
            return short_name
    for city, city_province in CITY_PROVINCE_HINTS.items():
        if city in joined:
            return city_province
    return "中国"


def strip_city_suffix(label: str) -> str:
    for suffix in ["特别行政区", "自治州", "地区", "市", "盟", "州", "县", "区"]:
        if label.endswith(suffix) and len(label) > len(suffix):
            return label[: -len(suffix)]
    return label


def infer_city(labels: list[str], province: str, museum_name: str) -> str:
    if province in MUNICIPALITIES:
        return province
    joined = simplify_chinese(" ".join(labels + [museum_name]))
    for city, city_province in CITY_PROVINCE_HINTS.items():
        if city_province == province and city in joined:
            return city
    for label in labels:
        label = simplify_chinese(label)
        if label in PROVINCE_NAMES or SHORT_PROVINCE_ALIASES.get(label) == province:
            continue
        if label.endswith(("市", "自治州", "地区", "盟", "州")):
            return strip_city_suffix(label)
    for label in labels:
        if label.endswith(("县", "区")):
            return strip_city_suffix(label)
    return province


def infer_category(name: str, english_name: str, description: str | None) -> str:
    haystack = simplify_chinese(f"{name} {english_name} {description or ''}").lower()
    for category, keywords in CATEGORY_KEYWORDS:
        if any(keyword in haystack for keyword in keywords):
            return category
    return "综合"


def theme_for_category(category: str) -> str:
    return {
        "历史": "地方历史、考古发现与文物收藏",
        "艺术": "艺术收藏、展览策划与公共美育",
        "科技": "科学技术、互动体验与科普教育",
        "自然": "自然标本、生态环境与地质演化",
        "军事": "军事历史、装备文献与国防教育",
        "革命纪念": "革命历史、人物事迹与文献实物",
        "民俗": "民俗生活、非遗传承与地方文化",
        "专题": "专题收藏、主题研究与公共展示",
        "综合": "地方文化、历史记忆与综合收藏",
    }[category]


def build_summary(name: str, province: str, city: str, category: str, description: str | None) -> str:
    location = province if province == city else f"{province}{city}"
    theme = theme_for_category(category)
    return f"{name}位于{location}，是一座以{theme}为主要内容的{category}类博物馆。馆内展陈通常围绕常设收藏、专题展览与公共教育展开，适合作为了解当地文化脉络的参观点。"


def slugify(text: str, fallback: str) -> str:
    slug = text.lower()
    slug = re.sub(r"&", " and ", slug)
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug:
        slug = fallback.lower()
    if not slug.endswith(("museum", "memorial", "gallery", "hall", "center", "centre", "park", "site")):
        slug += "_museum"
    return slug


def normalize_for_duplicate(text: str) -> str:
    text = simplify_chinese(text.lower())
    return re.sub(r"[\s·・,，。.'’‘\"“”()（）\-_/]", "", text)


def existing_museums(data_dir: Path) -> tuple[set[str], set[str], set[str]]:
    ids: set[str] = set()
    names: set[str] = set()
    english_names: set[str] = set()
    for info_path in data_dir.glob("*/info.json"):
        data = json.loads(info_path.read_text(encoding="utf-8"))
        ids.add(data["id"])
        names.add(normalize_for_duplicate(data.get("name", "")))
        english_names.add(normalize_for_duplicate(data.get("englishName", "")))
    return ids, names, english_names


def is_duplicate(name: str, english_name: str, existing_names: set[str], existing_english_names: set[str]) -> bool:
    normalized_name = normalize_for_duplicate(name)
    normalized_english = normalize_for_duplicate(english_name)
    if normalized_name in {normalize_for_duplicate(value) for value in MANUAL_DUPLICATE_NAMES}:
        return True
    if normalized_name in existing_names or normalized_english in existing_english_names:
        return True
    # Catch common short aliases such as "故宫" vs "故宫博物院" without overfitting all museums.
    if len(normalized_name) >= 2:
        for existing in existing_names:
            if normalized_name in existing or existing in normalized_name:
                if "博物" in existing or "museum" in existing:
                    return True
    return False


def score_candidate(entity: dict[str, Any]) -> int:
    score = 0
    if "zhwiki" in entity.get("sitelinks", {}):
        score += 5
    if first_string_claim(entity, "P856"):
        score += 4
    lat, lon = first_coord(entity)
    if lat is not None and lon is not None:
        score += 4
    if first_string_claim(entity, "P6375"):
        score += 2
    if first_year(entity):
        score += 1
    if localized_text(entity.get("labels", {}), "en"):
        score += 1
    return score


def build_record(
    qid: str,
    entity: dict[str, Any],
    admin_entities: dict[str, Any],
    used_ids: set[str],
) -> dict[str, Any] | None:
    name = preferred_chinese_name(entity)
    english_name = localized_text(entity.get("labels", {}), "en")
    if not name or not english_name:
        return None
    if "研究所" in name and not is_museum_like_name(name):
        return None

    description = localized_text(entity.get("descriptions", {}), "zh", "zh-hans", "zh-cn")
    if description:
        description = simplify_chinese(description)
    labels = admin_chain(entity, admin_entities)
    province = infer_province(labels, name)
    city = infer_city(labels, province, name)
    category = infer_category(name, english_name, description)
    latitude, longitude = first_coord(entity)
    if latitude is None or longitude is None:
        return None
    if province == "中国":
        return None

    base_id = slugify(english_name, qid)
    museum_id = base_id
    if museum_id in used_ids:
        museum_id = f"{base_id}_{qid.lower()}"
    used_ids.add(museum_id)

    website = first_string_claim(entity, "P856")
    phone = first_string_claim(entity, "P1329")
    address = first_string_claim(entity, "P6375")
    if address:
        address = clean_name(address)
    if not address:
        location = province if province == city else f"{province}{city}"
        address = f"{location}（坐标定位，详细地址请查看官网）"

    return {
        "id": museum_id,
        "name": name,
        "englishName": english_name,
        "city": city,
        "province": province,
        "category": category,
        "founded": first_year(entity),
        "area": None,
        "annualVisitors": None,
        "freeEntry": False,
        "address": address,
        "website": website,
        "phone": phone,
        "openingHours": "请查看官网",
        "summary": build_summary(name, province, city, category, description),
        "highlights": HIGHLIGHTS_BY_CATEGORY[category],
        "images": [],
        "latitude": latitude,
        "longitude": longitude,
        "grade": None,
    }


def main() -> int:
    args = parse_args()
    qids = query_museum_qids(args.query_limit)
    entities = fetch_entities(qids)
    used_ids, existing_names, existing_english_names = existing_museums(args.data_dir)

    ordered_qids = sorted(qids, key=lambda qid: (-score_candidate(entities[qid]), qid))
    preselected_qids: list[str] = []
    preselected_count = max(args.limit * 3, 300)
    for qid in ordered_qids:
        entity = entities.get(qid)
        if not entity or entity.get("missing"):
            continue
        name = preferred_chinese_name(entity) or ""
        english_name = localized_text(entity.get("labels", {}), "en") or ""
        latitude, longitude = first_coord(entity)
        if latitude is None or longitude is None:
            continue
        if is_duplicate(name, english_name, existing_names, existing_english_names):
            continue
        preselected_qids.append(qid)
        if len(preselected_qids) >= preselected_count:
            break

    candidate_entities = {qid: entities[qid] for qid in preselected_qids}
    admin_entities = collect_admin_entities(candidate_entities)

    records: list[dict[str, Any]] = []
    for qid in preselected_qids:
        entity = entities.get(qid)
        if not entity or entity.get("missing"):
            continue
        name = preferred_chinese_name(entity) or ""
        english_name = localized_text(entity.get("labels", {}), "en") or ""
        if is_duplicate(name, english_name, existing_names, existing_english_names):
            continue
        record = build_record(qid, entity, admin_entities, used_ids)
        if not record:
            continue
        records.append(record)
        existing_names.add(normalize_for_duplicate(record["name"]))
        existing_english_names.add(normalize_for_duplicate(record["englishName"]))
        if len(records) >= args.limit:
            break

    if len(records) < args.limit:
        raise RuntimeError(f"Only found {len(records)} usable candidates; increase --query-limit.")

    if args.dry_run:
        for index, record in enumerate(records, start=1):
            website_mark = "官网" if record.get("website") else "无官网"
            print(f"{index:03d}. {record['id']} | {record['name']} | {record['province']} {record['city']} | {record['category']} | {website_mark}")
        return 0

    for record in records:
        museum_dir = args.data_dir / record["id"]
        museum_dir.mkdir(parents=True, exist_ok=False)
        info_path = museum_dir / "info.json"
        info_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Added {len(records)} museums to {args.data_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
