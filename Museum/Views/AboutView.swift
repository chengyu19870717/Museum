import SwiftUI

struct AboutView: View {
    @EnvironmentObject var store: MuseumStore

    var body: some View {
        List {
            // App 信息
            Section {
                HStack {
                    Spacer()
                    VStack(spacing: 12) {
                        Image(systemName: "building.columns.fill")
                            .font(.system(size: 56))
                            .foregroundStyle(.blue)
                        Text("中国博物馆")
                            .font(.title2.bold())
                        Text("探索华夏文明，走进中国博物馆")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        Text("版本 1.0.0")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }
                    Spacer()
                }
                .padding(.vertical, 16)
            }

            // 统计数据
            Section("数据概览") {
                LabeledContent("博物馆数量") {
                    Text("\(store.museums.count) 家")
                }
                LabeledContent("覆盖省份") {
                    Text("\(store.provinces.count) 个")
                }
                LabeledContent("图片总数") {
                    Text("\(store.statsTotalImages) 张")
                }
            }

            // #4: progress bar + fraction for data completeness
            Section("数据完整度") {
                CompletenessRow(label: "英文名",   value: store.statsMuseumsWithEnglishName, total: store.museums.count)
                CompletenessRow(label: "地图坐标", value: store.statsMuseumsWithLocation,   total: store.museums.count)
                CompletenessRow(label: "官方网站", value: store.statsMuseumsWithWebsite,    total: store.museums.count)
                CompletenessRow(label: "馆址地址", value: store.statsMuseumsWithAddress,    total: store.museums.count)
                CompletenessRow(label: "建馆年份", value: store.statsMuseumsWithFounded,    total: store.museums.count)
                CompletenessRow(label: "图片授权", value: store.statsImagesWithLicense,     total: store.statsTotalImages)
                CompletenessRow(label: "图片署名", value: store.statsImagesWithCredit,      total: store.statsTotalImages)
            }

            // 图片版权声明
            Section("图片版权声明") {
                VStack(alignment: .leading, spacing: 12) {
                    Label("图片来源", systemImage: "photo.on.rectangle")
                        .font(.subheadline.bold())
                    Text("本应用中的博物馆图片主要来自 Wikimedia Commons。不同图片可能采用 CC BY、CC BY-SA、CC0、Public Domain 等不同授权，具体以每张图片的授权信息为准。")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Divider()

                    Label("授权协议", systemImage: "doc.text")
                        .font(.subheadline.bold())
                    Text("使用或再分发图片时，请分别遵守对应图片的授权条款；需要署名的图片应保留作者、来源与协议说明，ShareAlike 图片需以兼容协议共享。")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Divider()

                    Label("署名要求", systemImage: "person.text.rectangle")
                        .font(.subheadline.bold())
                    Text("每张图片的摄影师和具体授权信息可在全屏查看模式下查看。授权或署名为空的图片，需要在发布前继续补齐或替换。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 8)
            }

            // 数据来源
            Section("数据来源") {
                VStack(alignment: .leading, spacing: 8) {
                    Label("博物馆简介", systemImage: "text.book.closed")
                        .font(.subheadline.bold())
                    Text("博物馆简介内容来源于维基百科中文站点，遵循 CC BY-SA 3.0 协议。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 4)

                VStack(alignment: .leading, spacing: 8) {
                    Label("地理坐标", systemImage: "mappin.and.ellipse")
                        .font(.subheadline.bold())
                    Text("博物馆地理坐标主要来自维基百科与 Wikidata，用于地图标注展示。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 4)

                VStack(alignment: .leading, spacing: 8) {
                    Label("结构化字段", systemImage: "square.text.square")
                        .font(.subheadline.bold())
                    Text("英文名、官网、建馆年份等字段来自 Wikidata 与馆方公开信息整理。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 4)
            }

            // 隐私说明
            Section("隐私政策") {
                VStack(alignment: .leading, spacing: 8) {
                    Text("本应用不收集任何用户个人数据。收藏和待办数据仅存储在您的设备本地，不会上传至任何服务器。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text("地图功能仅在您主动使用时请求位置权限，用于显示附近博物馆。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 4)
            }

            // 开源许可
            Section {
                NavigationLink {
                    LicenseListView()
                } label: {
                    Label("开源许可", systemImage: "doc.richtext")
                }
            }
        }
        .navigationTitle("关于")
    }
}

// MARK: - #4: Data completeness row with progress bar

private struct CompletenessRow: View {
    let label: String
    let value: Int
    let total: Int

    var body: some View {
        LabeledContent(label) {
            HStack(spacing: 8) {
                ProgressView(value: total > 0 ? Double(value) / Double(total) : 0)
                    .frame(width: 80)
                    .tint(tint)
                Text("\(value)/\(total)")
                    .font(.subheadline.monospacedDigit())
                    .foregroundStyle(.secondary)
            }
        }
        .accessibilityLabel("\(label)：\(value) 家，共 \(total) 家")
    }

    private var tint: Color {
        guard total > 0 else { return .gray }
        let ratio = Double(value) / Double(total)
        if ratio >= 0.8 { return .green }
        if ratio >= 0.5 { return .orange }
        return .red
    }
}

// MARK: - 开源许可列表

struct LicenseListView: View {
    var body: some View {
        List {
            Section("Wikimedia Commons 图片授权") {
                VStack(alignment: .leading, spacing: 6) {
                    Text("逐图授权")
                        .font(.subheadline.bold())
                    Text("图片元数据中可能包含 CC BY、CC BY-SA、CC0、Public Domain 等授权类型；请以单张图片的 license 字段为准。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    if let url = URL(string: "https://commons.wikimedia.org/wiki/Commons:Licensing") {
                        Link("查看 Wikimedia Commons 授权说明", destination: url)
                            .font(.caption)
                    }
                }
                .padding(.vertical, 4)
            }

            Section("Creative Commons") {
                VStack(alignment: .leading, spacing: 6) {
                    Text("常见 CC 协议")
                        .font(.subheadline.bold())
                    Text("CC BY 需要署名；CC BY-SA 还要求相同方式共享；CC0 通常表示权利人放弃可放弃的版权权益。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    if let url = URL(string: "https://creativecommons.org/licenses/") {
                        Link("查看 Creative Commons 协议说明", destination: url)
                            .font(.caption)
                    }
                }
                .padding(.vertical, 4)
            }

            Section("Wikipedia") {
                VStack(alignment: .leading, spacing: 6) {
                    Text("CC BY-SA 3.0")
                        .font(.subheadline.bold())
                    Text("维基百科内容在署名相同许可协议下可自由使用和分发。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    if let url = URL(string: "https://creativecommons.org/licenses/by-sa/3.0/deed.zh") {
                        Link("查看完整协议", destination: url)
                            .font(.caption)
                    }
                }
                .padding(.vertical, 4)
            }

            Section("Apple Maps") {
                VStack(alignment: .leading, spacing: 6) {
                    Text("MapKit")
                        .font(.subheadline.bold())
                    Text("地图数据由 Apple 提供，遵循 Apple Maps 服务条款。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 4)
            }
        }
        .navigationTitle("开源许可")
        .navigationBarTitleDisplayMode(.inline)
    }
}
