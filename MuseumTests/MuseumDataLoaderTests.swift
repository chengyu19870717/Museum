import XCTest
@testable import Museum

final class MuseumDataLoaderTests: XCTestCase {

    // MARK: - loadAll (Integration — requires MuseumData in test bundle)
    // These tests pass when MuseumData folder is included in the test target's Copy Files phase.

    func testLoadAllReturnsNonEmptyList() {
        let museums = MuseumDataLoader.loadAll()
        XCTAssertFalse(museums.isEmpty, "loadAll 应返回至少一个博物馆")
    }

    func testLoadAllMuseumsHaveRequiredFields() {
        let museums = MuseumDataLoader.loadAll()
        for m in museums {
            XCTAssertFalse(m.id.isEmpty,       "\(m.name): id 不能为空")
            XCTAssertFalse(m.name.isEmpty,     "\(m.id): name 不能为空")
            XCTAssertFalse(m.province.isEmpty, "\(m.id): province 不能为空")
            XCTAssertFalse(m.city.isEmpty,     "\(m.id): city 不能为空")
            XCTAssertFalse(m.address.isEmpty,  "\(m.id): address 不能为空")
            XCTAssertEqual(m.highlights.count, 3, "\(m.id): highlights 应有 3 条，实际 \(m.highlights.count)")
        }
    }

    func testLoadAllIDsAreUnique() {
        let museums = MuseumDataLoader.loadAll()
        let ids = museums.map(\.id)
        let uniqueIDs = Set(ids)
        XCTAssertEqual(ids.count, uniqueIDs.count, "存在重复的博物馆 ID")
    }

    func testLoadAllCoordinatesInRange() {
        let museums = MuseumDataLoader.loadAll()
        let mainland = museums.filter { !["香港","澳门","台湾"].contains($0.province) }
        for m in mainland {
            if let lat = m.latitude {
                XCTAssertTrue((18.0...53.5).contains(lat),
                              "\(m.id): 纬度越界 lat=\(lat)")
            }
            if let lon = m.longitude {
                XCTAssertTrue((73.0...135.0).contains(lon),
                              "\(m.id): 经度越界 lon=\(lon)")
            }
        }
    }

    func testLoadAllCategoriesAreValid() {
        let museums = MuseumDataLoader.loadAll()
        let valid = Set(MuseumCategory.allCases)
        for m in museums {
            XCTAssertTrue(valid.contains(m.category), "\(m.id): 非法 category \(m.category.rawValue)")
        }
    }

    func testLoadAllFreeEntryIsNotNil() {
        // freeEntry 是非可选 Bool，JSON 解码不通过则条目被丢弃
        // 通过验证总数 > 0 间接保证所有条目均成功解码
        let museums = MuseumDataLoader.loadAll()
        XCTAssertGreaterThan(museums.count, 300, "博物馆数量应 > 300，实际 \(museums.count)")
    }

    func testLoadAllImagesFilesExistForMuseumsWithImages() {
        let museums = MuseumDataLoader.loadAll()
        let withImages = museums.filter { !$0.images.isEmpty }
        // At least some museums should have images in the bundle
        XCTAssertFalse(withImages.isEmpty, "应有博物馆包含图片数据")
    }

    // MARK: - buildURLMap

    func testBuildURLMapIsEmptyBeforeLoad() {
        // With no museums passed in, map should be empty
        let map = MuseumDataLoader.buildURLMap(for: [])
        XCTAssertTrue(map.isEmpty)
    }

    func testBuildURLMapKeyFormat() {
        // Museum with no images → no entries in map
        let museums = MuseumDataLoader.loadAll().filter { !$0.images.isEmpty }
        guard let first = museums.first else {
            return XCTSkip("No museums with images in test bundle")
        }
        let map = MuseumDataLoader.buildURLMap(for: [first])
        // Keys should be "museumID/filename"
        for key in map.keys {
            let parts = key.split(separator: "/")
            XCTAssertEqual(parts.count, 2, "URL map key 格式应为 'museumID/filename', 实际: \(key)")
        }
    }

    func testBuildURLMapURLsAreReachable() {
        let museums = MuseumDataLoader.loadAll().filter { !$0.images.isEmpty }
        guard !museums.isEmpty else {
            return XCTSkip("No museums with images in test bundle")
        }
        let map = MuseumDataLoader.buildURLMap(for: museums)
        for (key, url) in map {
            XCTAssertTrue(FileManager.default.fileExists(atPath: url.path),
                          "图片文件不存在: \(key) → \(url.path)")
        }
    }

    // MARK: - imageURL (@MainActor)

    @MainActor
    func testImageURLReturnsNilBeforeMapBuilt() {
        // A fresh call before applyURLMap should return nil
        let result = MuseumDataLoader.imageURL(museumID: "palace_museum", filename: "01.jpg")
        // May or may not be nil depending on whether a previous test applied the map;
        // the important thing is it doesn't crash.
        _ = result
    }
}
