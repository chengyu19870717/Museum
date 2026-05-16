import SwiftUI

struct JourneyStatsView: View {
    @EnvironmentObject var store: MuseumStore

    var body: some View {
        let visited = store.visitedMuseums
        Group {
            if visited.isEmpty {
                ContentUnavailableView(
                    "还没有打卡记录",
                    systemImage: "mappin.slash",
                    description: Text("进入博物馆详情页，点击旗帜图标即可打卡")
                )
            } else {
                List {
                    Section {
                        statsGrid(visited: visited)
                    }
                    Section("已打卡（\(visited.count) 家）") {
                        ForEach(visited) { museum in
                            NavigationLink {
                                MuseumDetailView(museum: museum)
                            } label: {
                                MuseumRowView(museum: museum, isVisited: true)
                            }
                            .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                                Button(role: .destructive) {
                                    store.toggleVisited(museum.id)
                                } label: {
                                    Label("取消打卡", systemImage: "mappin.slash")
                                }
                            }
                        }
                    }
                }
                .listStyle(.plain)
            }
        }
    }

    private func statsGrid(visited: [Museum]) -> some View {
        let stats      = store.visitedStats()
        let provinces  = stats.provinces.count
        let categories = stats.categories.count
        return LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
            JourneyStatCard(value: "\(visited.count)",         label: "已打卡", icon: "mappin.circle.fill", color: .green)
            JourneyStatCard(value: "\(store.favoriteIDsCount)", label: "已收藏", icon: "heart.fill",        color: .red)
            JourneyStatCard(value: "\(provinces)",             label: "涵盖省份", icon: "map.fill",         color: .blue)
            JourneyStatCard(value: "\(categories)",            label: "涵盖类别", icon: "tag.fill",         color: .purple)
        }
        .padding(.vertical, 4)
    }
}

private struct JourneyStatCard: View {
    let value: String
    let label: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon).font(.title2).foregroundStyle(color)
            Text(value).font(.title.bold())
            Text(label).font(.caption).foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(color.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}
