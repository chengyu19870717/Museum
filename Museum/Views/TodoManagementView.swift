import SwiftUI

// MARK: - 数据模型

struct TodoItem: Identifiable, Codable, Equatable {
    var id: UUID
    var title: String
    var note: String
    var priority: Priority
    var isDone: Bool
    var createdAt: Date
    var dueDate: Date?

    init(
        id: UUID = UUID(),
        title: String,
        note: String = "",
        priority: Priority = .medium,
        isDone: Bool = false,
        createdAt: Date = Date(),
        dueDate: Date? = nil
    ) {
        self.id        = id
        self.title     = title
        self.note      = note
        self.priority  = priority
        self.isDone    = isDone
        self.createdAt = createdAt
        self.dueDate   = dueDate
    }

    enum Priority: String, Codable, CaseIterable {
        case high   = "高"
        case medium = "中"
        case low    = "低"

        var color: Color {
            switch self {
            case .high:   return .red
            case .medium: return .orange
            case .low:    return .blue
            }
        }

        var icon: String {
            switch self {
            case .high:   return "exclamationmark.3"
            case .medium: return "exclamationmark.2"
            case .low:    return "exclamationmark"
            }
        }

        var sortOrder: Int {
            switch self {
            case .high:   return 0
            case .medium: return 1
            case .low:    return 2
            }
        }
    }
}

// MARK: - 主视图

struct TodoManagementView: View {

    @AppStorage("todoItems") private var todosData: Data = Data()
    @State private var todos: [TodoItem] = []
    @State private var showAddSheet = false
    @State private var editingItem: TodoItem? = nil
    @State private var filterDone = false

    // #1: cached as @State so delete IndexSet stays aligned with displayed List rows
    @State private var filtered: [TodoItem] = []

    private func rebuildFiltered() {
        let sorted = todos.sorted {
            if $0.isDone != $1.isDone { return !$0.isDone }
            if $0.priority != $1.priority { return $0.priority.sortOrder < $1.priority.sortOrder }
            return $0.createdAt > $1.createdAt
        }
        filtered = filterDone ? sorted.filter(\.isDone) : sorted.filter { !$0.isDone }
    }

    var body: some View {
        // Single pass for both counts
        let doneCount    = todos.reduce(0) { $0 + ($1.isDone ? 1 : 0) }
        let pendingCount = todos.count - doneCount
        return VStack(spacing: 0) {
            Picker("", selection: $filterDone) {
                Text("待完成 (\(pendingCount))").tag(false)
                Text("已完成 (\(doneCount))").tag(true)
            }
            .pickerStyle(.segmented)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)

            if filtered.isEmpty {
                ContentUnavailableView(
                    filterDone ? "暂无已完成事项" : "暂无待办事项",
                    systemImage: filterDone ? "checkmark.circle" : "checklist",
                    description: Text(filterDone ? "完成事项后会出现在这里" : "点击右上角 + 添加第一条待办")
                )
            } else {
                List {
                    ForEach(filtered) { item in
                        TodoRowView(item: item,
                                    onToggle: { toggle(item) },
                                    onEdit:   { editingItem = item })
                    }
                    .onDelete(perform: delete)
                }
                .listStyle(.plain)
            }
        }
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button { showAddSheet = true } label: {
                    Image(systemName: "plus")
                }
            }
        }
        .sheet(isPresented: $showAddSheet) {
            TodoEditSheet(item: nil, onSave: add)
        }
        .sheet(item: $editingItem) { item in
            TodoEditSheet(item: item, onSave: update)
        }
        .onAppear(perform: load)
        .onChange(of: todos)      { rebuildFiltered() }
        .onChange(of: filterDone) { rebuildFiltered() }
    }

    // MARK: - 数据操作

    private func load() {
        todos = (try? JSONDecoder().decode([TodoItem].self, from: todosData)) ?? []
        rebuildFiltered()
    }

    private func save() {
        todosData = (try? JSONEncoder().encode(todos)) ?? Data()
    }

    private func add(_ item: TodoItem) {
        todos.insert(item, at: 0)
        save()
    }

    private func update(_ item: TodoItem) {
        if let idx = todos.firstIndex(where: { $0.id == item.id }) {
            todos[idx] = item
            save()
        }
    }

    private func toggle(_ item: TodoItem) {
        if let idx = todos.firstIndex(where: { $0.id == item.id }) {
            todos[idx].isDone.toggle()
            save()
        }
    }

    // #1: delete uses snapshot `filtered` that was stable at render time
    private func delete(at offsets: IndexSet) {
        let idsToRemove = Set(offsets.map { filtered[$0].id })
        todos.removeAll { idsToRemove.contains($0.id) }
        save()
    }
}

// MARK: - 列表行

private struct TodoRowView: View {
    let item: TodoItem
    let onToggle: () -> Void
    let onEdit: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            Button(action: onToggle) {
                Image(systemName: item.isDone ? "checkmark.circle.fill" : "circle")
                    .font(.title3)
                    .foregroundStyle(item.isDone ? .green : .secondary)
            }
            .buttonStyle(.plain)

            VStack(alignment: .leading, spacing: 3) {
                Text(item.title)
                    .font(.body)
                    .strikethrough(item.isDone, color: .secondary)
                    .foregroundStyle(item.isDone ? .secondary : .primary)
                    .lineLimit(1)

                HStack(spacing: 6) {
                    Label(item.priority.rawValue, systemImage: item.priority.icon)
                        .font(.caption2)
                        .foregroundStyle(item.priority.color)

                    if let due = item.dueDate {
                        Label(due.formatted(date: .abbreviated, time: .omitted),
                              systemImage: "calendar")
                            .font(.caption2)
                            .foregroundStyle(due < Date() && !item.isDone ? .red : .secondary)
                    }

                    if !item.note.isEmpty {
                        Label("有备注", systemImage: "text.bubble")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Spacer()

            Button(action: onEdit) {
                Image(systemName: "pencil.circle")
                    .foregroundStyle(.secondary)
            }
            .buttonStyle(.plain)
        }
        .padding(.vertical, 4)
        .contentShape(Rectangle())
    }
}

// MARK: - 添加 / 编辑 Sheet

struct TodoEditSheet: View {
    @Environment(\.dismiss) private var dismiss

    // nil 表示新建，有值表示编辑
    let item: TodoItem?
    let onSave: (TodoItem) -> Void

    @State private var title: String = ""
    @State private var note: String = ""
    @State private var priority: TodoItem.Priority = .medium
    @State private var hasDueDate = false
    @State private var dueDate: Date = Calendar.current.date(byAdding: .day, value: 1, to: Date()) ?? Date()

    var isEditing: Bool { item != nil }

    var body: some View {
        NavigationStack {
            Form {
                Section("事项内容") {
                    TextField("待办标题（必填）", text: $title)
                    TextField("备注（选填）", text: $note, axis: .vertical)
                        .lineLimit(3, reservesSpace: true)
                }

                Section("优先级") {
                    Picker("优先级", selection: $priority) {
                        ForEach(TodoItem.Priority.allCases, id: \.self) { p in
                            Label(p.rawValue, systemImage: p.icon)
                                .foregroundStyle(p.color)
                                .tag(p)
                        }
                    }
                    .pickerStyle(.segmented)
                }

                Section("截止日期") {
                    Toggle("设置截止日期", isOn: $hasDueDate)
                    if hasDueDate {
                        DatePicker("日期", selection: $dueDate, displayedComponents: .date)
                    }
                }
            }
            .navigationTitle(isEditing ? "编辑待办" : "新建待办")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("保存") { save() }
                        .disabled(title.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
            .onAppear { prefill() }
        }
    }

    private func prefill() {
        guard let item else { return }
        title = item.title
        note = item.note
        priority = item.priority
        if let due = item.dueDate {
            hasDueDate = true
            dueDate = due
        }
    }

    private func save() {
        var result = item ?? TodoItem(title: "")
        result.title = title.trimmingCharacters(in: .whitespaces)
        result.note = note
        result.priority = priority
        result.dueDate = hasDueDate ? dueDate : nil
        onSave(result)
        dismiss()
    }
}
