import SwiftUI

struct FilterView: View {
    @EnvironmentObject var store: MuseumStore
    @Environment(\.dismiss) var dismiss
    // #3: province search
    @State private var provinceQuery = ""

    private var filteredProvinces: [(province: String, count: Int)] {
        guard !provinceQuery.isEmpty else { return store.provinceCounts }
        let q = provinceQuery.lowercased()
        return store.provinceCounts.filter { $0.province.lowercased().contains(q) }
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("排序方式") {
                    ForEach(SortOption.allCases) { option in
                        Button {
                            store.sortOption = option
                        } label: {
                            HStack {
                                Text(option.rawValue).foregroundStyle(.primary)
                                Spacer()
                                if store.sortOption == option {
                                    Image(systemName: "checkmark").foregroundStyle(.blue)
                                }
                            }
                        }
                    }
                }

                Section("按类别筛选") {
                    if store.categoryCounts.count <= 1 {
                        ContentUnavailableView(
                            "分类待细化",
                            systemImage: "tag",
                            description: Text("当前数据暂未形成有效分类，后续补齐后这里会自动显示可筛选类别。")
                        )
                    } else {
                        ForEach(store.categoryCounts, id: \.category) { item in
                            Button {
                                store.selectedCategory = store.selectedCategory == item.category ? nil : item.category
                            } label: {
                                HStack {
                                    Text(item.category.rawValue).foregroundStyle(.primary)
                                    Spacer()
                                    Text("\(item.count)").font(.caption).foregroundStyle(.secondary)
                                    if store.selectedCategory == item.category {
                                        Image(systemName: "checkmark").foregroundStyle(.blue)
                                    }
                                }
                            }
                        }
                    }
                }

                // #3: searchable province list
                Section("按省份筛选") {
                    if !store.provinceCounts.isEmpty {
                        HStack {
                            Image(systemName: "magnifyingglass").foregroundStyle(.secondary)
                            TextField("搜索省份", text: $provinceQuery)
                                .autocorrectionDisabled()
                        }
                    }
                    ForEach(filteredProvinces, id: \.province) { item in
                        Button {
                            store.selectedProvince = store.selectedProvince == item.province ? nil : item.province
                        } label: {
                            HStack {
                                Text(item.province).foregroundStyle(.primary)
                                Spacer()
                                Text("\(item.count)").font(.caption).foregroundStyle(.secondary)
                                if store.selectedProvince == item.province {
                                    Image(systemName: "checkmark").foregroundStyle(.blue)
                                }
                            }
                        }
                    }
                    if filteredProvinces.isEmpty && !provinceQuery.isEmpty {
                        Text("无匹配省份").foregroundStyle(.secondary).font(.caption)
                    }
                }
            }
            .navigationTitle("筛选")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("重置") {
                        store.selectedCategory = nil
                        store.selectedProvince = nil
                        store.sortOption = .nameAZ
                        provinceQuery = ""
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("完成") { dismiss() }.bold()
                }
            }
        }
    }
}
