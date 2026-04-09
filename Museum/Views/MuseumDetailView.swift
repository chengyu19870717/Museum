import SwiftUI

struct MuseumDetailView: View {
    let museum: Museum
    @EnvironmentObject var store: MuseumStore
    @State private var selectedImageIndex = 0
    @State private var showFullGallery = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                // 图片画廊
                ImageGalleryView(
                    museum: museum,
                    selectedIndex: $selectedImageIndex,
                    showFull: $showFullGallery
                )
                .frame(height: 280)

                VStack(alignment: .leading, spacing: 20) {
                    // 标题区
                    VStack(alignment: .leading, spacing: 6) {
                        Text(museum.name)
                            .font(.title2.bold())
                        Text(museum.englishName)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        HStack {
                            Label("\(museum.province) \(museum.city)", systemImage: "mappin")
                            Spacer()
                            if museum.freeEntry {
                                Label("免费开放", systemImage: "ticket.fill")
                                    .foregroundStyle(.green)
                            }
                        }
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    }

                    Divider()

                    // 基本信息卡片
                    InfoCardView(museum: museum)

                    Divider()

                    // 简介
                    VStack(alignment: .leading, spacing: 8) {
                        Text("博物馆简介")
                            .font(.headline)
                        Text(museum.summary)
                            .font(.body)
                            .lineSpacing(6)
                    }

                    // 镇馆之宝
                    if !museum.highlights.isEmpty {
                        Divider()
                        VStack(alignment: .leading, spacing: 10) {
                            Text("镇馆之宝 / 亮点")
                                .font(.headline)
                            ForEach(museum.highlights, id: \.self) { item in
                                Label(item, systemImage: "star.fill")
                                    .font(.body)
                                    .foregroundStyle(.primary)
                            }
                        }
                    }

                    // 导航按钮
                    Divider()
                    NavigationButtonsView(museum: museum)
                }
                .padding()
            }
        }
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    store.toggleFavorite(museum.id)
                } label: {
                    Image(systemName: store.isFavorite(museum.id) ? "heart.fill" : "heart")
                        .foregroundStyle(store.isFavorite(museum.id) ? .red : .gray)
                        .animation(.easeInOut(duration: 0.2), value: store.isFavorite(museum.id))
                }
            }
        }
        .fullScreenCover(isPresented: $showFullGallery) {
            FullGalleryView(museum: museum, initialIndex: selectedImageIndex)
        }
    }
}

struct InfoCardView: View {
    let museum: Museum

    var body: some View {
        VStack(spacing: 12) {
            HStack {
                InfoItem(icon: "calendar", label: "建馆年份",
                         value: museum.founded.map { "\($0)年" } ?? "—")
                Spacer()
                InfoItem(icon: "square.3.layers.3d", label: "建筑面积",
                         value: museum.area.map { "\(Int($0 / 10000))万㎡" } ?? "—")
                Spacer()
                InfoItem(icon: "person.3", label: "年访客量",
                         value: museum.annualVisitors.map { formatVisitors($0) } ?? "—")
            }
            if let hours = museum.openingHours.isEmpty ? nil : museum.openingHours {
                HStack {
                    Image(systemName: "clock")
                        .foregroundStyle(.secondary)
                    Text(hours)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Spacer()
                }
            }
        }
        .padding()
        .background(.quaternary)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    func formatVisitors(_ n: Int) -> String {
        if n >= 1_000_000 { return "\(n / 1_000_000)百万" }
        if n >= 10_000 { return "\(n / 10_000)万" }
        return "\(n)"
    }
}

struct InfoItem: View {
    let icon: String
    let label: String
    let value: String

    var body: some View {
        VStack(spacing: 4) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundStyle(.blue)
            Text(value)
                .font(.subheadline.bold())
            Text(label)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
    }
}

struct NavigationButtonsView: View {
    let museum: Museum

    var body: some View {
        HStack(spacing: 16) {
            if let urlStr = museum.website, let url = URL(string: urlStr) {
                Link(destination: url) {
                    Label("官方网站", systemImage: "globe")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
            }
            if let phone = museum.phone, let url = URL(string: "tel://\(phone)") {
                Link(destination: url) {
                    Label("电话预约", systemImage: "phone")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
            }
        }
    }
}
