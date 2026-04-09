# Museum App — 概要设计文档

> 本文档供开发者接手开发使用，请完整阅读后再开始编码。

## 一、项目概述

**项目名称**：Museum（中国博物馆）
**目标平台**：iOS 17.0+
**开发语言**：Swift 5.9 / SwiftUI
**目标**：上架 Apple App Store 的中国博物馆导览 App，涵盖全国 63 家主要博物馆的图文介绍

---

## 二、功能模块

### 2.1 核心功能

| 模块 | 功能描述 |
|------|----------|
| 博物馆列表 | 展示全部博物馆，支持关键词搜索（名称/城市/简介） |
| 博物馆详情 | 图片画廊、基本信息、中文简介、镇馆之宝、导航按钮 |
| 地图视图 | MapKit 地图标注所有有坐标的博物馆，点击弹出详情 |
| 筛选功能 | 按分类（9种）和省份（32个）双维度筛选 |
| 收藏功能 | 本地持久化收藏，用 `@AppStorage` 存储 ID 列表 |

### 2.2 数据集

- **63 家**博物馆，覆盖全国 **32 个**省市自治区（含港澳台）
- 每家博物馆：`info.json` + `images/` 目录
- 总图片：**432 张**，54 家达到 3 张以上，26 家达到 10 张
- 图片来源：Wikimedia Commons，CC BY-SA 授权，商业合规

---

## 三、技术架构

### 3.1 整体架构：MVVM

```
App 入口
└── ContentView（TabView）
    ├── MuseumListView          # 列表页
    │   ├── FilterView          # 筛选面板（Sheet）
    │   └── MuseumDetailView    # 详情页（NavigationStack）
    │       └── ImageGalleryView / FullGalleryView
    ├── MapView                 # 地图页（MapKit）
    └── FavoritesView           # 收藏页
```

**状态管理**：`MuseumStore`（`@MainActor ObservableObject`）集中管理所有数据和筛选状态，通过 `.environmentObject` 注入各视图。

### 3.2 数据层

**数据模型**（`Museum/Models/Museum.swift`）：

```swift
struct Museum: Identifiable, Codable, Hashable {
    let id: String               // 目录名，如 "palace_museum"
    let name: String             // 中文名
    let englishName: String
    let city: String
    let province: String
    let category: MuseumCategory // 枚举：历史/艺术/科技/自然/军事/革命纪念/民俗/专题/综合
    let grade: MuseumGrade?      // 枚举：国家一/二/三级博物馆
    let latitude: Double?
    let longitude: Double?
    let images: [MuseumImage]    // 图片元数据列表
    let summary: String
    let highlights: [String]     // 镇馆之宝
    let founded: Int?
    let area: Double?            // 建筑面积（平方米）
    let annualVisitors: Int?
    let freeEntry: Bool
    let address: String
    let website: String?
    let phone: String?
    let openingHours: String
}
```

**数据加载**（`Museum/Models/MuseumDataLoader.swift`）：
- 从 App Bundle 的 `MuseumData/` 目录递归读取每个博物馆的 `info.json`
- 图片通过 `imageURL(museumID:filename:)` 拼接本地路径，供 `AsyncImage` 加载
- Fallback：Bundle 找不到时从 Documents 目录读取（方便远程更新）

**筛选逻辑**（`Museum/Models/MuseumStore.swift`）：

```swift
var filteredMuseums: [Museum] {
    museums.filter { museum in
        let matchesSearch = searchText.isEmpty ||
            museum.name.contains(searchText) ||
            museum.city.contains(searchText) ||
            museum.summary.contains(searchText)
        let matchesCategory = selectedCategory == nil || museum.category == selectedCategory
        let matchesProvince = selectedProvince == nil || museum.province == selectedProvince
        return matchesSearch && matchesCategory && matchesProvince
    }
}
```

### 3.3 视图层关键实现

**图片画廊**（`Museum/Views/ImageGalleryView.swift`）：
- `TabView` + `.tabViewStyle(.page)` 实现左右滑动翻页
- 自定义圆点指示器，底部渐变遮罩显示说明文字
- 支持点击进入全屏画廊（`FullGalleryView`，`.fullScreenCover` 呈现）

**地图视图**（`Museum/Views/MapView.swift`）：
- 使用 iOS 17 新 API `Map(position:selection:)` + `Annotation`
- 点击标注弹出 `.presentationDetents([.medium, .large])` 的详情 Sheet

**收藏持久化**（`Museum/Views/FavoritesView.swift`）：
- `@AppStorage("favoriteMuseumIDs")` 存储 JSON 编码的 `[String]`，无需 CoreData

---

## 四、项目文件结构

```
Museum/
├── project.yml                        # XcodeGen 配置，运行 `xcodegen` 生成 .xcodeproj
├── DESIGN.md                          # 本文档
├── Museum/
│   ├── App/
│   │   └── MuseumApp.swift            # @main 入口
│   ├── Models/
│   │   ├── Museum.swift               # 数据模型（Museum / MuseumImage / 枚举）
│   │   ├── MuseumStore.swift          # ObservableObject，全局状态与筛选逻辑
│   │   └── MuseumDataLoader.swift     # 从 Bundle/Documents 加载 JSON 和图片路径
│   ├── Views/
│   │   ├── ContentView.swift          # TabView 根视图
│   │   ├── MuseumListView.swift       # 列表 + 搜索栏 + 行视图 + 分类徽章
│   │   ├── MuseumDetailView.swift     # 详情页（画廊 + 信息卡 + 简介 + 亮点）
│   │   ├── ImageGalleryView.swift     # 图片画廊（翻页 + 全屏）
│   │   ├── FilterView.swift           # 筛选 Sheet（类别 + 省份）
│   │   ├── MapView.swift              # 地图标注页
│   │   └── FavoritesView.swift        # 收藏列表页
│   ├── Resources/
│   │   └── Assets.xcassets/           # AppIcon（待填充）、AccentColor
│   └── Info.plist
└── MuseumData/                        # 63 家博物馆数据（已就绪）
    ├── palace_museum/
    │   ├── info.json
    │   └── images/（01.jpg ~ 10.jpg）
    ├── shanghai_museum/
    └── ...（共 63 个目录）
```

---

## 五、数据格式说明

### info.json 完整结构

```json
{
  "id": "palace_museum",
  "name": "故宫博物院",
  "englishName": "",
  "city": "北京",
  "province": "北京",
  "category": "综合",
  "founded": null,
  "area": null,
  "annualVisitors": null,
  "freeEntry": false,
  "address": "",
  "website": null,
  "phone": null,
  "openingHours": "请查看官网",
  "summary": "故宫博物院，又称北京故宫，是位于...",
  "highlights": [],
  "images": [
    {
      "filename": "01.jpg",
      "caption": "故宫博物院",
      "credit": "Zhang Zeduan",
      "license": "Public domain"
    }
  ],
  "latitude": 39.915556,
  "longitude": 116.390833,
  "grade": null
}
```

**注意**：当前自动爬取的数据中，`founded`、`area`、`annualVisitors`、`address`、`website`、`highlights`、`englishName`、`grade` 大多为空，需要人工补全（见第七节待开发任务）。

---

## 六、开发难点与注意事项

### 6.1 本地图片加载（重点）

`AsyncImage` 加载本地 `file://` URL 需要注意：

1. 在 Xcode 中，`MuseumData` 目录必须作为 **Folder Reference**（蓝色图标）加入 Bundle，而非 Group（黄色图标）。操作：将文件夹拖入 Xcode 时选择"Create folder references"。
2. Bundle 路径查找方式：
   ```swift
   Bundle.main.url(forResource: museumID, withExtension: nil, subdirectory: "MuseumData")
   ```
3. 拼接图片路径后直接传给 `AsyncImage(url:)`，SwiftUI 原生支持 `file://` URL。

### 6.2 数据加载性能

- 63 个 JSON 文件同步读取约耗时 100~300ms，须在 `Task {}` 中异步执行，避免阻塞主线程。
- 建议策略：优先加载前 20 家（按省份/知名度排序）先渲染，其余后台补充。
- `MuseumStore.load()` 目前是骨架实现，需补充异步逻辑。

### 6.3 地图坐标缺失处理

部分博物馆 `latitude/longitude` 为 `nil`，地图页必须过滤：

```swift
var museumsWithLocation: [Museum] {
    store.museums.filter { $0.latitude != nil && $0.longitude != nil }
}
```

### 6.4 图片体积问题

部分图片原始尺寸超过 5MB（如澳门博物馆 6.7MB），直接打包会导致 App 包体积过大。**打包前必须压缩**，建议运行提供的脚本将所有图片压缩至 ≤500KB、最长边 ≤1200px。

压缩命令（需安装 `sips`，macOS 自带）：
```bash
for f in MuseumData/*/images/*.jpg; do
  sips -Z 1200 "$f" --out "$f"
done
```

### 6.5 iOS 17 API 兼容性

- `Map(position:selection:)` 和 `Annotation` 是 iOS 17 新 API，低于 iOS 17 需替换为旧式写法
- `ContentUnavailableView` 同样是 iOS 17+，低版本需自定义空状态视图
- 建议保持 iOS 17.0+ 部署目标，当前市场占有率已足够

### 6.6 App Store 审核合规

- **图片版权**：所有图片来自 Wikimedia Commons CC BY-SA 授权，必须在 App 内"关于"页面注明图片来源
- **位置权限**：`NSLocationWhenInUseUsageDescription` 已在 Info.plist 配置
- **隐私说明**：App 不收集任何用户数据，需在 App Store Connect 的隐私问卷中如实填写

---

## 七、待开发任务清单（优先级排序）

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 生成 Xcode 项目 | 安装 `xcodegen`，在项目根目录运行 `xcodegen`，将 `MuseumData` 以 Folder Reference 方式加入 |
| P0 | 修复本地图片加载 | 验证 `MuseumDataLoader.imageURL()` 在真机/模拟器上正确返回路径 |
| P0 | 完善 `MuseumStore.load()` | 实现后台异步加载，加载期间显示 ProgressView |
| P1 | 图片批量压缩 | 将所有图片压缩至 ≤500KB，降低包体积 |
| P1 | 补全 TOP 20 博物馆数据 | 人工补全 `address`、`website`、`founded`、`highlights`、`englishName`、`grade` 字段 |
| P1 | 新增"关于"页面 | 包含：App 简介、图片版权声明（Wikimedia Commons CC BY-SA）、数据来源 |
| P2 | App Icon 设计 | 提供 1024×1024 图标，填充 `AppIcon.appiconset` |
| P2 | 收藏心形按钮 | 在详情页 NavigationBar 添加收藏/取消收藏按钮，与 FavoritesView 联动 |
| P2 | 暗黑模式适配 | 检查所有颜色使用 semantic color，避免硬编码 |
| P3 | 真机性能测试 | 重点测试列表滚动帧率、图片加载内存占用 |
| P3 | 本地化 | 考虑添加英文版本（英文名、英文简介字段已预留） |

---

## 八、启动项目步骤

```bash
# 1. 安装 XcodeGen
brew install xcodegen

# 2. 生成 Xcode 项目文件
cd ~/Museum
xcodegen

# 3. 打开 Xcode
open Museum.xcodeproj

# 4. 在 Xcode 中将 MuseumData 文件夹以 Folder Reference 方式加入项目
#    （拖入时选择 "Create folder references"，图标应为蓝色）

# 5. 选择模拟器，Command+R 运行
```

---

*文档版本：v1.0 | 生成日期：2026-04-08*
