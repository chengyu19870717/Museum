import SwiftUI
import MapKit

struct MapView: View {
    @EnvironmentObject var store: MuseumStore
    @State private var selectedMuseum: Museum?

    var body: some View {
        NavigationStack {
            // Pre-filter: only pass geo-tagged museums to avoid per-update work inside ClusteredMapView
        ClusteredMapView(
            museums: store.filteredMuseums.filter { $0.latitude != nil && $0.longitude != nil },
            selectedMuseum: $selectedMuseum
        )
                .ignoresSafeArea(edges: .bottom)
                .navigationTitle("博物馆地图")
                .navigationBarTitleDisplayMode(.inline)
                .sheet(item: $selectedMuseum) { museum in
                    NavigationStack {
                        MuseumDetailView(museum: museum)
                    }
                    .presentationDetents([.medium, .large])
                }
        }
    }
}
