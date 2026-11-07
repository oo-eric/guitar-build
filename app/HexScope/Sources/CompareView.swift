import SwiftUI

/// Two captures side by side, per string, with the change from A to B coloured by whether it's better.
struct CompareView: View {
    @Environment(CaptureStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @State private var aID: UUID?
    @State private var bID: UUID?

    var body: some View {
        NavigationStack {
            let a = store.captures.first { $0.id == aID }
            let b = store.captures.first { $0.id == bID }
            List {
                Section {
                    picker("Before (A)", $aID)
                    picker("After (B)", $bID)
                }
                if let a, let b {
                    let sa = a.summary(), sb = b.summary()
                    ForEach(0..<max(sa.count, sb.count), id: \.self) { i in
                        Section {
                            Grid(alignment: .leading, horizontalSpacing: 12, verticalSpacing: 6) {
                                GridRow {
                                    Text("")
                                    Text("A").bold()
                                    Text("B").bold()
                                    Text("Δ").bold()
                                }
                                .font(.caption).foregroundStyle(.secondary)
                                ForEach(SummaryMetric.allCases) { m in
                                    row(m, sa[safe: i], sb[safe: i])
                                }
                            }
                        } header: {
                            StringHeader(index: i)
                        }
                    }
                }
            }
            .navigationTitle("Compare")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } }
            }
            .onAppear {
                // Default: previous capture vs. the newest.
                if aID == nil { aID = store.captures[safe: 1]?.id }
                if bID == nil { bID = store.captures[safe: 0]?.id }
            }
        }
        #if os(macOS)
        .frame(minWidth: 560, minHeight: 640)
        #endif
    }

    private func picker(_ title: String, _ sel: Binding<UUID?>) -> some View {
        Picker(title, selection: sel) {
            ForEach(store.captures) { c in
                Text("\(c.name) — \(c.startedAt.formatted(date: .numeric, time: .shortened))").tag(Optional(c.id))
            }
        }
    }

    @ViewBuilder
    private func row(_ m: SummaryMetric, _ a: StringSummary?, _ b: StringSummary?) -> some View {
        let va = a.flatMap(m.value), vb = b.flatMap(m.value)
        GridRow {
            Text(m.title).font(.caption)
            Text(a.map(m.format) ?? "—").font(.caption.monospacedDigit())
            Text(b.map(m.format) ?? "—").font(.caption.monospacedDigit())
            if let va, let vb {
                let d = vb - va
                Text(m.deltaText(d))
                    .font(.caption.monospacedDigit().bold())
                    .foregroundStyle(color(m, d))
            } else {
                Text("")
            }
        }
    }

    private func color(_ m: SummaryMetric, _ d: Double) -> Color {
        guard m.better != 0, abs(d) > 0.5 else { return .secondary }
        return (d > 0) == (m.better > 0) ? .green : .red
    }
}
