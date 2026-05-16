# Museum

中国博物馆 iOS App 项目，当前代码库同时承载 App 端资源与 Museum 专属的采集工具。

## 当前状态

- App 主体功能已接通：列表、搜索、分类/省份筛选、详情页、图片画廊、地图、收藏、百宝箱
- 当前仓库内的数据脚本校验可正常完成；本机 `xcodebuild` 校验暂受限于缺少 iOS Simulator runtime，卡在 `actool` 资源编译阶段
- 当前主导航已接入 4 个 Tab：博物馆、地图、收藏、更多
- `AboutView` 与 `TodoManagementView` 已通过 `TreasureBoxView` 接入主流程
- 已补齐 iPad 设备族、iPad 专用方向、启动屏与隐私清单等发布基础配置

## 数据现状

- `MuseumData/` 当前包含 63 家博物馆
- 磁盘图片与 `info.json` 图片元数据已经对齐，当前共 432 张本地图片
- `summary`、`englishName`、经纬度已全部补齐，地图页数据已完整
- `address`、`phone`、`website` 与 `founded` 已全部补齐
- `highlights` 已全部补齐，`category` 已从单一“综合”细分为历史、艺术、科技、自然、军事、民俗、专题、革命纪念与综合等类别
- 当前仍主要缺少人工整理字段：
  `annualVisitors`、`area`，以及少量不适用于国家等级体系或仍待确认的 `grade`
- 图片授权和署名元数据已纳入审计，发布前仍需补齐空缺项并压缩超大图片

## 待优先完善

1. 使用正式 Bundle ID、Apple Developer Team 与 Xcode 26 / iOS 26 SDK 做一次归档验证。
2. 补齐图片授权 / 署名空缺，并压缩超过 500KB 的图片，降低发布合规和包体积风险。
3. 补齐 `annualVisitors`、`area`，并复核剩余 `grade` 是否适用国家博物馆等级体系。
4. 为 `MuseumDataLoader`、筛选逻辑、收藏状态和图片路径补基础测试，当前仓库几乎没有 iOS 侧测试覆盖。
5. 为 iPad 做进一步产品化布局，例如用 `NavigationSplitView` 在大屏上展示列表 + 详情。
6. 评估是否继续保留 `TreasureBox` 中的待办功能，还是进一步产品化为“行程 / 观展清单”。
7. 如需继续扩充数据，统一使用本仓库下的 `tools/museum_scraper/`，不要再在 `PlayAndStudy` 中继续推进 Museum 采集任务。

## 辅助脚本

- `Scripts/audit_museum_data.py`：审计 `MuseumData` 的字段缺失、分类分布、图片一致性、授权/署名空缺和超大图片。
- `Scripts/enrich_museum_metadata.py`：从 Wikipedia / Wikidata 回填高置信字段，并包含人工确认过的 fallback；可用 `--manual-only` 只应用本地 fallback。
- `Scripts/sync_image_metadata.py`：把 `images/` 目录与 `info.json` 的图片条目自动对齐，可选清理 `Thumbs.db` / `.DS_Store`。

## 数据采集归位

`tools/museum_scraper/` 已在本仓库落地为 Museum 项目的正式采集入口。后续关于 Museum 的验证码导出、批量爬取、数据集构建、字段审计，都以这里为准。
