import Foundation

struct MuseumDataLoader {
    /// 从 MuseumData 目录加载所有博物馆 JSON
    static func loadAll() -> [Museum] {
        if let dataURL = Bundle.main.url(forResource: "MuseumData", withExtension: nil) {
            let museums = loadFrom(directory: dataURL)
            if !museums.isEmpty { return museums }
        }
        return loadFromDocuments()
    }

    private static func loadFromDocuments() -> [Museum] {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        return loadFrom(directory: docs.appendingPathComponent("MuseumData"))
    }

    private static func loadFrom(directory: URL) -> [Museum] {
        guard let subdirs = try? FileManager.default.contentsOfDirectory(
            at: directory, includingPropertiesForKeys: [.isDirectoryKey]
        ) else { return [] }

        return subdirs.compactMap { dir in
            guard (try? dir.resourceValues(forKeys: [.isDirectoryKey]))?.isDirectory == true
            else { return nil }
            let infoURL = dir.appendingPathComponent("info.json")
            guard let data = try? Data(contentsOf: infoURL),
                  let museum = try? JSONDecoder().decode(Museum.self, from: data)
            else { return nil }
            return museum
        }
    }

    // MARK: - #7: Pre-built URL map — populated once after load, read on MainActor

    // Accessed only on MainActor (SwiftUI body is always on main thread), so no queue needed.
    @MainActor private static var _imageURLMap: [String: URL] = [:]

    /// Build the complete image URL map synchronously (call from a background task).
    static func buildURLMap(for museums: [Museum]) -> [String: URL] {
        let fm   = FileManager.default
        let docs = fm.urls(for: .documentDirectory, in: .userDomainMask).first!
        var map  = [String: URL]()
        map.reserveCapacity(museums.reduce(0) { $0 + $1.images.count })

        for museum in museums {
            let bundleDir: URL? =
                Bundle.main.url(forResource: museum.id, withExtension: nil, subdirectory: "MuseumData")
                ?? Bundle.main.url(forResource: "MuseumData", withExtension: nil)
                        .map { $0.appendingPathComponent(museum.id) }

            // List directory contents once per museum instead of one fileExists per image.
            // 63 contentsOfDirectory calls vs up to 864 fileExists calls — ~10x fewer syscalls.
            let bundleImagesDir = bundleDir?.appendingPathComponent("images")
            let bundleFiles: Set<String> = bundleImagesDir.flatMap {
                try? fm.contentsOfDirectory(atPath: $0.path)
            }.map(Set.init) ?? []

            let docImagesDir = docs.appendingPathComponent("MuseumData/\(museum.id)/images")
            let docFiles: Set<String> = (try? fm.contentsOfDirectory(atPath: docImagesDir.path))
                .map(Set.init) ?? []

            for img in museum.images {
                let key = "\(museum.id)/\(img.filename)"
                if bundleFiles.contains(img.filename), let dir = bundleImagesDir {
                    map[key] = dir.appendingPathComponent(img.filename)
                } else if docFiles.contains(img.filename) {
                    map[key] = docImagesDir.appendingPathComponent(img.filename)
                }
            }
        }
        return map
    }

    /// Apply a pre-built map; must be called on MainActor.
    @MainActor
    static func applyURLMap(_ map: [String: URL]) {
        _imageURLMap = map
    }

    @MainActor
    static func imageURL(museumID: String, filename: String) -> URL? {
        _imageURLMap["\(museumID)/\(filename)"]
    }
}
