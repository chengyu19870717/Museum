import SwiftUI

struct FilterView: View {
    @EnvironmentObject var store: MuseumStore
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section("按类别筛选") {
                    ForEach(MuseumCategory.allCases, id: \.self) { cat in
                        Button {
                            store.selectedCategory = store.selectedCategory == cat ? nil : cat
                        } label: {
                            HStack {
                                Text(cat.rawValue)
                                    .foregroundStyle(.primary)
                                Spacer()
                                if store.selectedCategory == cat {
                                    Image(systemName: "checkmark")
                                        .foregroundStyle(.blue)
                                }
                            }
                        }
                    }
                }

                Section("按省份筛选") {
                    ForEach(store.provinces, id: \.self) { prov in
                        Button {
                            store.selectedProvince = store.selectedProvince == prov ? nil : prov
                        } label: {
                            HStack {
                                Text(prov)
                                    .foregroundStyle(.primary)
                                Spacer()
                                if store.selectedProvince == prov {
                                    Image(systemName: "checkmark")
                                        .foregroundStyle(.blue)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("筛选")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("重置") {
                        store.selectedCategory = nil
                        store.selectedProvince = nil
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("完成") { dismiss() }
                        .bold()
                }
            }
        }
    }
}
