import SwiftUI
import MapKit
import CoreLocation

// MARK: - UIViewRepresentable wrapping MKMapView with clustering support

struct ClusteredMapView: UIViewRepresentable {
    let museums: [Museum]
    @Binding var selectedMuseum: Museum?

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIView(context: Context) -> MKMapView {
        let mapView = MKMapView()
        mapView.delegate = context.coordinator
        // Only enable user location after permission is already granted — never prompt on launch.
        let status = context.coordinator.locationManager.authorizationStatus
        mapView.showsUserLocation = (status == .authorizedWhenInUse || status == .authorizedAlways)
        context.coordinator.mapView = mapView
        mapView.register(
            MuseumPinView.self,
            forAnnotationViewWithReuseIdentifier: MuseumPinView.reuseID
        )
        mapView.register(
            MKMarkerAnnotationView.self,
            forAnnotationViewWithReuseIdentifier: MKMapViewDefaultClusterAnnotationViewReuseIdentifier
        )
        mapView.setRegion(
            MKCoordinateRegion(
                center: CLLocationCoordinate2D(latitude: 35.86, longitude: 104.19),
                span: MKCoordinateSpan(latitudeDelta: 30, longitudeDelta: 30)
            ),
            animated: false
        )

        // #10: user tracking button, pinned to bottom-right safe area
        let trackingButton = MKUserTrackingButton(mapView: mapView)
        trackingButton.translatesAutoresizingMaskIntoConstraints = false
        trackingButton.backgroundColor = UIColor.systemBackground.withAlphaComponent(0.85)
        trackingButton.layer.cornerRadius = 8
        mapView.addSubview(trackingButton)
        NSLayoutConstraint.activate([
            trackingButton.trailingAnchor.constraint(equalTo: mapView.safeAreaLayoutGuide.trailingAnchor, constant: -12),
            trackingButton.bottomAnchor.constraint(equalTo: mapView.safeAreaLayoutGuide.bottomAnchor, constant: -16),
        ])

        return mapView
    }

    func updateUIView(_ mapView: MKMapView, context: Context) {
        // All incoming museums are pre-filtered to have coordinates (done in MapView)
        let newIDs = Set(museums.map(\.id))
        let existing = mapView.annotations.compactMap { $0 as? MuseumAnnotation }
        let existingIDs = Set(existing.map(\.museumID))

        let toRemove = existing.filter { !newIDs.contains($0.museumID) }
        if !toRemove.isEmpty { mapView.removeAnnotations(toRemove) }

        let toAdd: [MuseumAnnotation] = museums.compactMap { museum in
            guard !existingIDs.contains(museum.id),
                  let lat = museum.latitude, let lon = museum.longitude
            else { return nil }
            return MuseumAnnotation(museum: museum, lat: lat, lon: lon)
        }
        if !toAdd.isEmpty { mapView.addAnnotations(toAdd) }
    }

    // MARK: - Coordinator

    final class Coordinator: NSObject, MKMapViewDelegate, CLLocationManagerDelegate {
        var parent: ClusteredMapView
        weak var mapView: MKMapView?
        let locationManager = CLLocationManager()

        init(_ parent: ClusteredMapView) {
            self.parent = parent
            super.init()
            locationManager.delegate = self
        }

        func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
            let status = manager.authorizationStatus
            if status == .authorizedWhenInUse || status == .authorizedAlways {
                mapView?.showsUserLocation = true
            }
        }

        func mapView(_ mapView: MKMapView, viewFor annotation: MKAnnotation) -> MKAnnotationView? {
            if annotation is MKUserLocation { return nil }

            if let cluster = annotation as? MKClusterAnnotation {
                let view = mapView.dequeueReusableAnnotationView(
                    withIdentifier: MKMapViewDefaultClusterAnnotationViewReuseIdentifier,
                    for: cluster
                ) as! MKMarkerAnnotationView
                view.markerTintColor = .systemBlue
                view.titleVisibility = .hidden
                return view
            }

            if let ann = annotation as? MuseumAnnotation {
                let view = mapView.dequeueReusableAnnotationView(
                    withIdentifier: MuseumPinView.reuseID,
                    for: ann
                ) as! MuseumPinView
                return view
            }

            return nil
        }

        func mapView(_ mapView: MKMapView, didSelect view: MKAnnotationView) {
            if let ann = view.annotation as? MuseumAnnotation {
                // Single museum pin: show detail
                parent.selectedMuseum = ann.museum
                mapView.deselectAnnotation(ann, animated: false)
                return
            }

            if let cluster = view.annotation as? MKClusterAnnotation {
                // Cluster: zoom in to reveal individual pins
                mapView.deselectAnnotation(cluster, animated: false)
                var region = mapView.region
                region.span.latitudeDelta  /= 3
                region.span.longitudeDelta /= 3
                region.center = cluster.coordinate
                mapView.setRegion(region, animated: true)
            }
        }
    }
}

// MARK: - Custom annotation model

final class MuseumAnnotation: NSObject, MKAnnotation {
    let museum: Museum
    let coordinate: CLLocationCoordinate2D
    var title: String? { museum.name }
    var museumID: String { museum.id }

    init(museum: Museum, lat: Double, lon: Double) {
        self.museum = museum
        self.coordinate = CLLocationCoordinate2D(latitude: lat, longitude: lon)
    }
}

// MARK: - Custom annotation view with clustering identifier

final class MuseumPinView: MKAnnotationView {
    static let reuseID = "museum-pin"

    override init(annotation: MKAnnotation?, reuseIdentifier: String?) {
        super.init(annotation: annotation, reuseIdentifier: reuseIdentifier)
        clusteringIdentifier = "museum-cluster"
        canShowCallout = false
        setupAppearance()
    }

    required init?(coder: NSCoder) { super.init(coder: coder) }

    private func setupAppearance() {
        let size: CGFloat = 32
        let bg = UIView(frame: CGRect(x: 0, y: 0, width: size, height: size))
        bg.backgroundColor = .systemBlue
        bg.layer.cornerRadius = size / 2

        let config = UIImage.SymbolConfiguration(pointSize: 14, weight: .medium)
        let icon = UIImage(systemName: "building.columns.fill", withConfiguration: config)?
            .withTintColor(.white, renderingMode: .alwaysOriginal)
        let iconView = UIImageView(image: icon)
        iconView.frame = CGRect(x: 9, y: 9, width: 14, height: 14)
        iconView.contentMode = .scaleAspectFit
        bg.addSubview(iconView)

        addSubview(bg)
        frame = bg.frame
        centerOffset = CGPoint(x: 0, y: -size / 2)
    }
}
