import SwiftUI
import MapKit

struct MapView: View {
    @EnvironmentObject var store: MuseumStore
    @State private var cameraPosition = MapCameraPosition.region(
        MKCoordinateRegion(
            center: CLLocationCoordinate2D(latitude: 35.86, longitude: 104.19),
            span: MKCoordinateSpan(latitudeDelta: 30, longitudeDelta: 30)
        )
    )
    @State private var selectedMuseum: Museum?

    var museumsWithLocation: [Museum] {
        store.museums.filter { $0.latitude != nil && $0.longitude != nil }
    }

    var body: some View {
        NavigationStack {
            Map(position: $cameraPosition, selection: $selectedMuseum) {
                ForEach(museumsWithLocation) { museum in
                    Annotation(museum.name, coordinate: CLLocationCoordinate2D(
                        latitude: museum.latitude!,
                        longitude: museum.longitude!
                    )) {
                        Image(systemName: "building.columns.fill")
                            .foregroundStyle(.white)
                            .padding(6)
                            .background(.blue)
                            .clipShape(Circle())
                    }
                    .tag(museum)
                }
            }
            .navigationTitle("博物馆地图")
            .sheet(item: $selectedMuseum) { museum in
                NavigationStack {
                    MuseumDetailView(museum: museum)
                }
                .presentationDetents([.medium, .large])
            }
        }
    }
}
