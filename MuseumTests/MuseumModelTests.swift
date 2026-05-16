import XCTest
@testable import Museum

final class MuseumModelTests: XCTestCase {

    // MARK: - Codable 解码

    func testDecodeMinimalMuseum() throws {
        let museum = try decode(category: "历史", grade: nil, freeEntry: true)
        XCTAssertEqual(museum.id, "test_museum")
        XCTAssertTrue(museum.freeEntry)
        XCTAssertNil(museum.founded)
        XCTAssertNil(museum.grade)
        XCTAssertEqual(museum.category, .history)
        XCTAssertTrue(museum.images.isEmpty)
    }

    func testDecodeAllGrades() throws {
        let cases: [(String, MuseumGrade)] = [
            ("国家一级博物馆", .nationalFirst),
            ("国家二级博物馆", .nationalSecond),
            ("国家三级博物馆", .nationalThird),
        ]
        for (raw, expected) in cases {
            let museum = try decode(grade: raw)
            XCTAssertEqual(museum.grade, expected, "grade 解码失败: \(raw)")
        }
    }

    func testDecodeAllCategories() throws {
        let cases: [(String, MuseumCategory)] = [
            ("历史", .history), ("艺术", .art), ("科技", .science),
            ("自然", .natural), ("军事", .military), ("革命纪念", .revolutionary),
            ("民俗", .folk), ("专题", .specialty), ("综合", .comprehensive),
        ]
        for (raw, expected) in cases {
            let museum = try decode(category: raw)
            XCTAssertEqual(museum.category, expected, "category 解码失败: \(raw)")
        }
    }

    // 非法 category 值应导致整个博物馆解码失败（loadFrom compactMap 会静默丢弃）
    func testInvalidCategoryThrows() {
        XCTAssertThrowsError(try decode(category: "未知类型"))
    }

    func testDecodeMuseumImage() throws {
        let json = #"{"filename":"01.jpg","caption":"外景","credit":"张三","license":"CC BY 4.0"}"#
            .data(using: .utf8)!
        let img = try JSONDecoder().decode(MuseumImage.self, from: json)
        XCTAssertEqual(img.filename, "01.jpg")
        XCTAssertEqual(img.credit, "张三")
        XCTAssertEqual(img.license, "CC BY 4.0")
    }

    func testDecodeMuseumImageNullCredit() throws {
        let json = #"{"filename":"02.jpg","caption":"内景","credit":null,"license":null}"#
            .data(using: .utf8)!
        let img = try JSONDecoder().decode(MuseumImage.self, from: json)
        XCTAssertNil(img.credit)
        XCTAssertNil(img.license)
    }

    // MARK: - formattedVisitors

    func testFormattedVisitorsNil() {
        XCTAssertNil(decode(annualVisitors: nil).formattedVisitors)
    }

    func testFormattedVisitorsUnder10000() {
        XCTAssertEqual(decode(annualVisitors: 9999).formattedVisitors, "9999")
    }

    func testFormattedVisitors1Wan() {
        XCTAssertEqual(decode(annualVisitors: 10_000).formattedVisitors, "1万")
    }

    func testFormattedVisitors500Wan() {
        XCTAssertEqual(decode(annualVisitors: 5_000_000).formattedVisitors, "500万")
    }

    // MARK: - formattedArea

    func testFormattedAreaNil() {
        XCTAssertNil(decode(area: nil).formattedArea)
    }

    func testFormattedAreaSmall() {
        XCTAssertEqual(decode(area: 999).formattedArea, "999㎡")
    }

    func testFormattedAreaExact1Wan() {
        XCTAssertEqual(decode(area: 10_000).formattedArea, "1万㎡")
    }

    func testFormattedAreaDecimalWan() {
        XCTAssertEqual(decode(area: 36_000).formattedArea, "3.6万㎡")
    }

    func testFormattedAreaRoundWan() {
        XCTAssertEqual(decode(area: 50_000).formattedArea, "5万㎡")
    }

    // MARK: - meaningfulOpeningHours

    func testMeaningfulOpeningHoursNormal() {
        XCTAssertEqual(decode(openingHours: "9:00-17:00").meaningfulOpeningHours, "9:00-17:00")
    }

    func testMeaningfulOpeningHoursPlaceholder() {
        XCTAssertNil(decode(openingHours: "请查看官网").meaningfulOpeningHours)
    }

    func testMeaningfulOpeningHoursEmpty() {
        XCTAssertNil(decode(openingHours: "").meaningfulOpeningHours)
    }

    func testMeaningfulOpeningHoursWhitespaceOnly() {
        XCTAssertNil(decode(openingHours: "   ").meaningfulOpeningHours)
    }

    // MARK: - localDirectory

    func testLocalDirectoryEqualsID() throws {
        let museum = try decode()
        XCTAssertEqual(museum.localDirectory, museum.id)
    }

    // MARK: - Factory helpers

    private func decode(
        category: String = "历史",
        grade: String? = nil,
        freeEntry: Bool = false,
        annualVisitors: Int? = nil,
        area: Double? = nil,
        openingHours: String = "请查看官网"
    ) throws -> Museum {
        let gradeStr = grade.map { #""\#($0)""# } ?? "null"
        let visitorsStr = annualVisitors.map { "\($0)" } ?? "null"
        let areaStr = area.map { "\($0)" } ?? "null"
        let json = """
        {
          "id": "test_museum", "name": "测试博物馆", "englishName": "Test Museum",
          "city": "北京", "province": "北京", "category": "\(category)",
          "founded": null, "area": \(areaStr), "annualVisitors": \(visitorsStr),
          "freeEntry": \(freeEntry), "address": "北京市东城区1号",
          "website": null, "phone": null, "openingHours": "\(openingHours)",
          "summary": "简介", "highlights": ["亮点A","亮点B","亮点C"],
          "images": [], "latitude": 39.9, "longitude": 116.4, "grade": \(gradeStr)
        }
        """.data(using: .utf8)!
        return try JSONDecoder().decode(Museum.self, from: json)
    }

    // Convenience overloads that don't throw (for computed-property tests)
    private func decode(annualVisitors: Int?) -> Museum {
        try! decode(category: "历史", annualVisitors: annualVisitors)
    }
    private func decode(area: Double?) -> Museum {
        try! decode(category: "历史", area: area)
    }
    private func decode(openingHours: String) -> Museum {
        try! decode(category: "历史", openingHours: openingHours)
    }
    private func decode() throws -> Museum {
        try decode(category: "历史")
    }
}
