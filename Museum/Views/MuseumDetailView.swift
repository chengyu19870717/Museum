import SwiftUI
import UIKit

struct MuseumDetailView: View {
    let museum: Museum
    @EnvironmentObject var store: MuseumStore
    @State private var selectedImageIndex = 0
    @State private var showFullGallery = false

    var body: some View {
        let shareText = museum.shareText  // compute once; Museum fields are immutable
        return ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                DetailGalleryHeader(
                    museum: museum,
                    selectedIndex: $selectedImageIndex,
                    showFull: $showFullGallery
                )

                VStack(alignment: .leading, spacing: 20) {
                    // 标题区
                    VStack(alignment: .leading, spacing: 6) {
                        Text(museum.name)
                            .font(.title2.bold())
                        if !museum.englishName.isEmpty {
                            Text(museum.englishName)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                        HStack(spacing: 8) {
                            CategoryBadge(category: museum.category)
                            if let grade = museum.grade {
                                Text(grade.rawValue)
                                    .font(.caption2)
                                    .foregroundStyle(.orange)
                                    .accessibilityLabel(grade.rawValue)
                            }
                        }
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
                    InfoCardView(museum: museum)
                    Divider()

                    // 参观信息（地址/官网/电话合并，全部可点击）
                    ContactInfoSection(museum: museum)

                    // 简介
                    VStack(alignment: .leading, spacing: 8) {
                        Text("博物馆简介").font(.headline)
                        Text(museum.summary.isEmpty ? "暂无简介" : museum.summary)
                            .font(.body)
                            .lineSpacing(6)
                    }

                    // 镇馆之宝
                    if !museum.highlights.isEmpty {
                        Divider()
                        VStack(alignment: .leading, spacing: 10) {
                            Text("镇馆之宝 / 亮点").font(.headline)
                            ForEach(museum.highlights, id: \.self) { item in
                                Label(item, systemImage: "star.fill")
                                    .font(.body)
                                    .foregroundStyle(.primary)
                            }
                        }
                    }
                }
                .padding()
            }
        }
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                HStack(spacing: 4) {
                    ShareLink(item: shareText) {
                        Image(systemName: "square.and.arrow.up")
                    }
                    .accessibilityLabel("分享")

                    Button {
                        store.toggleVisited(museum.id)
                    } label: {
                        Image(systemName: store.isVisited(museum.id) ? "mappin.circle.fill" : "mappin.circle")
                            .foregroundStyle(store.isVisited(museum.id) ? .green : .gray)
                            .animation(.easeInOut(duration: 0.2), value: store.isVisited(museum.id))
                    }
                    .accessibilityLabel(store.isVisited(museum.id) ? "取消打卡" : "标记已打卡")

                    Button {
                        store.toggleFavorite(museum.id)
                    } label: {
                        Image(systemName: store.isFavorite(museum.id) ? "heart.fill" : "heart")
                            .foregroundStyle(store.isFavorite(museum.id) ? .red : .gray)
                            .animation(.easeInOut(duration: 0.2), value: store.isFavorite(museum.id))
                    }
                    .accessibilityLabel(store.isFavorite(museum.id) ? "取消收藏" : "添加收藏")
                }
            }
        }
        .fullScreenCover(isPresented: $showFullGallery) {
            FullGalleryView(museum: museum, initialIndex: selectedImageIndex)
        }
    }
}

private struct DetailGalleryHeader: View {
    let museum: Museum
    @Binding var selectedIndex: Int
    @Binding var showFull: Bool

    var body: some View {
        ImageGalleryView(
            museum: museum,
            selectedIndex: $selectedIndex,
            showFull: $showFull
        )
        .frame(maxWidth: .infinity)
        // Use layout width via GeometryReader to avoid deprecated UIScreen.main.bounds
        .modifier(GalleryHeightModifier())
        .clipped()
        .contentShape(Rectangle())
    }
}

private struct GalleryHeightModifier: ViewModifier {
    @State private var height: CGFloat = 260

    func body(content: Content) -> some View {
        content
            .frame(height: height)
            .background(
                GeometryReader { geo in
                    Color.clear.onAppear {
                        height = computeHeight(for: geo.size.width)
                    }
                    .onChange(of: geo.size.width) { _, w in
                        height = computeHeight(for: w)
                    }
                }
            )
    }

    private func computeHeight(for width: CGFloat) -> CGFloat {
        guard width > 0 else { return 260 }
        let usable = UIDevice.current.userInterfaceIdiom == .pad
            ? min(width * 0.75, 680)
            : width
        return max(220, usable * 0.75)
    }
}

// MARK: - Info Card (统计数字)

struct InfoCardView: View {
    let museum: Museum

    var body: some View {
        VStack(spacing: 12) {
            HStack(alignment: .top) {
                InfoItem(icon: "calendar", label: "建馆年份",
                         value: museum.founded.map { "\($0)年" } ?? "—")
                Spacer()
                InfoItem(icon: "square.3.layers.3d", label: "建筑面积",
                         value: museum.formattedArea ?? "—")
                Spacer()
                InfoItem(icon: "person.3", label: "年访客量",
                         value: museum.formattedVisitors ?? "—")
            }
            let websiteURL = museum.websiteURL
            if let hours = museum.meaningfulOpeningHours {
                HStack {
                    Image(systemName: "clock").foregroundStyle(.secondary)
                    Text(hours).font(.caption).foregroundStyle(.secondary)
                    Spacer()
                }
            } else if let url = websiteURL {
                HStack {
                    Image(systemName: "clock").foregroundStyle(.secondary)
                    Link("查看官网获取开放时间", destination: url).font(.caption)
                    Spacer()
                }
            }
        }
        .padding()
        .background(.quaternary)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

// MARK: - Contact Info Section (地址/官网/电话合并，均可点击)

struct ContactInfoSection: View {
    let museum: Museum

    var body: some View {
        let mapURL     = museum.mapURL
        let websiteURL = museum.websiteURL
        let phoneURL   = museum.phoneURL
        if !museum.address.isEmpty || websiteURL != nil || phoneURL != nil {
            VStack(alignment: .leading, spacing: 12) {
                Text("参观信息").font(.headline)

                if !museum.address.isEmpty {
                    ContactRow(icon: "location", label: "地址",
                               value: museum.address, url: mapURL)
                }
                if let url = websiteURL {
                    ContactRow(icon: "globe", label: "官网",
                               value: museum.website ?? url.absoluteString, url: url)
                }
                if let url = phoneURL {
                    ContactRow(icon: "phone", label: "电话",
                               value: museum.phone ?? "", url: url)
                }

                if let url = mapURL {
                    Link(destination: url) {
                        Label("在地图中导航", systemImage: "map")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .padding(.top, 4)
                    .accessibilityLabel("在地图中导航")
                }
            }
            Divider()
        }
    }
}

private struct ContactRow: View {
    let icon: String
    let label: String
    let value: String
    let url: URL?

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: icon)
                .foregroundStyle(.blue)
                .frame(width: 20)

            VStack(alignment: .leading, spacing: 2) {
                Text(label).font(.caption).foregroundStyle(.secondary)
                if let url {
                    Link(destination: url) {
                        Text(value)
                            .font(.subheadline)
                            .foregroundStyle(.blue)
                            .multilineTextAlignment(.leading)
                    }
                } else {
                    Text(value)
                        .font(.subheadline)
                        .textSelection(.enabled)
                }
            }

            Spacer()

            if url != nil {
                Image(systemName: "arrow.up.right")
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
                    .accessibilityHidden(true)
            }
        }
    }
}

// MARK: - Info Item

struct InfoItem: View {
    let icon: String
    let label: String
    let value: String

    var body: some View {
        VStack(spacing: 4) {
            Image(systemName: icon).font(.title3).foregroundStyle(.blue)
            Text(value).font(.subheadline.bold())
            Text(label).font(.caption2).foregroundStyle(.secondary)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(label)：\(value)")
    }
}

// MARK: - Museum model helpers (URL & share)

extension Museum {
    var websiteURL: URL? {
        guard let s = website, !s.isEmpty else { return nil }
        return URL(string: s)
    }

    var phoneURL: URL? {
        guard let raw = phone?.trimmingCharacters(in: .whitespacesAndNewlines),
              !raw.isEmpty else { return nil }
        for candidate in raw.components(separatedBy: Museum.phoneSeparators) {
            let cleaned = candidate.unicodeScalars
                .filter { Museum.phoneAllowed.contains($0) }.map(String.init).joined()
            if cleaned.filter(\.isNumber).count >= 5 {
                return URL(string: "tel://\(cleaned)")
            }
        }
        return nil
    }

    private static let phoneSeparators = CharacterSet(charactersIn: "；;,，、/\n")
    private static let phoneAllowed    = CharacterSet(charactersIn: "+0123456789")

    var mapURL: URL? {
        var components = URLComponents(string: "https://maps.apple.com/")
        if let lat = latitude, let lon = longitude {
            components?.queryItems = [
                URLQueryItem(name: "ll", value: "\(lat),\(lon)"),
                URLQueryItem(name: "q", value: name),
            ]
        } else if !address.isEmpty {
            components?.queryItems = [
                URLQueryItem(name: "q", value: "\(name) \(address)"),
            ]
        } else {
            return nil
        }
        return components?.url
    }

    var shareText: String {
        var parts = [name]
        if !englishName.isEmpty { parts.append(englishName) }
        parts.append("\(province) \(city)")
        if !address.isEmpty { parts.append(address) }
        if let w = website, !w.isEmpty { parts.append(w) }
        return parts.joined(separator: "\n")
    }
}
