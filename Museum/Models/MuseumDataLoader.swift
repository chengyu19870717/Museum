import Foundation

struct MuseumDataLoader {
    /// 从 MuseumData 目录加载所有博物馆 JSON
    static func loadAll() -> [Museum] {
        // 优先从 Bundle 加载
        if let dataURL = Bundle.main.url(forResource: "MuseumData", withExtension: nil) {
            let museums = loadFrom(directory: dataURL)
            if !museums.isEmpty { return museums }
        }
        // Fallback：从 Documents 目录加载（支持远程更新场景）
        return loadFromDocuments()
    }

    private static func loadFromDocuments() -> [Museum] {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        let dataDir = docs.appendingPathComponent("MuseumData")
        return loadFrom(directory: dataDir)
    }

    private static func loadFrom(directory: URL) -> [Museum] {
        guard let subdirs = try? FileManager.default.contentsOfDirectory(
            at: directory, includingPropertiesForKeys: [.isDirectoryKey]
        ) else { return [] }

        return subdirs.compactMap { dir in
            let infoURL = dir.appendingPathComponent("info.json")
            guard let data = try? Data(contentsOf: infoURL),
                  let museum = try? JSONDecoder().decode(Museum.self, from: data)
            else { return nil }
            return museum
        }
    }

    /// 获取某博物馆的图片本地 URL
    static func imageURL(museumID: String, filename: String) -> URL? {
        // 1. 尝试从 Bundle 的 MuseumData 子目录查找
        if let baseURL = Bundle.main.url(forResource: museumID, withExtension: nil, subdirectory: "MuseumData") {
            let imgURL = baseURL.appendingPathComponent("images/\(filename)")
            if FileManager.default.fileExists(atPath: imgURL.path) { return imgURL }
        }

        // 2. 尝试直接从 Bundle 根目录查找（某些打包方式可能将资源放在根目录）
        if let baseURL = Bundle.main.url(forResource: "MuseumData", withExtension: nil) {
            let imgURL = baseURL.appendingPathComponent("\(museumID)/images/\(filename)")
            if FileManager.default.fileExists(atPath: imgURL.path) { return imgURL }
        }

        // 3. Fallback：从 Documents 目录查找
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        let docURL = docs.appendingPathComponent("MuseumData/\(museumID)/images/\(filename)")
        if FileManager.default.fileExists(atPath: docURL.path) { return docURL }

        return nil
    }
}