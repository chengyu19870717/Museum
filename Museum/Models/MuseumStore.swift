import Foundation
import Combine

enum SortOption: String, CaseIterable, Identifiable {
    case nameAZ       = "名称 A-Z"
    case foundedOld   = "建馆最早"
    case foundedNew   = "建馆最新"
    case visitorsDesc = "访客最多"
    case freeFirst    = "免费优先"
    var id: String { rawValue }
}

@MainActor
class MuseumStore: ObservableObject {
    @Published private(set) var museums: [Museum] = []
    @Published private(set) var isLoading = false
    @Published private(set) var loadError = false
    @Published var searchText = ""
    @Published var selectedCategory: MuseumCategory? = nil
    @Published var selectedProvince: String? = nil
    @Published var sortOption: SortOption = .nameAZ

    @Published private var favoriteIDs: [String] = [] { didSet { favoriteIDSet = Set(favoriteIDs) } }
    @Published private var visitedIDs:  [String] = [] { didSet { visitedIDSet  = Set(visitedIDs)  } }
    // #8: O(1) membership checks — rebuilt automatically via didSet
    private var favoriteIDSet: Set<String> = []
    private var visitedIDSet:  Set<String> = []
    @Published private(set) var debouncedSearchText: String = ""

    // Cached filtered results — updated only when inputs change
    @Published private(set) var filteredMuseums: [Museum] = []

    private(set) var categoryCounts: [(category: MuseumCategory, count: Int)] = []
    private(set) var provinceCounts: [(province: String, count: Int)] = []
    private(set) var provinces: [String] = []

    // Pre-computed stats used by AboutView
    private(set) var statsMuseumsWithWebsite: Int = 0
    private(set) var statsMuseumsWithAddress: Int = 0
    private(set) var statsMuseumsWithFounded: Int = 0
    private(set) var statsMuseumsWithLocation: Int = 0
    private(set) var statsMuseumsWithEnglishName: Int = 0
    private(set) var statsTotalImages: Int = 0
    private(set) var statsImagesWithCredit: Int = 0
    private(set) var statsImagesWithLicense: Int = 0

    // #6: single index entry replaces two separate dictionaries
    private struct IndexEntry {
        let museum: Museum
        let searchBlob: String
    }
    private var museumIndex: [String: IndexEntry] = [:]

    private var cancellables = Set<AnyCancellable>()

    private let favoritesKey = "com.museum.app.favoriteMuseumIDs"
    private let visitedKey   = "com.museum.app.visitedMuseumIDs"

    init() {
        Self.migrateIfNeeded(from: "favoriteMuseumIDs", to: favoritesKey)
        Self.migrateIfNeeded(from: "visitedMuseumIDs",  to: visitedKey)
        let fav = Self.loadIDs(forKey: favoritesKey)
        let vis = Self.loadIDs(forKey: visitedKey)
        favoriteIDs    = fav;  favoriteIDSet = Set(fav)
        visitedIDs     = vis;  visitedIDSet  = Set(vis)

        $searchText
            .debounce(for: .milliseconds(150), scheduler: RunLoop.main)
            .sink { [weak self] text in self?.debouncedSearchText = text }
            .store(in: &cancellables)

        // Rebuild filteredMuseums only when its inputs actually change
        Publishers.CombineLatest4(
            $museums,
            $debouncedSearchText,
            Publishers.CombineLatest($selectedCategory, $selectedProvince),
            $sortOption
        )
        .map { [weak self] museums, query, categoryProvince, sort -> [Museum] in
            guard let self else { return [] }
            return self.computeFiltered(
                museums: museums,
                query: query,
                category: categoryProvince.0,
                province: categoryProvince.1,
                sort: sort
            )
        }
        .assign(to: &$filteredMuseums)
    }

    // MARK: - Favorites

    var favoriteMuseums: [Museum] { favoriteIDs.compactMap { museum(by: $0) } }
    // O(1) count — avoids O(n) compactMap just for badges/stats
    var favoriteIDsCount: Int { favoriteIDs.count }

    func isFavorite(_ id: String) -> Bool { favoriteIDSet.contains(id) }

    func toggleFavorite(_ id: String) {
        toggle(id, in: &favoriteIDs, knownInSet: favoriteIDSet)
        saveIDs(favoriteIDs, forKey: favoritesKey)
    }

    // MARK: - Visited / Check-in

    var visitedMuseums: [Museum] { visitedIDs.compactMap { museum(by: $0) } }

    func isVisited(_ id: String) -> Bool { visitedIDSet.contains(id) }

    func toggleVisited(_ id: String) {
        toggle(id, in: &visitedIDs, knownInSet: visitedIDSet)
        saveIDs(visitedIDs, forKey: visitedKey)
    }

    var visitedProvinces: Set<String>          { Set(visitedIDs.compactMap { museumIndex[$0]?.museum.province }) }
    var visitedCategories: Set<MuseumCategory> { Set(visitedIDs.compactMap { museumIndex[$0]?.museum.category }) }

    /// Returns province and category sets for visited museums in a single pass.
    func visitedStats() -> (provinces: Set<String>, categories: Set<MuseumCategory>) {
        var provinces  = Set<String>()
        var categories = Set<MuseumCategory>()
        for id in visitedIDs {
            if let m = museumIndex[id]?.museum {
                provinces.insert(m.province)
                categories.insert(m.category)
            }
        }
        return (provinces, categories)
    }

    // MARK: - Active filter count (for badge)

    var activeFilterCount: Int {
        (selectedCategory != nil ? 1 : 0) +
        (selectedProvince != nil ? 1 : 0) +
        (sortOption != .nameAZ ? 1 : 0)
    }

    var isFiltered: Bool {
        !debouncedSearchText.isEmpty || selectedCategory != nil || selectedProvince != nil
    }

    // MARK: - Load

    func load(forceReload: Bool = false) {
        guard !isLoading else { return }
        guard forceReload || museums.isEmpty else { return }
        isLoading = true

        Task.detached(priority: .userInitiated) {
            let loaded = MuseumDataLoader.loadAll()
            let sortedByName = loaded.sorted { $0.name < $1.name }
            // #7: build URL map synchronously in this background task
            let urlMap = MuseumDataLoader.buildURLMap(for: sortedByName)
            let index  = Dictionary(uniqueKeysWithValues: sortedByName.map {
                ($0.id, IndexEntry(museum: $0, searchBlob: Self.searchBlob(for: $0)))
            })

            await MainActor.run { [weak self] in
                guard let self else { return }
                if sortedByName.isEmpty {
                    self.loadError = true
                } else {
                    self.museums = sortedByName
                    self.museumIndex = index
                    MuseumDataLoader.applyURLMap(urlMap)
                    self.precomputeStats(for: sortedByName)
                }
                self.isLoading = false
            }
        }
    }

    // O(1) lookup
    func museum(by id: String) -> Museum? { museumIndex[id]?.museum }

    // MARK: - #5: FavoritesView search — reuses pre-built searchBlob, no duplication
    func searchFavoriteMuseums(_ query: String) -> [Museum] {
        guard !query.isEmpty else { return favoriteMuseums }
        let normalized = PinyinHelper.normalizedQuery(query)
        let compact    = PinyinHelper.compactLetters(normalized)
        // Iterate favoriteIDs directly — avoids creating an intermediate [Museum] array
        return favoriteIDs.compactMap { id -> Museum? in
            guard let entry = museumIndex[id] else { return nil }
            let blob = entry.searchBlob
            guard blob.contains(normalized) || (!compact.isEmpty && blob.contains(compact)) else { return nil }
            return entry.museum
        }
    }

    // MARK: - Private helpers

    private func computeFiltered(
        museums: [Museum],
        query: String,
        category: MuseumCategory?,
        province: String?,
        sort: SortOption
    ) -> [Museum] {
        let normalizedQuery = PinyinHelper.normalizedQuery(query)
        let compactQuery    = PinyinHelper.compactLetters(normalizedQuery)

        let filtered = museums.filter { museum in
            let blob = museumIndex[museum.id]?.searchBlob ?? Self.searchBlob(for: museum)
            let matchesSearch = normalizedQuery.isEmpty ||
                blob.contains(normalizedQuery) ||
                (!compactQuery.isEmpty && blob.contains(compactQuery))
            let matchesCategory = category == nil || museum.category == category
            let matchesProvince = province == nil || museum.province == province
            return matchesSearch && matchesCategory && matchesProvince
        }

        return sorted(filtered, by: sort)
    }

    private func sorted(_ list: [Museum], by option: SortOption) -> [Museum] {
        switch option {
        case .nameAZ:
            return list.sorted { $0.name < $1.name }
        case .foundedOld:
            return list.sorted { ($0.founded ?? Int.max) < ($1.founded ?? Int.max) }
        case .foundedNew:
            return list.sorted { ($0.founded ?? 0) > ($1.founded ?? 0) }
        case .visitorsDesc:
            return list.sorted { ($0.annualVisitors ?? 0) > ($1.annualVisitors ?? 0) }
        case .freeFirst:
            return list.sorted {
                if $0.freeEntry != $1.freeEntry { return $0.freeEntry }
                return $0.name < $1.name
            }
        }
    }

    // #3 (precomputeStats): single-pass instead of 9 separate filter passes
    private func precomputeStats(for list: [Museum]) {
        var catCounts  = [MuseumCategory: Int]()
        var provCounts = [String: Int]()
        var withWebsite = 0, withAddress = 0, withFounded = 0
        var withLocation = 0, withEnglishName = 0
        var totalImages = 0, imagesWithCredit = 0, imagesWithLicense = 0

        for m in list {
            catCounts[m.category, default: 0]  += 1
            provCounts[m.province, default: 0] += 1
            if !(m.website ?? "").isEmpty               { withWebsite     += 1 }
            if !m.address.isEmpty                        { withAddress     += 1 }
            if m.founded != nil                          { withFounded     += 1 }
            if m.latitude != nil && m.longitude != nil   { withLocation    += 1 }
            if !m.englishName.isEmpty                    { withEnglishName += 1 }
            for img in m.images {
                totalImages += 1
                if !(img.credit  ?? "").trimmingCharacters(in: .whitespacesAndNewlines).isEmpty { imagesWithCredit  += 1 }
                if !(img.license ?? "").trimmingCharacters(in: .whitespacesAndNewlines).isEmpty { imagesWithLicense += 1 }
            }
        }

        categoryCounts = MuseumCategory.allCases.compactMap { cat in
            guard let count = catCounts[cat], count > 0 else { return nil }
            return (cat, count)
        }
        let sortedProvs = provCounts.keys.sorted()
        provinceCounts = sortedProvs.map { ($0, provCounts[$0] ?? 0) }
        provinces      = sortedProvs

        statsMuseumsWithWebsite     = withWebsite
        statsMuseumsWithAddress     = withAddress
        statsMuseumsWithFounded     = withFounded
        statsMuseumsWithLocation    = withLocation
        statsMuseumsWithEnglishName = withEnglishName
        statsTotalImages            = totalImages
        statsImagesWithCredit       = imagesWithCredit
        statsImagesWithLicense      = imagesWithLicense
    }

    private func toggle(_ id: String, in list: inout [String], knownInSet set: Set<String>) {
        if set.contains(id) { list.removeAll { $0 == id } }
        else { list.append(id) }
    }

    private static func migrateIfNeeded(from oldKey: String, to newKey: String) {
        guard UserDefaults.standard.data(forKey: newKey) == nil,
              let data = UserDefaults.standard.data(forKey: oldKey)
        else { return }
        UserDefaults.standard.set(data, forKey: newKey)
        UserDefaults.standard.removeObject(forKey: oldKey)
    }

    private static func loadIDs(forKey key: String) -> [String] {
        guard let data = UserDefaults.standard.data(forKey: key),
              let ids = try? JSONDecoder().decode([String].self, from: data)
        else { return [] }
        return ids
    }

    private func saveIDs(_ ids: [String], forKey key: String) {
        UserDefaults.standard.set(try? JSONEncoder().encode(ids), forKey: key)
    }

    private static func searchBlob(for museum: Museum) -> String {
        let texts = [
            museum.name, museum.englishName, museum.city,
            museum.province, museum.category.rawValue, museum.address, museum.summary,
        ] + museum.highlights
        return texts.map(PinyinHelper.searchBlob(for:)).joined(separator: " ")
    }
}
