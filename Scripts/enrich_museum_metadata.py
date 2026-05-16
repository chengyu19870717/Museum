#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

WIKIPEDIA_API = "https://zh.wikipedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
HEADERS = {
    "User-Agent": "MuseumApp/1.0 (iOS museum guide; metadata enrichment; contact@example.com)"
}
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# Exact title overrides for entries that need traditional characters or renamed pages.
TITLE_OVERRIDES = {
    "hk_palace_museum": "香港故宮文化博物館",
    "macau_museum": "澳門博物館",
    "natural_history_bj": "国家自然博物馆",
    "npm_southern": "國立故宮博物院南部院區",
}

# Manual fallbacks for entries that are poorly covered by Wikipedia but can be
# confirmed from public museum pages / directory pages.
MANUAL_FALLBACKS: dict[str, dict[str, Any]] = {
    "anhui_museum": {
        "address": "安徽省合肥市怀宁路87号",
        "phone": "0551-63736658",
    },
    "aviation_museum": {
        "address": "北京市昌平区小汤山镇大汤山村700号",
        "phone": "010-61784882",
    },
    "capital_museum": {
        "address": "北京市西城区复兴门外大街16号",
        "phone": "010-63370491",
    },
    "china_art_museum": {
        "address": "上海市浦东新区上南路205号",
        "phone": "400-921-9021",
    },
    "china_silk_museum": {
        "founded": 1992,
        "address": "浙江省杭州市西湖区玉皇山路73-1号",
        "phone": "0571-87035150",
    },
    "china_tea_museum": {
        "address": "浙江省杭州市龙井路88号（双峰馆区）；浙江省杭州市翁家山268号（龙井馆区）",
        "phone": "0571-87964221",
    },
    "chongqing_museum": {
        "address": "重庆市渝中区人民路236号",
        "phone": "023-63679066",
    },
    "dunhuang_museum": {
        # 莫高窟以敦煌研究院官网作为官方信息入口，始建年份按首窟开凿的常用纪年处理。
        "founded": 366,
        "address": "甘肃省酒泉市敦煌市217省道",
        "website": "https://www.dha.ac.cn/",
        "phone": "400-997-1608",
    },
    "fujian_museum": {
        "address": "福建省福州市鼓楼区湖头街96号",
        "website": "https://museum.fjsen.com/",
        "phone": "0591-83757670",
    },
    "gansu_museum": {
        "address": "甘肃省兰州市七里河区西津西路3号",
        "phone": "0931-2339131",
    },
    "guangdong_museum": {
        "address": "广东省广州市天河区珠江新城珠江东路2号",
        "phone": "020-38046886",
    },
    "guangxi_museum": {
        "address": "广西壮族自治区南宁市青秀区民族大道34号",
        "phone": "0771-2707027",
        "website": "https://www.gxmuseum.cn/",
    },
    "guangzhou_museum": {
        "founded": 1929,
        "address": "广东省广州市越秀区越秀公园内镇海楼",
        "website": "https://www.guangzhoumuseum.cn/",
        "phone": "020-83550627",
    },
    "guizhou_museum": {
        "founded": 1953,
        "address": "贵州省贵阳市观山湖区林城东路107号",
        "phone": "0851-84811809",
    },
    "hainan_museum": {
        "address": "海南省海口市琼山区国兴大道76号",
        "phone": "0898-65238891",
    },
    "han_yangling": {
        "founded": 1999,
        "address": "陕西省西安经济技术开发区泾河工业园机场路东段",
        "website": "http://www.hylae.com/",
        "phone": "029-62657569",
    },
    "hebei_museum": {
        "address": "河北省石家庄市长安区东大街4号",
        "phone": "0311-966518",
    },
    "heilongjiang_museum": {
        "founded": 1904,
        "address": "黑龙江省哈尔滨市南岗区红军街50号",
        "phone": "0451-53644151",
    },
    "henan_museum": {
        "address": "河南省郑州市金水区农业路8号",
        "phone": "0371-65393166",
    },
    "hk_history_museum": {
        "address": "香港九龙尖沙咀漆咸道南100号",
        "phone": "+852 2724 9042",
    },
    "hk_palace_museum": {
        "address": "香港九龙西九文化区博物馆道8号",
        "phone": "+852 2200 0217",
    },
    "hubei_museum": {
        "address": "湖北省武汉市武昌区东湖路160号",
        "phone": "027-86790329",
    },
    "hunan_museum": {
        "address": "湖南省长沙市开福区东风路50号",
        "phone": "0731-84415833",
    },
    "jiangxi_museum": {
        "founded": 1953,
        "address": "江西省南昌市红谷滩区赣江北大道698号",
        "website": "https://www.jxmuseum.cn/",
        "phone": "0791-88233369",
    },
    "jingdezhen_museum": {
        "englishName": "Jingdezhen China Ceramics Museum",
        "founded": 1954,
        "address": "江西省景德镇市昌江区紫晶北路1号",
        "website": "https://www.jdzcct.com/",
        "phone": "0798-8253701",
        "summary": "景德镇中国陶瓷博物馆前身为景德镇陶瓷馆，创建于1954年，是中国较早成立的陶瓷专题博物馆之一。现馆位于江西省景德镇市昌江区紫晶北路1号，常设陈列系统展示景德镇陶瓷发展脉络与代表性藏品。",
        # Public OSM museum point for the named museum.
        "latitude": 29.2957790,
        "longitude": 117.1701087,
    },
    "jilin_museum": {
        "address": "吉林省长春市南关区永顺路1666号",
        "phone": "0431-88917353",
    },
    "jinsha_museum": {
        "founded": 2007,
        "address": "四川省成都市青羊区金沙遗址路2号",
        "website": "https://www.jinshasitemuseum.com/",
        "phone": "028-87303522",
    },
    "liangzhu_museum": {
        "founded": 1994,
        "address": "浙江省杭州市余杭区良渚街道美丽洲路1号",
        "phone": "0571-88773875",
    },
    "liaoning_museum": {
        "address": "辽宁省沈阳市浑南区智慧三街157号",
        "phone": "024-22741193",
    },
    "linzi_museum": {
        "founded": 1958,
        "address": "山东省淄博市张店区商场西路153号",
        "website": "http://www.zbsbwg.cn",
        "phone": "0533-2287817",
    },
    "macau_museum": {
        "address": "澳门博物馆前地112号",
        "phone": "+853 2835 7911",
    },
    "military_museum": {
        "address": "北京市海淀区复兴路9号",
        "phone": "010-66866244",
    },
    "nanjing_city_museum": {
        # 南京市博物馆现位于朝天宫古建筑群内，使用朝天宫坐标作为馆址坐标。
        "address": "江苏省南京市秦淮区王府大街朝天宫4号",
        "website": "http://www.njmm.cn/",
        "phone": "025-84466460",
        "latitude": 32.0370394,
        "longitude": 118.77040386,
    },
    "nanjing_massacre": {
        "address": "江苏省南京市建邺区水西门大街418号",
        "phone": "025-86612230",
        "website": "https://www.19371213.com.cn/",
    },
    "nanjing_museum": {
        "address": "江苏省南京市玄武区中山东路321号",
        "phone": "025-84807923",
    },
    "nanyue_museum": {
        # 2021 年两馆整合后启用“南越王博物院”名称。
        "founded": 2021,
        "address": "广东省广州市越秀区解放北路867号（王墓展区）；广东省广州市越秀区中山四路316号（王宫展区）",
        "phone": "020-36182920；020-83896501",
    },
    "national_museum_cn": {
        "address": "北京市东城区东长安街16号",
        "phone": "010-65116400",
    },
    "natural_history_bj": {
        "address": "北京市东城区天桥南大街126号",
        "phone": "010-67027702",
        "website": "https://www.nnhm.org.cn/",
    },
    "ningxia_museum": {
        "address": "宁夏回族自治区银川市金凤区人民广场东街6号",
        "phone": "0951-5085093",
    },
    "npm_southern": {
        "address": "台湾嘉义县太保市故宫大道888号",
        "phone": "+886-5-362-0777",
    },
    "npm_taipei": {
        "address": "台湾台北市士林区至善路二段221号",
        "phone": "+886-2-2881-2021",
    },
    "palace_museum": {
        "address": "北京市东城区景山前街4号",
        "phone": "400-950-1925",
    },
    "palace_museum_bj": {
        # 颐和园按 UNESCO 简介中的首次营建时间处理 founded 字段。
        "founded": 1750,
        "address": "北京市海淀区新建宫门路19号",
        "phone": "010-62881144",
    },
    "powerstation_art": {
        "address": "上海市黄浦区苗江路678号",
        "phone": "021-31108550",
    },
    "sanxingdui_museum": {
        "address": "四川省广汉市三星堆镇西安路133号",
        "phone": "0838-5533333",
    },
    "science_museum_bj": {
        "address": "北京市朝阳区北辰东路5号",
        "phone": "010-59041000",
    },
    "shaanxi_history": {
        "address": "陕西省西安市雁塔区小寨东路91号",
        "phone": "029-85253806",
    },
    "shandong_museum": {
        "address": "山东省济南市历下区经十路11899号",
        "phone": "0531-85058201",
    },
    "shanghai_history": {
        "address": "上海市黄浦区南京西路325号",
        "phone": "021-23299999",
    },
    "shanghai_museum": {
        "address": "上海市黄浦区人民大道201号",
        "phone": "021-63723500",
    },
    "shanghai_natural": {
        "address": "上海市静安区北京西路510号",
        "phone": "021-68622000",
    },
    "shanghai_science": {
        "address": "上海市浦东新区世纪大道2000号",
        "phone": "021-68622000",
    },
    "shanxi_museum": {
        "address": "山西省太原市滨河西路北段13号",
        "phone": "0351-8789188",
    },
    "sichuan_museum": {
        "address": "四川省成都市青羊区浣花南路251号",
        "phone": "028-65521888",
    },
    "suzhou_museum": {
        "address": "江苏省苏州市姑苏区东北街204号",
        "phone": "0512-67575666",
    },
    "terracotta_army": {
        # 按 1975 年国务院决定在遗址上建立博物馆的时间处理 founded 字段。
        "founded": 1975,
        "address": "陕西省西安市临潼区秦陵北路",
        "website": "https://www.bmy.com.cn/",
        "phone": "029-81399127",
    },
    "tibet_museum": {
        "address": "西藏自治区拉萨市城关区罗布林卡路19号",
        "phone": "0891-6835244",
    },
    "xian_museum": {
        "founded": 2007,
        "address": "陕西省西安市碑林区友谊西路72号",
        "website": "https://www.xabwy.com/",
        "phone": "18066819253",
    },
    "xinjiang_museum": {
        "address": "新疆乌鲁木齐市沙依巴克区西北路581号",
        "website": "http://www.xjmuseum.com.cn",
        "phone": "0991-4533451",
    },
    "yunnan_ethnic": {
        "founded": 1995,
        "address": "云南省昆明市西山区滇池路1503号",
        "website": "https://www.ynnmuseum.com/",
        "phone": "0871-64311385",
    },
    "yunnan_museum": {
        "address": "云南省昆明市官渡区广福路6393号",
        "phone": "0871-67286223",
    },
    "zhejiang_museum": {
        "address": "浙江省杭州市西湖区孤山路25号",
        "phone": "0571-87970017",
    },
}

MANUAL_CONTENT_FALLBACKS: dict[str, dict[str, Any]] = {
    "anhui_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["楚大鼎", "鄂君启金节", "吴王光剑"],
    },
    "aviation_museum": {
        "category": "军事",
        "grade": "国家一级博物馆",
        "highlights": ["毛主席座机", "歼-12轻型歼击机", "人民空军装备发展陈列"],
    },
    "capital_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["伯矩鬲", "古都北京历史文化陈列", "馆藏青铜器与佛教造像"],
    },
    "china_art_museum": {
        "category": "艺术",
        "highlights": ["近现代美术作品", "上海美术收藏与展览", "清明上河图数字艺术展示"],
    },
    "china_silk_museum": {
        "category": "专题",
        "grade": "国家一级博物馆",
        "highlights": ["中国丝绸史陈列", "丝绸之路主题展", "纺织品文物保护展示"],
    },
    "china_tea_museum": {
        "category": "专题",
        "grade": "国家一级博物馆",
        "highlights": ["中华茶文化展", "西湖龙井茶专题展", "茶具文物精品展示"],
    },
    "chongqing_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["三峡文物", "巴渝青铜器", "抗战大后方历史陈列"],
    },
    "dunhuang_museum": {
        "category": "历史",
        "highlights": ["莫高窟壁画", "敦煌彩塑艺术", "藏经洞文献"],
    },
    "fujian_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["福建古代文明陈列", "闽台历史文化", "馆藏陶瓷与书画"],
    },
    "gansu_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["铜奔马", "驿使图画像砖", "丝绸之路文明陈列"],
    },
    "guangdong_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["端砚", "潮州木雕", "广东历史文化陈列"],
    },
    "guangxi_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["铜鼓文化", "广西民族文物", "岭南历史文化陈列"],
    },
    "guangzhou_museum": {
        "category": "历史",
        "highlights": ["镇海楼", "广州城市历史陈列", "海上丝绸之路相关文物"],
    },
    "guizhou_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["贵州民族文物", "贵州古生物化石", "夜郎文化相关文物"],
    },
    "hainan_museum": {
        "highlights": ["海南历史陈列", "南海海洋文化", "黎族苗族民俗文物"],
    },
    "han_yangling": {
        "category": "历史",
        "grade": "国家一级博物馆",
        "highlights": ["汉景帝阳陵地下遗址", "裸体陶俑", "外藏坑遗址展示"],
    },
    "hebei_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["长信宫灯", "错金博山炉", "金缕玉衣"],
    },
    "heilongjiang_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["金代文物", "黑龙江自然与历史陈列", "东北抗联相关文物"],
    },
    "henan_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["莲鹤方壶", "贾湖骨笛", "妇好鸮尊"],
    },
    "hk_history_museum": {
        "category": "历史",
        "highlights": ["香港故事常设展", "考古与民俗藏品", "香港城市发展史料"],
    },
    "hk_palace_museum": {
        "category": "艺术",
        "highlights": ["故宫博物院借展文物", "清代宫廷艺术", "中国书画与器物展览"],
    },
    "hubei_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["曾侯乙编钟", "越王勾践剑", "郧县人头骨化石"],
    },
    "hunan_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["马王堆汉墓文物", "素纱单衣", "辛追夫人遗体"],
    },
    "jiangxi_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["商代伏鸟双尾青铜虎", "洪州窑瓷器", "江西革命文物"],
    },
    "jilin_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["高句丽文物", "吉林地方历史陈列", "东北民族民俗文物"],
    },
    "jingdezhen_museum": {
        "category": "专题",
        "grade": "国家一级博物馆",
        "highlights": ["元青花瓷器", "明清御窑瓷", "景德镇陶瓷发展陈列"],
    },
    "jinsha_museum": {
        "category": "历史",
        "grade": "国家一级博物馆",
        "highlights": ["太阳神鸟金饰", "金面具", "金沙遗址祭祀区"],
    },
    "liangzhu_museum": {
        "category": "历史",
        "grade": "国家一级博物馆",
        "highlights": ["玉琮王", "良渚古城遗址展示", "良渚玉器"],
    },
    "liaoning_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["唐摹王羲之一门书翰", "宋徽宗瑞鹤图", "辽代文物"],
    },
    "linzi_museum": {
        "category": "历史",
        "highlights": ["齐国故城文物", "临淄陶俑", "齐文化陈列"],
    },
    "macau_museum": {
        "category": "历史",
        "highlights": ["澳门历史城区文化", "中西交流史展品", "民俗与城市生活陈列"],
    },
    "military_museum": {
        "category": "军事",
        "grade": "国家一级博物馆",
        "highlights": ["人民军队武器装备", "革命战争史陈列", "功勋武器与军史文物"],
    },
    "nanjing_city_museum": {
        "category": "历史",
        "highlights": ["朝天宫古建筑群", "南京城市史文物", "六朝文化遗存"],
    },
    "nanjing_massacre": {
        "category": "革命纪念",
        "grade": "国家一级博物馆",
        "highlights": ["遇难者名单墙", "万人坑遗址", "抗战史料与证言"],
    },
    "nanjing_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["金兽", "银缕玉衣", "明清瓷器与书画"],
    },
    "nanyue_museum": {
        "category": "历史",
        "grade": "国家一级博物馆",
        "highlights": ["南越王墓原址", "丝缕玉衣", "文帝行玺金印"],
    },
    "national_museum_cn": {
        "grade": "国家一级博物馆",
        "highlights": ["后母戊鼎", "四羊方尊", "复兴之路基本陈列"],
    },
    "natural_history_bj": {
        "category": "自然",
        "grade": "国家一级博物馆",
        "highlights": ["黄河象化石", "恐龙化石", "生物演化陈列"],
    },
    "neimenggu_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["恐龙化石", "草原民族文物", "辽代与蒙古族历史陈列"],
    },
    "ningxia_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["西夏文物", "宁夏历史文化陈列", "回族民俗文物"],
    },
    "npm_southern": {
        "category": "艺术",
        "highlights": ["亚洲艺术文化展", "国立故宫文物南院展览", "书画器物多媒体展示"],
    },
    "npm_taipei": {
        "category": "艺术",
        "highlights": ["翠玉白菜", "肉形石", "毛公鼎"],
    },
    "palace_museum": {
        "category": "艺术",
        "grade": "国家一级博物馆",
        "highlights": ["清明上河图", "千里江山图", "明清宫廷建筑群"],
    },
    "palace_museum_bj": {
        "category": "历史",
        "highlights": ["长廊", "佛香阁", "十七孔桥"],
    },
    "powerstation_art": {
        "category": "艺术",
        "highlights": ["当代艺术展览", "上海双年展", "工业遗存改造空间"],
    },
    "sanxingdui_museum": {
        "category": "历史",
        "grade": "国家一级博物馆",
        "highlights": ["青铜大立人像", "青铜神树", "黄金面具"],
    },
    "science_museum_bj": {
        "category": "科技",
        "grade": "国家一级博物馆",
        "highlights": ["科学乐园", "华夏之光", "探索与发现展厅"],
    },
    "shaanxi_history": {
        "grade": "国家一级博物馆",
        "highlights": ["镶金兽首玛瑙杯", "唐代壁画", "何家村窖藏文物"],
    },
    "shandong_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["亚醜钺", "鲁国大玉璧", "山东历史文化陈列"],
    },
    "shanghai_history": {
        "category": "历史",
        "highlights": ["上海城市历史陈列", "近代上海文物", "海派城市生活展品"],
    },
    "shanghai_museum": {
        "category": "艺术",
        "grade": "国家一级博物馆",
        "highlights": ["大克鼎", "晋侯稣钟", "青铜器与书画收藏"],
    },
    "shanghai_natural": {
        "category": "自然",
        "grade": "国家一级博物馆",
        "highlights": ["马门溪龙化石", "生命长河陈列", "自然生态标本"],
    },
    "shanghai_science": {
        "category": "科技",
        "grade": "国家一级博物馆",
        "highlights": ["智慧之光", "机器人世界", "地壳探秘"],
    },
    "shanxi_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["鸟尊", "晋侯墓地文物", "山西古代文明陈列"],
    },
    "sichuan_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["张大千临摹敦煌壁画", "巴蜀青铜器", "四川汉代画像砖"],
    },
    "suzhou_museum": {
        "category": "艺术",
        "grade": "国家一级博物馆",
        "highlights": ["秘色瓷莲花碗", "真珠舍利宝幢", "贝聿铭建筑空间"],
    },
    "terracotta_army": {
        "category": "历史",
        "grade": "国家一级博物馆",
        "highlights": ["一号兵马俑坑", "铜车马", "秦始皇帝陵遗址"],
    },
    "tibet_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["西藏历史文化陈列", "唐卡与佛教造像", "藏族民俗文物"],
    },
    "xian_museum": {
        "category": "历史",
        "highlights": ["小雁塔", "长安佛教造像", "西安城市历史陈列"],
    },
    "xinjiang_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["五星出东方利中国护膊", "古代干尸陈列", "新疆历史文物展"],
    },
    "yunnan_ethnic": {
        "category": "民俗",
        "highlights": ["云南少数民族服饰", "民族节庆与生活器物", "民族建筑与工艺展示"],
    },
    "yunnan_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["牛虎铜案", "滇国青铜器", "云南历史文明陈列"],
    },
    "zhejiang_museum": {
        "grade": "国家一级博物馆",
        "highlights": ["良渚玉器", "越窑青瓷", "黄宾虹书画收藏"],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich MuseumData from Wikipedia and Wikidata.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "MuseumData",
        help="Path to MuseumData directory.",
    )
    parser.add_argument("--write", action="store_true", help="Persist resolved fields to info.json.")
    parser.add_argument(
        "--ids",
        nargs="*",
        help="Optional list of museum ids to limit processing to.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.2,
        help="Delay between network requests to avoid hammering APIs.",
    )
    parser.add_argument(
        "--manual-only",
        action="store_true",
        help="Only apply local manual fallbacks without querying Wikipedia or Wikidata.",
    )
    return parser.parse_args()


def api_get(base_url: str, params: dict[str, Any], *, sleep_seconds: float = 0.0) -> dict[str, Any]:
    params = dict(params)
    params["format"] = "json"
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=20, context=SSL_CONTEXT) as response:
        payload = json.loads(response.read())
    if sleep_seconds > 0:
        time.sleep(sleep_seconds)
    return payload


def normalize_text(value: str) -> str:
    return re.sub(r"[\W_]+", "", value).lower()


def direct_page_lookup(title: str, *, sleep_seconds: float) -> dict[str, Any] | None:
    payload = api_get(
        WIKIPEDIA_API,
        {
            "action": "query",
            "titles": title,
            "prop": "extracts|coordinates|langlinks|pageprops",
            "exintro": True,
            "explaintext": True,
            "redirects": True,
            "lllang": "en",
            "lllimit": 1,
        },
        sleep_seconds=sleep_seconds,
    )
    pages = payload.get("query", {}).get("pages", {})
    if not pages:
        return None
    return next(iter(pages.values()))


def search_titles(query: str, *, sleep_seconds: float) -> list[dict[str, Any]]:
    payload = api_get(
        WIKIPEDIA_API,
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 5,
        },
        sleep_seconds=sleep_seconds,
    )
    return payload.get("query", {}).get("search", [])


def score_search_hit(query: str, hit_title: str, museum_name: str) -> int:
    query_norm = normalize_text(query)
    title_norm = normalize_text(hit_title)
    museum_norm = normalize_text(museum_name)

    if not title_norm:
        return -1
    if title_norm == query_norm or title_norm == museum_norm:
        return 100
    if query_norm and query_norm in title_norm:
        return 90
    if museum_norm and museum_norm in title_norm:
        return 85
    if title_norm in query_norm or title_norm in museum_norm:
        return 80
    return 0


def resolve_page(museum_id: str, museum_name: str, *, sleep_seconds: float) -> tuple[dict[str, Any] | None, str]:
    candidates = [TITLE_OVERRIDES.get(museum_id), museum_name]
    seen: set[str] = set()

    for title in [candidate for candidate in candidates if candidate]:
        if title in seen:
            continue
        seen.add(title)
        page = direct_page_lookup(title, sleep_seconds=sleep_seconds)
        if page and page.get("pageprops", {}).get("wikibase_item"):
            return page, "direct"

    for query in [candidate for candidate in candidates if candidate]:
        hits = search_titles(query, sleep_seconds=sleep_seconds)
        scored_hits = sorted(
            hits,
            key=lambda hit: score_search_hit(query, hit.get("title", ""), museum_name),
            reverse=True,
        )
        for hit in scored_hits:
            score = score_search_hit(query, hit.get("title", ""), museum_name)
            if score < 85:
                continue
            page = direct_page_lookup(hit["title"], sleep_seconds=sleep_seconds)
            if page and page.get("pageprops", {}).get("wikibase_item"):
                return page, f"search:{score}"

    return None, "unresolved"


def fetch_entity(item_id: str, *, sleep_seconds: float) -> dict[str, Any] | None:
    payload = api_get(
        WIKIDATA_API,
        {
            "action": "wbgetentities",
            "ids": item_id,
            "props": "labels|claims",
            "languages": "zh|en",
        },
        sleep_seconds=sleep_seconds,
    )
    return payload.get("entities", {}).get(item_id)


def first_claim_value(entity: dict[str, Any], property_id: str) -> Any | None:
    claims = entity.get("claims", {}).get(property_id, [])
    for claim in claims:
        mainsnak = claim.get("mainsnak", {})
        datavalue = mainsnak.get("datavalue")
        if datavalue:
            return datavalue.get("value")
    return None


def parse_year(value: dict[str, Any] | None) -> int | None:
    if not value:
        return None
    time_value = value.get("time")
    if not time_value or len(time_value) < 5:
        return None
    try:
        return int(time_value[1:5])
    except ValueError:
        return None


def extract_address(value: dict[str, Any] | None) -> str | None:
    if not value:
        return None
    text = value.get("text", "").strip()
    language = value.get("language", "")
    if not text:
        return None
    # Prefer Chinese-script addresses for a Chinese-language app.
    if language.startswith("zh"):
        return text
    return None


def fallback_updates(info: dict[str, Any], manual_fallback: dict[str, Any]) -> dict[str, Any]:
    updated_fields: dict[str, Any] = {}
    for field, value in manual_fallback.items():
        current_value = info.get(field)
        if current_value is None or current_value == "" or current_value == []:
            updated_fields[field] = value
        elif field == "category" and current_value == "综合" and value != "综合":
            updated_fields[field] = value
    return updated_fields


def enrich_info(info_path: Path, *, sleep_seconds: float, write: bool, manual_only: bool) -> dict[str, Any]:
    info = json.loads(info_path.read_text(encoding="utf-8"))
    museum_id = info["id"]
    museum_name = info["name"]
    manual_fallback = {
        **MANUAL_FALLBACKS.get(museum_id, {}),
        **MANUAL_CONTENT_FALLBACKS.get(museum_id, {}),
    }

    if manual_only:
        updated_fields = fallback_updates(info, manual_fallback)
        if updated_fields and write:
            info.update(updated_fields)
            info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {
            "museum_id": museum_id,
            "museum_name": museum_name,
            "resolved": False,
            "resolution": "manual-only",
            "updated_fields": updated_fields,
        }

    page, resolution = resolve_page(museum_id, museum_name, sleep_seconds=sleep_seconds)
    if not page:
        updated_fields = fallback_updates(info, manual_fallback)
        if updated_fields and write:
            info.update(updated_fields)
            info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {
            "museum_id": museum_id,
            "museum_name": museum_name,
            "resolved": False,
            "resolution": resolution,
            "updated_fields": updated_fields,
        }

    item_id = page.get("pageprops", {}).get("wikibase_item")
    entity = fetch_entity(item_id, sleep_seconds=sleep_seconds) if item_id else None
    updated_fields: dict[str, Any] = {}

    if not info.get("summary"):
        summary = (page.get("extract") or "").strip()
        if summary:
            updated_fields["summary"] = summary

    if not info.get("englishName"):
        english_name = None
        langlinks = page.get("langlinks") or []
        if langlinks:
            english_name = langlinks[0].get("*")
        if not english_name and entity:
            english_name = entity.get("labels", {}).get("en", {}).get("value")
        if english_name:
            updated_fields["englishName"] = english_name

    if (info.get("latitude") is None or info.get("longitude") is None):
        latitude = None
        longitude = None
        coordinates = page.get("coordinates") or []
        if coordinates:
            latitude = coordinates[0].get("lat")
            longitude = coordinates[0].get("lon")
        if (latitude is None or longitude is None) and entity:
            coord_value = first_claim_value(entity, "P625")
            if coord_value:
                latitude = coord_value.get("latitude")
                longitude = coord_value.get("longitude")
        if latitude is not None and longitude is not None:
            updated_fields["latitude"] = latitude
            updated_fields["longitude"] = longitude

    if not info.get("website") and entity:
        website = first_claim_value(entity, "P856")
        if isinstance(website, str) and website.startswith("http"):
            updated_fields["website"] = website

    if info.get("founded") is None and entity:
        founded_year = parse_year(first_claim_value(entity, "P571"))
        if founded_year:
            updated_fields["founded"] = founded_year

    if not info.get("address") and entity:
        address = extract_address(first_claim_value(entity, "P6375"))
        if address:
            updated_fields["address"] = address

    if not info.get("phone") and entity:
        phone = first_claim_value(entity, "P1329")
        if isinstance(phone, str) and phone.strip():
            updated_fields["phone"] = phone.strip()

    updated_fields.update(
        {
            field: value
            for field, value in fallback_updates(info, manual_fallback).items()
            if field not in updated_fields
        }
    )

    if updated_fields and write:
        info.update(updated_fields)
        info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "museum_id": museum_id,
        "museum_name": museum_name,
        "resolved": True,
        "resolution": resolution,
        "resolved_title": page.get("title"),
        "wikidata_item": item_id,
        "updated_fields": updated_fields,
    }


def main() -> int:
    args = parse_args()
    report_rows: list[dict[str, Any]] = []
    updated_museums = 0
    updated_fields_total = 0
    selected_ids = set(args.ids or [])

    for info_path in sorted(args.data_dir.glob("*/info.json")):
        museum_id = info_path.parent.name
        if selected_ids and museum_id not in selected_ids:
            continue
        row = enrich_info(info_path, sleep_seconds=args.sleep, write=args.write, manual_only=args.manual_only)
        report_rows.append(row)
        field_count = len(row.get("updated_fields", {}))
        if field_count:
            updated_museums += 1
            updated_fields_total += field_count

    summary = {
        "write": args.write,
        "museum_count": len(report_rows),
        "resolved_count": sum(1 for row in report_rows if row.get("resolved")),
        "updated_museum_count": updated_museums,
        "updated_field_count": updated_fields_total,
        "rows": report_rows,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
