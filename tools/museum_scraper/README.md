# Museum Scraper

面向“全国博物馆素材沉淀”的通用采集工具。

目标：

- 从官方名录或自定义种子导入全国博物馆清单
- 自动发现候选官网
- 抓取博物馆简介、开放信息、场馆/展厅/分馆页面、馆藏/藏品/展览介绍页
- 下载页面中的介绍图片
- 按博物馆名称分类存储到本地目录

## 目录结构

```text
tools/museum_scraper/
├── museum_scraper/
│   ├── cli.py
│   ├── config.py
│   ├── crawler.py
│   ├── dataset.py
│   ├── fetching.py
│   ├── models.py
│   ├── official_sources.py
│   ├── parsing.py
│   ├── search.py
│   ├── seeds.py
│   ├── site_extractors.py
│   ├── storage.py
│   └── utils.py
├── seeds/
│   └── sample_museums.csv
├── tests/
│   └── test_parser_and_storage.py
└── requirements.txt
```

## 依赖

建议使用你现有的 venv：

```bash
PYTHON=/Users/chengyu/PycharmProjects/PythonProject/.venv/bin/python
ROOT=/Users/chengyu/project/Museum

$PYTHON -m pip install -r $ROOT/tools/museum_scraper/requirements.txt
```

## 快速开始

### 1. 先用样例种子验证

```bash
$PYTHON $ROOT/tools/museum_scraper/run.py \
  crawl \
  --seed-file $ROOT/tools/museum_scraper/seeds/sample_museums.csv \
  --output $ROOT/tools/museum_scraper/output \
  --search-provider bing \
  --max-museums 2 \
  --max-pages 20 \
  --max-depth 2
```

### 2. 导出国家文物局官方名录种子

国家文物局“全国博物馆名录查询”页面前置了验证码，脚本支持先把验证码图片取下来，再人工输入验证码后批量导出。

先拉验证码：

```bash
$PYTHON $ROOT/tools/museum_scraper/run.py \
  official-captcha \
  --output $ROOT/tools/museum_scraper/.cache/ncha_captcha.png
```

再导出名录：

```bash
$PYTHON $ROOT/tools/museum_scraper/run.py \
  official-export \
  --captcha YOUR_CODE \
  --output $ROOT/tools/museum_scraper/seeds/official_museums.jsonl
```

可以只导某个省：

```bash
$PYTHON $ROOT/tools/museum_scraper/run.py \
  official-export \
  --captcha YOUR_CODE \
  --province 北京市 \
  --output $ROOT/tools/museum_scraper/seeds/beijing_museums.jsonl
```

### 3. 跑单馆验证

```bash
$PYTHON $ROOT/tools/museum_scraper/run.py \
  crawl-one \
  --name 中国国家博物馆 \
  --province 北京市 \
  --official-site https://www.chnmuseum.cn/ \
  --output $ROOT/tools/museum_scraper/output \
  --max-pages 20 \
  --max-depth 2 \
  --ignore-robots
```

### 4. 按省拆分全国种子

```bash
$PYTHON $ROOT/tools/museum_scraper/run.py \
  seed-split \
  --seed-file $ROOT/tools/museum_scraper/seeds/official_museums.jsonl \
  --output-dir $ROOT/tools/museum_scraper/.cache/split_seeds
```

### 5. 按省分批跑，并支持断点续跑

```bash
$PYTHON $ROOT/tools/museum_scraper/run.py \
  crawl-batch \
  --seed-file $ROOT/tools/museum_scraper/seeds/official_museums.jsonl \
  --output $ROOT/tools/museum_scraper/output \
  --max-pages 40 \
  --max-depth 2 \
  --resume
```

只跑一个省：

```bash
$PYTHON $ROOT/tools/museum_scraper/run.py \
  crawl-batch \
  --seed-file $ROOT/tools/museum_scraper/seeds/official_museums.jsonl \
  --output $ROOT/tools/museum_scraper/output \
  --province 北京市 \
  --max-pages 40 \
  --max-depth 2 \
  --resume
```

### 6. 生成后续 App 可直接消费的标准数据集

```bash
$PYTHON $ROOT/tools/museum_scraper/run.py \
  dataset-build \
  --input $ROOT/tools/museum_scraper/output \
  --output $ROOT/tools/museum_scraper/.cache/dataset
```

### 7. 审计字段完整度，定位需要补规则的馆站

```bash
$PYTHON $ROOT/tools/museum_scraper/run.py \
  crawl-audit \
  --input $ROOT/tools/museum_scraper/output \
  --output $ROOT/tools/museum_scraper/.cache/audit.json
```

## 输出结构

每个博物馆一个目录，例如：

```text
output/
└── 中国国家博物馆/
    ├── museum.json
    ├── crawl_report.json
    ├── pages/
    │   ├── overview/
    │   ├── venue/
    │   ├── collection/
    │   ├── exhibition/
    │   └── visit/
    └── images/
        ├── overview/
        ├── venue/
        ├── collection/
        └── exhibition/
```

其中：

- `museum.json`：种子与官网发现结果
- `crawl_report.json`：本次采集报告
- `pages/*/*.json`：页面元数据、正文摘要、图片引用
- `pages/*/*.md`：便于人工检查的正文文本
- `images/*/*`：下载下来的图片素材

## 标准数据集输出

`dataset-build` 会生成：

- `museums.jsonl`：每家博物馆一条记录，包含名称、省份、站点、基础元数据、页面统计
- `museums.jsonl` 额外聚合了 `overview`、`address`、`phone`、`email`、`opening_hours`，便于 App 直接消费
- `pages.jsonl`：每个页面一条记录，包含标题、类型、摘要、正文、来源 URL、本地路径
- `images.jsonl`：每张图片一条记录，包含来源页、原图 URL、本地路径、大小、扩展名
- `dataset_summary.json`：整体统计
- `audit.json`：字段完整度审计报告，可用来挑出最该补定制规则的馆站

适合后续做：

- App 本地素材库初始化
- 向量化检索或 RAG
- 后台 CMS 导入
- 图片审核和人工二次筛选

## 推荐流程

1. `official-captcha` 拉验证码图
2. `official-export` 导出全国或单省名录
3. `crawl-batch --resume` 分批跑素材采集
4. `dataset-build` 导出标准化 JSONL 数据集
5. 对 `images.jsonl` 里的图片做人工筛选、去重和版权校验

## 重要说明

本仓库中的 `tools/museum_scraper/` 是 Museum 项目的正式维护位置。后续 Museum 采集任务请以这里为准。

1. 这是“素材采集框架”，不是只针对某一个馆站写死的脚本。
2. 全国博物馆官网差异很大，真正大规模跑时需要持续补充域名白名单、页面规则和反爬兼容。
3. 脚本默认开启 `robots.txt` 检查、限速、同站点爬取，不做无边界全网横跳。
   如果某些官网把首页也写进了拒爬规则，但你确认有权采集素材，可显式加 `--ignore-robots`。
4. 国家文物局官方名录目前可作为“全国种子来源”；更细的藏品图片通常仍需回到各馆官网抓取。
5. 跑大批量采集前，建议先按省份分批跑，观察失败率和站点兼容性。
6. `--resume` 依赖每个博物馆目录里的 `crawl_report.json`，适合长时间跑批中断后继续。
7. `dataset-build` 是“标准化汇总层”，便于你后续直接做博物馆介绍 App，而不是再从散文件里重新拼数据。
8. 当前已内置一层“站点定制提取器”机制，适合持续给头部馆站补精细规则；当前已适配 `chnmuseum.cn` 与 `dpm.org.cn`。
9. 对大型综合站点，建议把 `--max-pages` 提到 `5-8`，这样更容易同时拿到 `简介 / 导览 / 联系方式 / 服务总页`。
