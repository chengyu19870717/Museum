import SwiftUI

struct FavoritesView: View {
    @EnvironmentObject var store: MuseumStore
    @State private var searchText = ""

    // #5: delegate to MuseumStore — reuses pre-built searchBlob covering all fields
    var displayedMuseums: [Museum] {
        store.searchFavoriteMuseums(searchText)
    }

    var body: some View {
        // Compute once per render; avoids double O(n) compactMap
        let displayed = displayedMuseums
        NavigationStack {
            Group {
                if store.favoriteIDsCount == 0 {
                    ContentUnavailableView(
                        "暂无收藏",
                        systemImage: "heart",
                        description: Text("浏览博物馆时点击心形图标即可收藏")
                    )
                } else if displayed.isEmpty && !searchText.isEmpty {
                    ContentUnavailableView.search(text: searchText)
                } else {
                    List {
                        ForEach(displayed) { museum in
                            NavigationLink {
                                MuseumDetailView(museum: museum)
                            } label: {
                                MuseumRowView(museum: museum, isVisited: store.isVisited(museum.id))
                            }
                            .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                                Button(role: .destructive) {
                                    store.toggleFavorite(museum.id)
                                } label: {
                                    Label("取消收藏", systemImage: "heart.slash")
                                }
                            }
                        }
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("我的收藏")
            .searchable(text: $searchText, prompt: "搜索收藏")
        }
    }
}
