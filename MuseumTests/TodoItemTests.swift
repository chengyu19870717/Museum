import XCTest
@testable import Museum

final class TodoItemTests: XCTestCase {

    // MARK: - Codable 往返

    func testEncodeDecode() throws {
        let original = TodoItem(
            title: "参观故宫",
            note: "买好票",
            priority: .high,
            isDone: false,
            createdAt: Date(timeIntervalSince1970: 1_700_000_000),
            dueDate: Date(timeIntervalSince1970: 1_800_000_000)
        )
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(TodoItem.self, from: data)

        XCTAssertEqual(decoded.id, original.id)
        XCTAssertEqual(decoded.title, original.title)
        XCTAssertEqual(decoded.note, original.note)
        XCTAssertEqual(decoded.priority, .high)
        XCTAssertFalse(decoded.isDone)
        XCTAssertEqual(decoded.dueDate?.timeIntervalSince1970,
                       original.dueDate?.timeIntervalSince1970,
                       accuracy: 1)
    }

    func testEncodeDecodeNilDueDate() throws {
        let item = TodoItem(title: "测试", dueDate: nil)
        let data  = try JSONEncoder().encode(item)
        let decoded = try JSONDecoder().decode(TodoItem.self, from: data)
        XCTAssertNil(decoded.dueDate)
    }

    func testEncodeDecodeList() throws {
        let items = [
            TodoItem(title: "A", priority: .low),
            TodoItem(title: "B", priority: .medium, isDone: true),
            TodoItem(title: "C", priority: .high),
        ]
        let data    = try JSONEncoder().encode(items)
        let decoded = try JSONDecoder().decode([TodoItem].self, from: data)
        XCTAssertEqual(decoded.count, 3)
        XCTAssertEqual(decoded[1].isDone, true)
    }

    // MARK: - Priority

    func testPriorityAllCasesCount() {
        XCTAssertEqual(TodoItem.Priority.allCases.count, 3)
    }

    func testPrioritySortOrder() {
        XCTAssertLessThan(TodoItem.Priority.high.sortOrder, TodoItem.Priority.medium.sortOrder)
        XCTAssertLessThan(TodoItem.Priority.medium.sortOrder, TodoItem.Priority.low.sortOrder)
    }

    func testPriorityRawValues() {
        XCTAssertEqual(TodoItem.Priority.high.rawValue,   "高")
        XCTAssertEqual(TodoItem.Priority.medium.rawValue, "中")
        XCTAssertEqual(TodoItem.Priority.low.rawValue,    "低")
    }

    func testPriorityIcons() {
        // Each priority has a distinct SF Symbol name
        let icons = TodoItem.Priority.allCases.map(\.icon)
        XCTAssertEqual(Set(icons).count, icons.count, "每个优先级应有唯一图标")
    }

    // MARK: - Equatable

    func testEqualityByID() throws {
        var item = TodoItem(title: "测试")
        let copy = item
        XCTAssertEqual(item, copy)

        item.title = "修改后"
        XCTAssertNotEqual(item, copy) // Equatable checks all fields via struct
    }

    // MARK: - Default values

    func testDefaultPriorityIsMedium() {
        let item = TodoItem(title: "默认优先级")
        XCTAssertEqual(item.priority, .medium)
    }

    func testDefaultIsDoneIsFalse() {
        let item = TodoItem(title: "未完成")
        XCTAssertFalse(item.isDone)
    }

    func testDefaultNoteIsEmpty() {
        let item = TodoItem(title: "无备注")
        XCTAssertTrue(item.note.isEmpty)
    }

    func testIDIsUniquePerInstance() {
        let a = TodoItem(title: "A")
        let b = TodoItem(title: "B")
        XCTAssertNotEqual(a.id, b.id)
    }
}
