import SwiftUI

struct MuseumListView: View {
    @EnvironmentObject var store: MuseumStore
    @State private var showFilters = false

    var body: some View {
        NavigationStack {
            Group {
                if store.isLoading {
                    ProgressView("加载中...")
                } else {
                    List(store.filteredMuseums) { museum in
                        NavigationLink(value: museum) {
                            MuseumRowView(museum: museum)
                        }
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("中国博物馆")
            .navigationDestination(for: Museum.self) { museum in
                MuseumDetailView(museum: museum)
            }
            .searchable(text: $store.searchText, prompt: "搜索博物馆、城市、拼音...")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showFilters = true
                    } label: {
                        Image(systemName: "line.3.horizontal.decrease.circle")
                    }
                }
            }
            .sheet(isPresented: $showFilters) {
                FilterView()
            }
        }
    }
}

struct MuseumRowView: View {
    let museum: Museum

    var body: some View {
        HStack(spacing: 12) {
            MuseumThumbnailView(museum: museum)
                .frame(width: 72, height: 72)
                .clipShape(RoundedRectangle(cornerRadius: 8))

            VStack(alignment: .leading, spacing: 4) {
                Text(museum.name)
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
    }
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
    }

    var categoryColor: Color {
        switch category {
        case .history: return .brown
        case .art: return .purple
        case .science: return .blue
        case .natural: return .green
        case .military: return .red
        case .revolutionary: return .orange
        case .folk: return Color(red: 0.85, green: 0.65, blue: 0.13) // 深金色，暗黑模式可见
        case .specialty: return .cyan
        case .comprehensive: return .gray
        }
    }
}
