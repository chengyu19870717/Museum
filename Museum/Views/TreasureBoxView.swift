import SwiftUI

// MARK: - 功能入口定义

struct FeatureEntry: Identifiable {
    let id = UUID()
    let name: String       // 用于去重的唯一标识（名称相同视为重复）
    let icon: String
    let content: AnyView

    init(name: String, icon: String, @ViewBuilder content: () -> some View) {
        self.name    = name
        self.icon    = icon
        self.content = AnyView(content())
    }
}

// MARK: - 百宝箱主视图

struct TreasureBoxView: View {

    /// 所有注册的功能入口（名称相同的条目只保留第一个）
    private var features: [FeatureEntry] {
        [
            FeatureEntry(name: "待办管理", icon: "checklist") { TodoManagementView() },
            FeatureEntry(name: "关于", icon: "info.circle")   { AboutView() },
        ]
    }

    @State private var selectedName: String = "待办管理"

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // 水平页签栏（仅显示去重后的功能）
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(features) { feature in
                            TabPill(
                                title: feature.name,
                                icon:  feature.icon,
                                isSelected: selectedName == feature.name
                            )
                            .onTapGesture { selectedName = feature.name }
                        }
                    }
                    .padding(.horizontal, 16)
                }
                .padding(.vertical, 10)

                Divider()

                // 当前选中功能的内容
                if let current = features.first(where: { $0.name == selectedName }) {
                    current.content
                }
            }
            .navigationTitle("程钰的百宝箱")
            .navigationBarTitleDisplayMode(.inline)
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

