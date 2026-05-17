import SwiftUI

private struct MuseumRoute: Hashable {
    let id: String
}

struct MuseumListView: View {
    @EnvironmentObject var store: MuseumStore
    @State private var showFilters = false
    @State private var showAbout = false
    @State private var navigationPath: [MuseumRoute] = []
    /// iPad NavigationSplitView passes a binding; iPhone uses NavigationStack push
    var iPadSelectedMuseum: Binding<Museum?>?

    var body: some View {
        // On iPad the parent NavigationSplitView provides the container
        if iPadSelectedMuseum != nil {
            coreContent
        } else {
            NavigationStack(path: $navigationPath) {
                coreContent
                    .navigationDestination(for: MuseumRoute.self) { route in
                        if let museum = store.museum(by: route.id) {
                            MuseumDetailView(museum: museum)
                        } else {
                            ContentUnavailableView(
                                "博物馆不存在",
                                systemImage: "building.columns",
                                description: Text("这条记录可能已被更新，请返回列表后重试。")
                            )
                        }
                    }
            }
        }
    }

    @ViewBuilder
    private var coreContent: some View {
        Group {
            if store.isLoading {
                ProgressView("加载中...")
            } else if store.loadError {
                ContentUnavailableView(
                    "加载失败",
                    systemImage: "exclamationmark.triangle",
                    description: Text("无法读取博物馆数据，请重启 App 重试")
                )
            } else {
                listContent
            }
        }
        .navigationTitle("中国博物馆")
        .searchable(text: $store.searchText, prompt: "中文、城市、拼音首字母均可搜索")
        .imeSearchFix(text: $store.searchText)
        .navigationDestination(isPresented: $showAbout) { AboutView() }
        .toolbarBackground(Visibility.visible, for: ToolbarPlacement.navigationBar)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button { showAbout = true } label: {
                    Image(systemName: "info.circle")
                }
                .accessibilityLabel("关于")
            }
            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    showFilters = true
                } label: {
                    Image(systemName: store.activeFilterCount > 0
                          ? "line.3.horizontal.decrease.circle.fill"
                          : "line.3.horizontal.decrease.circle")
                    .foregroundStyle(store.activeFilterCount > 0 ? .blue : .primary)
                }
                .accessibilityLabel(store.activeFilterCount > 0
                    ? "筛选（已激活 \(store.activeFilterCount) 项）"
                    : "筛选")
                .overlay(alignment: .topTrailing) {
                    if store.activeFilterCount > 0 {
                        Text("\(store.activeFilterCount)")
                            .font(.caption2.bold())
                            .foregroundStyle(.white)
                            .padding(4)
                            .background(.red)
                            .clipShape(Circle())
                            .offset(x: 8, y: -8)
                            .accessibilityHidden(true)
                    }
                }
            }
        }
        .sheet(isPresented: $showFilters) {
            FilterView()
        }
    }

    private var listContent: some View {
        Group {
            if store.filteredMuseums.isEmpty && store.isFiltered {
                if store.debouncedSearchText.isEmpty {
                    ContentUnavailableView(
                        "无匹配博物馆",
                        systemImage: "building.columns",
                        description: Text("尝试调整筛选条件")
                    )
                } else {
                    ContentUnavailableView.search(text: store.debouncedSearchText)
                }
            } else {
                List(store.filteredMuseums) { museum in
                    let row = MuseumRowView(
                        museum: museum,
                        isVisited: store.isVisited(museum.id),
                        searchQuery: store.debouncedSearchText
                    )
                    if let binding = iPadSelectedMuseum {
                        // iPad: explicit selection updates the NavigationSplitView detail column.
                        Button {
                            binding.wrappedValue = museum
                        } label: {
                            row
                                .contentShape(Rectangle())
                        }
                        .buttonStyle(.plain)
                        .listRowBackground(
                            binding.wrappedValue?.id == museum.id
                                ? Color.accentColor.opacity(0.12)
                                : Color.clear
                        )
                    } else {
                        // Keep the navigation path lightweight; the detail reads the fresh model by id.
                        Button {
                            navigationPath.append(MuseumRoute(id: museum.id))
                        } label: {
                            row.contentShape(Rectangle())
                        }
                        .buttonStyle(.plain)
                    }
                }
                .listStyle(.plain)
                .overlay(alignment: .top) { resultsCountPill }
            }
        }
    }

    @ViewBuilder
    private var resultsCountPill: some View {
        if store.isFiltered {
            Text(store.filteredMuseums.isEmpty
                 ? "无结果"
                 : "共 \(store.filteredMuseums.count) 家")
                .font(.caption2.bold())
                .foregroundStyle(.secondary)
                .padding(.horizontal, 12)
                .padding(.vertical, 5)
                .background(.regularMaterial)
                .clipShape(Capsule())
                .padding(.top, 8)
                .transition(.opacity.combined(with: .scale))
                .animation(.easeInOut(duration: 0.2), value: store.filteredMuseums.count)
        }
    }
}

struct MuseumRowView: View {
    let museum: Museum
    var isVisited: Bool = false
    var searchQuery: String = ""

    var body: some View {
        HStack(spacing: 12) {
            MuseumThumbnailView(museum: museum)
                .frame(width: 72, height: 72)
                .clipShape(RoundedRectangle(cornerRadius: 8))
                .overlay(alignment: .bottomTrailing) {
                    if isVisited {
                        Image(systemName: "checkmark.circle.fill")
                            .symbolRenderingMode(.palette)
                            .foregroundStyle(.white, .green)
                            .font(.system(size: 16))
                            .offset(x: 4, y: 4)
                            .accessibilityHidden(true)
                    }
                }

            VStack(alignment: .leading, spacing: 4) {
                // #9: highlight matched characters in museum name
                highlightedText(museum.name, query: searchQuery)
                    .font(.headline)
                    .lineLimit(1)
                Text("\(museum.province) · \(museum.city)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                HStack(spacing: 6) {
                    CategoryBadge(category: museum.category)
                    if let grade = museum.grade {
                        Text(grade.rawValue)
                            .font(.caption2)
                            .foregroundStyle(.orange)
                    }
                }
                if museum.freeEntry {
                    Label("免费", systemImage: "ticket")
                        .font(.caption2)
                        .foregroundStyle(.green)
                }
            }
        }
        .padding(.vertical, 4)
        .accessibilityElement(children: .combine)
        .accessibilityLabel(accessibilityDescription)
    }

    private var accessibilityDescription: String {
        var parts = [museum.name, "\(museum.province)\(museum.city)", museum.category.rawValue]
        if let grade = museum.grade { parts.append(grade.rawValue) }
        if museum.freeEntry { parts.append("免费") }
        if isVisited { parts.append("已打卡") }
        return parts.joined(separator: "，")
    }
}

// MARK: - #9: Highlight matching substring in a Text

private func highlightedText(_ text: String, query: String) -> Text {
    guard !query.isEmpty,
          let range = text.range(of: query, options: .caseInsensitive)
    else { return Text(text) }
    let before = String(text[text.startIndex..<range.lowerBound])
    let match  = String(text[range])
    let after  = String(text[range.upperBound...])
    return Text(before) + Text(match).bold().foregroundColor(.accentColor) + Text(after)
}

struct CategoryBadge: View {
    let category: MuseumCategory

    var body: some View {
        Text(category.rawValue)
            .font(.caption2)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(categoryColor.opacity(0.15))
            .foregroundStyle(categoryColor)
            .clipShape(Capsule())
            .accessibilityLabel("\(category.rawValue)类")
    }

    var categoryColor: Color {
        switch category {
        case .history:       return .brown
        case .art:           return .purple
        case .science:       return .blue
        case .natural:       return .green
        case .military:      return .red
        case .revolutionary: return .orange
        case .folk:          return Color(red: 0.85, green: 0.65, blue: 0.13)
        case .specialty:     return .cyan
        case .comprehensive: return .gray
        }
    }
}
