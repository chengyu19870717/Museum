import Foundation

@MainActor
class MuseumStore: ObservableObject {
    @Published var museums: [Museum] = []
    @Published var isLoading = false
    @Published var searchText = ""
    @Published var selectedCategory: MuseumCategory? = nil
    @Published var selectedProvince: String? = nil

    // MARK: - 收藏管理
    private let favoritesKey = "favoriteMuseumIDs"

    private var favoriteIDs: [String] {
        guard let data = UserDefaults.standard.data(forKey: favoritesKey),
              let ids = try? JSONDecoder().decode([String].self, from: data)
        else { return [] }
        return ids
    }

    var favoriteMuseums: [Museum] {
        favoriteIDs.compactMap { museum(by: $0) }
    }

    func isFavorite(_ museumID: String) -> Bool {
        favoriteIDs.contains(museumID)
    }

    func toggleFavorite(_ museumID: String) {
        var ids = favoriteIDs
        if ids.contains(museumID) {
            ids.removeAll { $0 == museumID }
        } else {
            ids.append(museumID)
        }
        let data = (try? JSONEncoder().encode(ids)) ?? Data()
        UserDefaults.standard.set(data, forKey: favoritesKey)
        objectWillChange.send()
    }

    var filteredMuseums: [Museum] {
        museums.filter { museum in
            let matchesSearch = searchText.isEmpty ||
                PinyinHelper.matches(museum.name, query: searchText) ||
                PinyinHelper.matches(museum.city, query: searchText) ||
                PinyinHelper.matches(museum.province, query: searchText) ||
                PinyinHelper.matches(museum.summary, query: searchText) ||
                PinyinHelper.matches(museum.englishName, query: searchText) ||
                museum.highlights.contains { PinyinHelper.matches($0, query: searchText) }
            let matchesCategory = selectedCategory == nil || museum.category == selectedCategory
            let matchesProvince = selectedProvince == nil || museum.province == selectedProvince
            return matchesSearch && matchesCategory && matchesProvince
        }
    }

    var provinces: [String] {
        Array(Set(museums.map(\.province))).sorted()
    }

    /// Load museum data asynchronously on a background thread
    func load() {
        guard !isLoading else { return }
        isLoading = true

        Task.detached(priority: .userInitiated) {
            let loaded = MuseumDataLoader.loadAll()
            let sorted = loaded.sorted { $0.name < $1.name }

            await MainActor.run {
                self.museums = sorted
                self.isLoading = false
            }
        }
    }

    func museum(by id: String) -> Museum? {
        museums.first { $0.id == id }
    }
}