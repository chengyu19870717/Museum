import XCTest
@testable import Museum

final class PinyinHelperTests: XCTestCase {

    // MARK: - toPinyin

    func testToPinyinBasic() {
        // 汉字转拼音（去声调）
        XCTAssertEqual(PinyinHelper.toPinyin("故宫"), "gu gong")
    }

    func testToPinyinMixed() {
        // 中英混合：英文保留，汉字转拼音
        let result = PinyinHelper.toPinyin("上海Museum")
        XCTAssertTrue(result.lowercased().contains("shang"))
        XCTAssertTrue(result.lowercased().contains("museum"))
    }

    func testToPinyinEmpty() {
        XCTAssertEqual(PinyinHelper.toPinyin(""), "")
    }

    func testToPinyinPureEnglish() {
        XCTAssertEqual(PinyinHelper.toPinyin("Beijing"), "beijing")
    }

    // MARK: - toPinyinInitials

    func testToPinyinInitials() {
        // "故宫博物院" → "ggbwy"
        let initials = PinyinHelper.toPinyinInitials("故宫博物院")
        XCTAssertFalse(initials.isEmpty)
        XCTAssertTrue(initials.hasPrefix("g"))
    }

    func testToPinyinInitialsEmpty() {
        XCTAssertEqual(PinyinHelper.toPinyinInitials(""), "")
    }

    // MARK: - compactLetters

    func testCompactLettersStripsSpaces() {
        XCTAssertEqual(PinyinHelper.compactLetters("gu gong"), "gugong")
    }

    func testCompactLettersLowercase() {
        XCTAssertEqual(PinyinHelper.compactLetters("GuGong"), "gugong")
    }

    func testCompactLettersStripsSpecialChars() {
        XCTAssertEqual(PinyinHelper.compactLetters("a-b.c!d"), "abcd")
    }

    func testCompactLettersKeepsDigits() {
        XCTAssertEqual(PinyinHelper.compactLetters("abc123"), "abc123")
    }

    func testCompactLettersEmpty() {
        XCTAssertEqual(PinyinHelper.compactLetters(""), "")
    }

    // MARK: - searchBlob

    func testSearchBlobContainsOriginal() {
        let blob = PinyinHelper.searchBlob(for: "故宫博物院")
        XCTAssertTrue(blob.contains("故宫博物院"))
    }

    func testSearchBlobContainsPinyin() {
        let blob = PinyinHelper.searchBlob(for: "故宫")
        // Should contain "gu gong" or "gugong"
        XCTAssertTrue(blob.contains("gu") && blob.contains("gong"), "blob should contain pinyin: \(blob)")
    }

    func testSearchBlobContainsInitials() {
        let blob = PinyinHelper.searchBlob(for: "故宫博物院")
        // Should contain initials like "ggbwy"
        let hasInitial = blob.split(separator: " ").contains { $0.count < 10 && $0.allSatisfy(\.isLetter) }
        XCTAssertTrue(hasInitial, "blob should contain initials: \(blob)")
    }

    func testSearchBlobIsLowercased() {
        let blob = PinyinHelper.searchBlob(for: "MUSEUM")
        XCTAssertEqual(blob, blob.lowercased())
    }

    // MARK: - normalizedQuery

    func testNormalizedQueryTrimsWhitespace() {
        XCTAssertEqual(PinyinHelper.normalizedQuery("  故宫  "), "故宫")
    }

    func testNormalizedQueryLowercases() {
        XCTAssertEqual(PinyinHelper.normalizedQuery("BEIJING"), "beijing")
    }

    func testNormalizedQueryEmpty() {
        XCTAssertEqual(PinyinHelper.normalizedQuery(""), "")
    }

    // MARK: - 搜索场景验证

    func testSearchByPinyinInitials() {
        // 用户输入 "ggbwy" 应该能匹配 "故宫博物院"
        let blob = PinyinHelper.searchBlob(for: "故宫博物院")
        let query = PinyinHelper.normalizedQuery("ggbwy")
        let compact = PinyinHelper.compactLetters(query)
        let matched = blob.contains(query) || (!compact.isEmpty && blob.contains(compact))
        XCTAssertTrue(matched, "拼音首字母搜索失败, blob=\(blob)")
    }

    func testSearchByFullPinyin() {
        // 用户输入 "gugong" 应该能匹配
        let blob = PinyinHelper.searchBlob(for: "故宫博物院")
        let query = PinyinHelper.normalizedQuery("gugong")
        let compact = PinyinHelper.compactLetters(query)
        let matched = blob.contains(query) || (!compact.isEmpty && blob.contains(compact))
        XCTAssertTrue(matched, "全拼搜索失败, blob=\(blob)")
    }

    func testSearchByChinese() {
        // 用户输入 "故宫" 应该直接匹配
        let blob = PinyinHelper.searchBlob(for: "故宫博物院")
        XCTAssertTrue(blob.contains("故宫"), "中文直接搜索失败")
    }
}
