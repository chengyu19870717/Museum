import XCTest
@testable import Museum

final class MuseumURLExtensionTests: XCTestCase {

    // MARK: - websiteURL

    func testWebsiteURLValid() throws {
        let m = try museum(website: "https://www.dpm.org.cn/")
        XCTAssertEqual(m.websiteURL?.absoluteString, "https://www.dpm.org.cn/")
    }

    func testWebsiteURLNil() throws {
        XCTAssertNil(try museum(website: nil).websiteURL)
    }

    func testWebsiteURLEmptyString() throws {
        XCTAssertNil(try museum(website: "").websiteURL)
    }

    func testWebsiteURLHTTP() throws {
        let m = try museum(website: "http://www.zbsbwg.cn")
        XCTAssertNotNil(m.websiteURL)
    }

    // MARK: - phoneURL

    func testPhoneURLSimple() throws {
        let m = try museum(phone: "010-65132255")
        XCTAssertEqual(m.phoneURL?.absoluteString, "tel://01065132255")
    }

    func testPhoneURLNil() throws {
        XCTAssertNil(try museum(phone: nil).phoneURL)
    }

    func testPhoneURLEmpty() throws {
        XCTAssertNil(try museum(phone: "").phoneURL)
    }

    func testPhoneURLMultiplePicksFirst() throws {
        // 多个电话号码用分号分隔，应取第一个有效的
        let m = try museum(phone: "010-12345678；021-87654321")
        XCTAssertEqual(m.phoneURL?.absoluteString, "tel://01012345678")
    }

    func testPhoneURLStripsNonDigits() throws {
        let m = try museum(phone: "0533-2287817")
        // Should strip the dash
        XCTAssertEqual(m.phoneURL?.absoluteString, "tel://05332287817")
    }

    func testPhoneURLTooShort() throws {
        // Less than 5 digits → no valid phone
        XCTAssertNil(try museum(phone: "1234").phoneURL)
    }

    // MARK: - mapURL

    func testMapURLWithCoordinates() throws {
        let m = try museum(lat: 39.9169, lon: 116.3907)
        let url = m.mapURL
        XCTAssertNotNil(url)
        let str = url!.absoluteString
        XCTAssertTrue(str.contains("maps.apple.com"), "Expected Apple Maps URL")
        XCTAssertTrue(str.contains("ll="), "Expected ll= coordinate param")
    }

    func testMapURLWithAddressOnly() throws {
        let m = try museum(lat: nil, lon: nil)
        let url = m.mapURL
        XCTAssertNotNil(url)
        XCTAssertTrue(url!.absoluteString.contains("maps.apple.com"))
        XCTAssertTrue(url!.absoluteString.contains("q="))
    }

    func testMapURLNilWhenNoCoordAndNoAddress() throws {
        let m = try museum(lat: nil, lon: nil, address: "")
        XCTAssertNil(m.mapURL)
    }

    // MARK: - shareText

    func testShareTextContainsName() throws {
        let m = try museum()
        XCTAssertTrue(m.shareText.contains(m.name))
    }

    func testShareTextContainsProvince() throws {
        let m = try museum()
        XCTAssertTrue(m.shareText.contains(m.province))
    }

    func testShareTextContainsWebsite() throws {
        let m = try museum(website: "https://www.test.cn/")
        XCTAssertTrue(m.shareText.contains("https://www.test.cn/"))
    }

    func testShareTextExcludesEmptyWebsite() throws {
        let m = try museum(website: nil)
        // Should not have a trailing nil / blank line
        XCTAssertFalse(m.shareText.contains("null"))
        XCTAssertFalse(m.shareText.hasSuffix("\n"))
    }

    // MARK: - Factory

    private func museum(
        phone: String? = "010-65132255",
        website: String? = "https://www.dpm.org.cn/",
        lat: Double? = 39.9169,
        lon: Double? = 116.3907,
        address: String = "北京市东城区景山前街4号"
    ) throws -> Museum {
        let latStr     = lat.map { "\($0)" } ?? "null"
        let lonStr     = lon.map { "\($0)" } ?? "null"
        let phoneStr   = phone.map { #""\#($0)""# } ?? "null"
        let websiteStr = website.map { #""\#($0)""# } ?? "null"
        let json = """
        {
          "id": "palace_museum", "name": "故宫博物院", "englishName": "Palace Museum",
          "city": "北京", "province": "北京", "category": "历史",
          "founded": 1925, "area": 720000, "annualVisitors": 17000000,
          "freeEntry": false, "address": "\(address)",
          "website": \(websiteStr), "phone": \(phoneStr),
          "openingHours": "8:30-17:00",
          "summary": "故宫博物院简介", "highlights": ["清明上河图","翠玉白菜","毛公鼎"],
          "images": [], "latitude": \(latStr), "longitude": \(lonStr),
          "grade": "国家一级博物馆"
        }
        """.data(using: .utf8)!
        return try JSONDecoder().decode(Museum.self, from: json)
    }
}
