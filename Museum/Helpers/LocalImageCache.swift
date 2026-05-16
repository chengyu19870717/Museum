import UIKit
import SwiftUI

// MARK: - In-memory image cache backed by NSCache

final class LocalImageCache {
    static let shared = LocalImageCache()
    private let cache = NSCache<NSString, UIImage>()

    private init() {
        // totalCostLimit is the binding constraint; countLimit acts as a safety net
        // for small images that don't consume much cost individually.
        cache.countLimit = 150
        cache.totalCostLimit = 80 * 1024 * 1024 // 80 MB — fits comfortably in iOS memory budget
        NotificationCenter.default.addObserver(
            forName: UIApplication.didReceiveMemoryWarningNotification,
            object: nil, queue: .main
        ) { [weak self] _ in
            self?.cache.removeAllObjects()
        }
    }

    func image(for url: URL) -> UIImage? {
        cache.object(forKey: url.path as NSString)
    }

    func store(_ image: UIImage, for url: URL) {
        let cost = Int(image.size.width * image.size.height * image.scale * image.scale * 4)
        cache.setObject(image, forKey: url.path as NSString, cost: cost)
    }
}

// MARK: - Async local-file image view with cache

struct LocalImageView: View {
    let url: URL?
    var contentMode: ContentMode = .fill
    @State private var uiImage: UIImage?

    var body: some View {
        Group {
            if let uiImage {
                Image(uiImage: uiImage)
                    .resizable()
                    .aspectRatio(contentMode: contentMode)
                    .transition(.opacity)
            } else {
                Color.gray.opacity(0.1)
                    .overlay(ProgressView())
            }
        }
        .task(id: url?.path) { await load() }
    }

    private func load() async {
        uiImage = nil  // instant clear — no animation so old image doesn't linger
        guard let url else { return }
        if let cached = LocalImageCache.shared.image(for: url) {
            withAnimation(.easeIn(duration: 0.2)) { uiImage = cached }
            return
        }
        let loaded = await Task.detached(priority: .userInitiated) {
            UIImage(contentsOfFile: url.path)
        }.value
        guard !Task.isCancelled else { return }
        if let loaded {
            LocalImageCache.shared.store(loaded, for: url)
            withAnimation(.easeIn(duration: 0.2)) { uiImage = loaded }
        }
    }
}
