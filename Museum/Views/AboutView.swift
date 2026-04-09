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
                    Text("\(store.museums.reduce(0) { $0 + $1.images.count }) 张")
                }
            }

            // 图片版权声明
            Section("图片版权声明") {
                VStack(alignment: .leading, spacing: 12) {
                    Label("图片来源", systemImage: "photo.on.rectangle")
                        .font(.subheadline.bold())
                    Text("本应用中所有博物馆图片均来自 Wikimedia Commons，遵循 CC BY-SA 授权协议。")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Divider()

                    Label("授权协议", systemImage: "doc.text")
                        .font(.subheadline.bold())
                    Text("图片采用 Creative Commons Attribution-ShareAlike (CC BY-SA) 许可协议，允许自由使用、修改和分发，但需注明原作者并以相同协议共享。")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Divider()

                    Label("署名要求", systemImage: "person.text.rectangle")
                        .font(.subheadline.bold())
                    Text("每张图片的摄影师和具体授权信息可在全屏查看模式下查看。使用图片时请遵守对应授权协议的署名要求。")
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
                    Text("博物馆地理坐标数据来自维基百科，用于地图标注展示。")
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

// MARK: - 开源许可列表

struct LicenseListView: View {
    var body: some View {
        List {
            Section("Wikimedia Commons") {
                VStack(alignment: .leading, spacing: 6) {
                    Text("CC BY-SA 4.0")
                        .font(.subheadline.bold())
                    Text("本作品可在署名相同许可协议下自由使用、修改和分发。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Link("查看完整协议", destination: URL(string: "https://creativecommons.org/licenses/by-sa/4.0/deed.zh")!)
                        .font(.caption)
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
                    Link("查看完整协议", destination: URL(string: "https://creativecommons.org/licenses/by-sa/3.0/deed.zh")!)
                        .font(.caption)
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