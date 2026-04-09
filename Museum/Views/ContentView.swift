import SwiftUI

struct ContentView: View {
    @EnvironmentObject var store: MuseumStore

    var body: some View {
        TabView {
            MuseumListView()
                .tabItem {
                    Label("博物馆", systemImage: "building.columns")
                }
            MapView()
                .tabItem {
                    Label("地图", systemImage: "map")
                }

            FavoritesView()
                .tabItem {
                    Label("收藏", systemImage: "heart")
                }

        }
        .onAppear { store.load() }
    }
}
