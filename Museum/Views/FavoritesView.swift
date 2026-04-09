import SwiftUI

struct FavoritesView: View {
    @EnvironmentObject var store: MuseumStore

    var body: some View {
        NavigationStack {
            Group {
                if store.favoriteMuseums.isEmpty {
                    ContentUnavailableView(
                        "暂无收藏",
                        systemImage: "heart",
                        description: Text("浏览博物馆时点击心形图标即可收藏")
                    )
                } else {
                    List {
                        ForEach(store.favoriteMuseums) { museum in
                            NavigationLink(value: museum) {
                                MuseumRowView(museum: museum)
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
            .navigationDestination(for: Museum.self) { museum in
                MuseumDetailView(museum: museum)
            }
        }
    }
}