import SwiftUI

struct ImageGalleryView: View {
    let museum: Museum
    @Binding var selectedIndex: Int
    @Binding var showFull: Bool

    var body: some View {
        ZStack(alignment: .bottom) {
            TabView(selection: $selectedIndex) {
                ForEach(Array(museum.images.enumerated()), id: \.offset) { index, img in
                    MuseumImageView(museumID: museum.id, image: img)
                        .tag(index)
                        .onTapGesture { showFull = true }
                }
            }
            .tabViewStyle(.page(indexDisplayMode: .never))

            // 指示器 + 说明文字
            VStack(spacing: 4) {
                if !museum.images.isEmpty {
                    let img = museum.images[selectedIndex]
                    Text(img.caption)
                        .font(.caption)
                        .foregroundStyle(.white)
                        .shadow(radius: 2)
                        .padding(.horizontal)
                }
                HStack(spacing: 6) {
                    ForEach(museum.images.indices, id: \.self) { i in
                        Circle()
                            .fill(i == selectedIndex ? Color.white : Color.white.opacity(0.5))
                            .frame(width: i == selectedIndex ? 8 : 6, height: i == selectedIndex ? 8 : 6)
                    }
                }
                .padding(.bottom, 12)
            }
            .background(
                LinearGradient(
                    colors: [.clear, .black.opacity(0.5)],
                    startPoint: .top,
                    endPoint: .bottom
                )
            )
        }
    }
}

struct MuseumThumbnailView: View {
    let museum: Museum

    var body: some View {
        if let firstImage = museum.images.first {
            MuseumImageView(museumID: museum.id, image: firstImage)
        } else {
            Image(systemName: "building.columns.fill")
                .resizable()
                .scaledToFit()
                .foregroundStyle(.gray.opacity(0.4))
                .padding(12)
                .background(Color.gray.opacity(0.1))
        }
    }
}

struct MuseumImageView: View {
    let museumID: String
    let image: MuseumImage

    var body: some View {
        if let url = MuseumDataLoader.imageURL(museumID: museumID, filename: image.filename) {
            AsyncImage(url: url) { phase in
                switch phase {
                case .success(let img):
                    img.resizable().scaledToFill()
                case .failure:
                    placeholderImage
                default:
                    ProgressView()
                }
            }
        } else {
            placeholderImage
        }
    }

    var placeholderImage: some View {
        Image(systemName: "building.columns")
            .resizable()
            .scaledToFit()
            .foregroundStyle(.gray.opacity(0.3))
            .background(Color.gray.opacity(0.08))
    }
}

struct FullGalleryView: View {
    let museum: Museum
    let initialIndex: Int
    @Environment(\.dismiss) var dismiss
    @State private var currentIndex: Int

    init(museum: Museum, initialIndex: Int) {
        self.museum = museum
        self.initialIndex = initialIndex
        self._currentIndex = State(initialValue: initialIndex)
    }

    var body: some View {
        NavigationStack {
            TabView(selection: $currentIndex) {
                ForEach(Array(museum.images.enumerated()), id: \.offset) { index, img in
                    VStack {
                        MuseumImageView(museumID: museum.id, image: img)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                            .padding()
                        VStack(spacing: 4) {
                            Text(img.caption)
                                .font(.headline)
                            if let credit = img.credit {
                                Text("摄影：\(credit)")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            if let license = img.license {
                                Text(license)
                                    .font(.caption2)
                                    .foregroundStyle(.tertiary)
                            }
                        }
                        .padding(.horizontal)
                    }
                    .tag(index)
                }
            }
            .tabViewStyle(.page)
            .navigationTitle("\(currentIndex + 1) / \(museum.images.count)")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("关闭") { dismiss() }
                }
            }
        }
    }
}
