import SwiftUI

// MARK: - Top-level navigation destination for sidebar

private enum SidebarTab: String, CaseIterable, Identifiable {
    case list     = "博物馆"
    case map      = "地图"
    case favorites = "收藏"
    case more     = "更多"

    var id: String { rawValue }
    var icon: String {
        switch self {
        case .list:      return "building.columns"
        case .map:       return "map"
        case .favorites: return "heart"
        case .more:      return "square.grid.2x2"
        }
    }
}

struct ContentView: View {
    @EnvironmentObject var store: MuseumStore
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass

    var body: some View {
        if shouldUseIPadLayout {
            iPadLayout
        } else if #available(iOS 18, *) {
            iPhoneLayout18
        } else {
            iPhoneLayout
        }
    }

    private var shouldUseIPadLayout: Bool {
        UIDevice.current.userInterfaceIdiom == .pad && horizontalSizeClass == .regular
    }

    // MARK: - #6 iPad: NavigationSplitView with full sidebar

    @State private var selectedTab: SidebarTab? = .list
    @State private var selectedMuseum: Museum?

    private var iPadLayout: some View {
        NavigationSplitView {
            // Sidebar — selection binding requires Optional on iOS
            List(SidebarTab.allCases, id: \.self, selection: $selectedTab) { tab in
                Label(tab.rawValue, systemImage: tab.icon)
                    .tag(tab)
                    .badge(tab == .favorites ? store.favoriteIDsCount : 0)
            }
            .navigationTitle("中国博物馆")
            .listStyle(.sidebar)
        } content: {
            // Content column
            switch selectedTab ?? .list {
            case .list:      MuseumListView(iPadSelectedMuseum: $selectedMuseum)
            case .map:       MapView()
            case .favorites: FavoritesView()
            case .more:      TreasureBoxView()
            }
        } detail: {
            // Detail column (only used by list tab)
            if selectedTab == .list || selectedTab == nil {
                if let museum = selectedMuseum {
                    MuseumDetailView(museum: museum)
                } else {
                    ContentUnavailableView(
                        "选择一个博物馆",
                        systemImage: "building.columns",
                        description: Text("从列表中选择博物馆查看详情")
                    )
                }
            } else {
                ContentUnavailableView("请从左侧选择", systemImage: "sidebar.left")
            }
        }
        .task { store.load() }
    }

    // MARK: - iPhone: TabView (iOS 18+ new Tab API)

    @available(iOS 18, *)
    private var iPhoneLayout18: some View {
        TabView {
            Tab("博物馆", systemImage: "building.columns") {
                MuseumListView()
            }
            Tab("地图", systemImage: "map") {
                MapView()
            }
            Tab("收藏", systemImage: "heart") {
                FavoritesView()
            }
            .badge(store.favoriteIDsCount)
            Tab("更多", systemImage: "square.grid.2x2") {
                TreasureBoxView()
            }
        }
        .task { store.load() }
    }

    // MARK: - iPhone: TabView (iOS 17 fallback)

    private var iPhoneLayout: some View {
        TabView {
            MuseumListView()
                .tabItem { Label("博物馆", systemImage: "building.columns") }
            MapView()
                .tabItem { Label("地图", systemImage: "map") }
            FavoritesView()
                .tabItem { Label("收藏", systemImage: "heart") }
                .badge(store.favoriteIDsCount)
            TreasureBoxView()
                .tabItem { Label("更多", systemImage: "square.grid.2x2") }
        }
        .task { store.load() }
    }
}
