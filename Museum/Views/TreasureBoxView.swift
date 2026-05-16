import SwiftUI

// MARK: - Feature tabs

private enum FeatureTab: String, CaseIterable, Identifiable {
    case journey  = "我的旅程"
    case todo     = "待办管理"
    case about    = "关于"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .journey: return "mappin.circle.fill"
        case .todo:    return "checklist"
        case .about:   return "info.circle"
        }
    }
}

// MARK: - 百宝箱主视图

struct TreasureBoxView: View {
    @State private var selected: FeatureTab = .journey

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(FeatureTab.allCases) { tab in
                            TabPill(title: tab.rawValue, icon: tab.icon, isSelected: selected == tab)
                                .onTapGesture { selected = tab }
                        }
                    }
                    .padding(.horizontal, 16)
                }
                .padding(.vertical, 10)

                Divider()

                featureContent
            }
            .navigationTitle("我的空间")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    @ViewBuilder
    private var featureContent: some View {
        switch selected {
        case .journey: JourneyStatsView()
        case .todo:    TodoManagementView()
        case .about:   AboutView()
        }
    }
}

// MARK: - 页签胶囊

private struct TabPill: View {
    let title: String
    let icon: String
    let isSelected: Bool

    var body: some View {
        HStack(spacing: 5) {
            Image(systemName: icon).font(.caption)
            Text(title).font(.subheadline)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 7)
        .background(isSelected ? Color.accentColor : Color.primary.opacity(0.08))
        .foregroundStyle(isSelected ? Color.white : Color.primary)
        .clipShape(Capsule())
        .animation(.easeInOut(duration: 0.18), value: isSelected)
    }
}
