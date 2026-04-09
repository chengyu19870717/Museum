import SwiftUI

@main
struct MuseumApp: App {
    @StateObject private var store = MuseumStore()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(store)
        }
    }
}
