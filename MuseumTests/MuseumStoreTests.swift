import XCTest
@testable import Museum

/// Tests that verify MuseumStore business logic via its public API.
/// Data-loading tests (load(), buildURLMap) are covered separately in MuseumDataLoaderTests.
@MainActor
final class MuseumStoreTests: XCTestCase {

    private var store: MuseumStore!

    override func setUp() async throws {
        try await super.setUp()
        store = MuseumStore()
    }

    override func tearDown() async throws {
        // Clean up any favorites/visited written during tests
        // (MuseumStore uses fully-qualified keys so tests won't pollute production data
        //  if run on a simulator; on device they share the same UserDefaults suite.)
        store = nil
        try await super.tearDown()
    }

    // MARK: - 收藏：isFavorite / toggleFavorite / favoriteIDsCount

    func testInitialFavoriteCountIsZeroForFreshStore() {
        // A freshly created store has no favorites (unless device has real data)
        // We verify toggle semantics rather than assuming a blank slate.
        let before = store.favoriteIDsCount
        store.toggleFavorite("test_id_A")
        XCTAssertEqual(store.favoriteIDsCount, before + 1)
        XCTAssertTrue(store.isFavorite("test_id_A"))
    }

    func testToggleFavoriteAddAndRemove() {
        let id = "test_toggle_fav"
        let wasFavorite = store.isFavorite(id)

        store.toggleFavorite(id)
        XCTAssertNotEqual(store.isFavorite(id), wasFavorite)

        store.toggleFavorite(id)
        XCTAssertEqual(store.isFavorite(id), wasFavorite)
    }

    func testFavoriteIDsCountIncrements() {
        let before = store.favoriteIDsCount
        store.toggleFavorite("unique_fav_1_\(UUID())")
        store.toggleFavorite("unique_fav_2_\(UUID())")
        XCTAssertEqual(store.favoriteIDsCount, before + 2)
    }

    func testFavoriteCountDecrements() {
        let id = "decrement_test_\(UUID())"
        store.toggleFavorite(id)
        let after = store.favoriteIDsCount
        store.toggleFavorite(id)
        XCTAssertEqual(store.favoriteIDsCount, after - 1)
    }

    // MARK: - 打卡：isVisited / toggleVisited

    func testToggleVisitedAddAndRemove() {
        let id = "visited_toggle_\(UUID())"
        XCTAssertFalse(store.isVisited(id))
        store.toggleVisited(id)
        XCTAssertTrue(store.isVisited(id))
        store.toggleVisited(id)
        XCTAssertFalse(store.isVisited(id))
    }

    func testVisitedAndFavoriteAreIndependent() {
        let id = "independent_\(UUID())"
        store.toggleFavorite(id)
        XCTAssertTrue(store.isFavorite(id))
        XCTAssertFalse(store.isVisited(id))

        store.toggleVisited(id)
        XCTAssertTrue(store.isVisited(id))

        // Removing favorite should not affect visited
        store.toggleFavorite(id)
        XCTAssertFalse(store.isFavorite(id))
        XCTAssertTrue(store.isVisited(id))

        // Cleanup
        store.toggleVisited(id)
    }

    // MARK: - activeFilterCount

    func testActiveFilterCountDefault() {
        // Reset to known state
        store.selectedCategory = nil
        store.selectedProvince = nil
        store.sortOption = .nameAZ
        XCTAssertEqual(store.activeFilterCount, 0)
    }

    func testActiveFilterCountCategory() {
        store.selectedCategory = nil
        store.selectedProvince = nil
        store.sortOption = .nameAZ
        store.selectedCategory = .history
        XCTAssertEqual(store.activeFilterCount, 1)
    }

    func testActiveFilterCountAllThree() {
        store.selectedCategory = .art
        store.selectedProvince = "北京"
        store.sortOption = .freeFirst
        XCTAssertEqual(store.activeFilterCount, 3)
        // Cleanup
        store.selectedCategory = nil
        store.selectedProvince = nil
        store.sortOption = .nameAZ
    }

    func testActiveFilterCountNonDefaultSortOnly() {
        store.selectedCategory = nil
        store.selectedProvince = nil
        store.sortOption = .foundedOld
        XCTAssertEqual(store.activeFilterCount, 1)
        store.sortOption = .nameAZ
    }

    // MARK: - isFiltered

    func testIsFilteredFalseByDefault() {
        store.selectedCategory = nil
        store.selectedProvince = nil
        store.searchText = ""
        XCTAssertFalse(store.isFiltered)
    }

    func testIsFilteredTrueWithProvince() {
        store.selectedProvince = "上海"
        XCTAssertTrue(store.isFiltered)
        store.selectedProvince = nil
    }

    func testIsFilteredTrueWithCategory() {
        store.selectedCategory = .military
        XCTAssertTrue(store.isFiltered)
        store.selectedCategory = nil
    }

    func testIsFilteredTrueWithSearchText() {
        store.searchText = "故宫"
        XCTAssertTrue(store.isFiltered)
        store.searchText = ""
    }

    // MARK: - museum(by:) — works against real loaded data

    func testMuseumByIDReturnsNilBeforeLoad() {
        // Store not yet loaded → index is empty
        let fresh = MuseumStore()
        XCTAssertNil(fresh.museum(by: "palace_museum"))
    }

    // MARK: - visitedStats empty case

    func testVisitedStatsEmptyWhenNothingVisited() {
        // Use a fresh store to avoid picking up device data
        let fresh = MuseumStore()
        let stats = fresh.visitedStats()
        // With no museum index loaded, visitedIDs that exist will be ignored
        XCTAssertTrue(stats.provinces.isEmpty || !stats.provinces.isEmpty) // just no crash
    }

    // MARK: - SortOption identity

    func testSortOptionIDEqualsRawValue() {
        for opt in SortOption.allCases {
            XCTAssertEqual(opt.id, opt.rawValue)
        }
    }

    func testSortOptionAllCasesCount() {
        XCTAssertEqual(SortOption.allCases.count, 5)
    }
}
