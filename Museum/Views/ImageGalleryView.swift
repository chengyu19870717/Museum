import SwiftUI

struct ImageGalleryView: View {
    let museum: Museum
    @Binding var selectedIndex: Int
    @Binding var showFull: Bool

    var body: some View {
        if museum.images.isEmpty {
            emptyGallery
        } else {
            gallery
                .onAppear(perform: clampSelectedIndex)
                .onChange(of: museum.images.count) { _, _ in
                    clampSelectedIndex()
                }
        }
    }

    private var gallery: some View {
        ZStack(alignment: .bottom) {
            MuseumImageView(museumID: museum.id, image: selectedImage, contentMode: .fit)
                .id(selectedImage.filename)

            if museum.images.count > 1 {
                HStack {
                    galleryControl(systemImage: "chevron.left") {
                        moveSelection(by: -1)
                    }
                    .accessibilityLabel("上一张图片")

                    Spacer()

                    galleryControl(systemImage: "chevron.right") {
                        moveSelection(by: 1)
                    }
                    .accessibilityLabel("下一张图片")
                }
                .padding(.horizontal, 12)
                .padding(.bottom, 44)
            }

            VStack {
                HStack {
                    Spacer()
                    Button {
                        showFull = true
                    } label: {
                        Label("查看大图", systemImage: "arrow.up.left.and.arrow.down.right")
                            .font(.caption.bold())
                            .foregroundStyle(.white)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 7)
                            .background(.black.opacity(0.42), in: Capsule())
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("查看大图")
                }
                Spacer()
            }
            .padding(12)

            // Caption + page indicator
            VStack(spacing: 4) {
                Text(selectedImage.caption)
                    .font(.caption)
                    .foregroundStyle(.white)
                    .shadow(radius: 2)
                    .padding(.horizontal)

                // Dots for ≤7 images; text counter beyond that to keep the row lightweight
                if museum.images.count <= 7 {
                    HStack(spacing: 6) {
                        ForEach(museum.images.indices, id: \.self) { i in
                            Circle()
                                .fill(i == safeSelectedIndex ? Color.white : Color.white.opacity(0.5))
                                .frame(width: i == safeSelectedIndex ? 8 : 6,
                                       height: i == safeSelectedIndex ? 8 : 6)
                        }
                    }
                } else {
                    Text("\(safeSelectedIndex + 1) / \(museum.images.count)")
                        .font(.caption2.monospacedDigit())
                        .foregroundStyle(.white.opacity(0.9))
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(.black.opacity(0.4))
                        .clipShape(Capsule())
                }
            }
            .padding(.bottom, 12)
            .background(
                LinearGradient(
                    colors: [.clear, .black.opacity(0.5)],
                    startPoint: .top,
                    endPoint: .bottom
                )
            )
            .allowsHitTesting(false)
        }
    }

    private var selectedImage: MuseumImage {
        museum.images[safeSelectedIndex]
    }

    private var emptyGallery: some View {
        ZStack {
            Color.gray.opacity(0.08)
            VStack(spacing: 8) {
                Image(systemName: "photo.on.rectangle.angled")
                    .font(.largeTitle)
                    .foregroundStyle(.secondary)
                Text("暂无图片")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
    }

    private var safeSelectedIndex: Int {
        guard !museum.images.isEmpty else { return 0 }
        return min(max(selectedIndex, 0), museum.images.count - 1)
    }

    private func clampSelectedIndex() {
        selectedIndex = safeSelectedIndex
    }

    private func moveSelection(by delta: Int) {
        guard !museum.images.isEmpty else { return }
        let count = museum.images.count
        selectedIndex = (safeSelectedIndex + delta + count) % count
    }

    private func galleryControl(systemImage: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: systemImage)
                .font(.headline.bold())
                .foregroundStyle(.white)
                .frame(width: 40, height: 40)
                .background(.black.opacity(0.38), in: Circle())
                .contentShape(Circle())
        }
        .buttonStyle(.plain)
    }
}

struct MuseumThumbnailView: View {
    let museum: Museum

    var body: some View {
        if let firstImage = museum.images.first {
            MuseumImageView(museumID: museum.id, image: firstImage)
        } else {
            Image(systemName: "building.columns.fill")
                .resizable()
                .scaledToFit()
                .foregroundStyle(.gray.opacity(0.4))
                .padding(12)
                .background(Color.gray.opacity(0.1))
        }
    }
}

struct MuseumImageView: View {
    let museumID: String
    let image: MuseumImage
    var contentMode: ContentMode = .fill

    var body: some View {
        let url = MuseumDataLoader.imageURL(museumID: museumID, filename: image.filename)
        if url != nil {
            LocalImageView(url: url, contentMode: contentMode)
        } else {
            placeholderImage
        }
    }

    private var placeholderImage: some View {
        Image(systemName: "building.columns")
            .resizable()
            .aspectRatio(contentMode: contentMode)
            .foregroundStyle(.gray.opacity(0.3))
            .background(Color.gray.opacity(0.08))
    }
}

struct FullGalleryView: View {
    let museum: Museum
    let initialIndex: Int
    @Environment(\.dismiss) var dismiss
    @State private var currentIndex: Int

    init(museum: Museum, initialIndex: Int) {
        self.museum = museum
        self.initialIndex = initialIndex
        let safe = museum.images.isEmpty ? 0 : min(max(initialIndex, 0), museum.images.count - 1)
        self._currentIndex = State(initialValue: safe)
    }

    var body: some View {
        NavigationStack {
            Group {
                if museum.images.isEmpty {
                    ContentUnavailableView(
                        "暂无图片",
                        systemImage: "photo",
                        description: Text("当前博物馆还没有可查看的本地图片。")
                    )
                } else {
                    TabView(selection: $currentIndex) {
                        ForEach(Array(museum.images.enumerated()), id: \.offset) { index, img in
                            // #5: each image wrapped in a zoomable scroll view
                            ZoomableImageView(museumID: museum.id, image: img)
                                .tag(index)
                        }
                    }
                    .tabViewStyle(.page(indexDisplayMode: .never))
                    .background(Color.black)
                    .overlay(alignment: .bottom) { captionOverlay }
                }
            }
            .navigationTitle(museum.images.isEmpty ? "0 / 0" : "\(currentIndex + 1) / \(museum.images.count)")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("关闭") { dismiss() }
                }
            }
        }
    }

    @ViewBuilder
    private var captionOverlay: some View {
        if !museum.images.isEmpty {
            let img = museum.images[min(currentIndex, museum.images.count - 1)]
            VStack(spacing: 4) {
                Text(img.caption).font(.headline).foregroundStyle(.white)
                if let credit = img.credit {
                    Text("摄影：\(credit)").font(.caption).foregroundStyle(.white.opacity(0.8))
                }
                if let license = img.license {
                    Text(license).font(.caption2).foregroundStyle(.white.opacity(0.6))
                }
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 32)
        }
    }
}

// MARK: - #5: Pinch-to-zoom image view

// Custom scroll view that keeps imageView.frame in sync whenever Auto Layout
// resolves the actual bounds (first layout, rotation, split-screen resize).
private final class ZoomableScrollView: UIScrollView {
    weak var imageViewRef: UIImageView?

    override func layoutSubviews() {
        super.layoutSubviews()
        guard !bounds.isEmpty, let iv = imageViewRef, zoomScale == 1 else { return }
        if iv.frame != bounds {
            iv.frame = bounds
            contentSize = bounds.size
        }
    }
}

private struct ZoomableImageView: UIViewRepresentable {
    let museumID: String
    let image: MuseumImage

    func makeUIView(context: Context) -> ZoomableScrollView {
        let scrollView = ZoomableScrollView()
        scrollView.minimumZoomScale = 1.0
        scrollView.maximumZoomScale = 4.0
        scrollView.showsHorizontalScrollIndicator = false
        scrollView.showsVerticalScrollIndicator = false
        scrollView.bouncesZoom = true
        scrollView.backgroundColor = .black
        scrollView.delegate = context.coordinator

        let imageView = UIImageView()
        imageView.contentMode = .scaleAspectFit
        imageView.clipsToBounds = true
        imageView.backgroundColor = .black
        scrollView.addSubview(imageView)
        scrollView.imageViewRef = imageView
        context.coordinator.imageView = imageView

        // Double-tap to zoom
        let tap = UITapGestureRecognizer(target: context.coordinator, action: #selector(Coordinator.handleDoubleTap(_:)))
        tap.numberOfTapsRequired = 2
        scrollView.addGestureRecognizer(tap)

        return scrollView
    }

    func updateUIView(_ scrollView: ZoomableScrollView, context: Context) {
        guard let imageView = context.coordinator.imageView else { return }
        // Skip reload if same image is already displayed (layoutSubviews keeps frame current)
        guard context.coordinator.loadedFilename != image.filename else { return }
        context.coordinator.loadedFilename = image.filename
        // Cancel any in-flight load from a previous page swipe
        context.coordinator.loadTask?.cancel()
        let url = MuseumDataLoader.imageURL(museumID: museumID, filename: image.filename)
        context.coordinator.loadTask = Task.detached(priority: .userInitiated) {
            let uiImage = url.flatMap { UIImage(contentsOfFile: $0.path) }
            guard !Task.isCancelled else { return }
            await MainActor.run {
                guard !Task.isCancelled else { return }
                imageView.image = uiImage
                imageView.frame = scrollView.bounds
                scrollView.contentSize = scrollView.bounds.size
                scrollView.zoomScale = 1.0
            }
        }
    }

    func makeCoordinator() -> Coordinator { Coordinator() }

    static func dismantleUIView(_ uiView: ZoomableScrollView, coordinator: Coordinator) {
        coordinator.loadTask?.cancel()
    }

    final class Coordinator: NSObject, UIScrollViewDelegate {
        weak var imageView: UIImageView?
        var loadedFilename: String = ""
        var loadTask: Task<Void, Never>?

        func viewForZooming(in scrollView: UIScrollView) -> UIView? { imageView }

        func scrollViewDidZoom(_ scrollView: UIScrollView) {
            guard let imageView else { return }
            let offsetX = max((scrollView.bounds.width  - imageView.frame.width)  / 2, 0)
            let offsetY = max((scrollView.bounds.height - imageView.frame.height) / 2, 0)
            imageView.center = CGPoint(x: scrollView.contentSize.width  / 2 + offsetX,
                                       y: scrollView.contentSize.height / 2 + offsetY)
        }

        @objc func handleDoubleTap(_ gesture: UITapGestureRecognizer) {
            guard let scrollView = gesture.view as? UIScrollView else { return }
            if scrollView.zoomScale > 1 {
                scrollView.setZoomScale(1, animated: true)
            } else {
                let point = gesture.location(in: scrollView)
                let rect  = CGRect(x: point.x - 50, y: point.y - 50, width: 100, height: 100)
                scrollView.zoom(to: rect, animated: true)
            }
        }
    }
}
