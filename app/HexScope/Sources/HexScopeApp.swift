import SwiftUI

@main
struct HexScopeApp: App {
    @State private var model = GuitarModel()
    @State private var store = CaptureStore()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(model)
                .environment(store)
                .task { model.start() }
        }
        #if os(macOS)
        .defaultSize(width: 1100, height: 820)
        #endif
    }
}

struct RootView: View {
    var body: some View {
        TabView {
            Tab("Live", systemImage: "waveform") { LiveView() }
            Tab("Captures", systemImage: "square.stack.3d.up") { CapturesView() }
        }
    }
}
