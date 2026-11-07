import SwiftUI

struct CapturesView: View {
    @Environment(CaptureStore.self) private var store
    @State private var comparing = false

    var body: some View {
        NavigationStack {
            List {
                if let e = store.loadError { Text(e).foregroundStyle(.orange) }
                if store.captures.isEmpty {
                    ContentUnavailableView("No captures", systemImage: "record.circle",
                                           description: Text("Hit Record on the Live tab, play each string, then stop and save."))
                }
                ForEach(store.captures) { c in
                    NavigationLink(value: c) { CaptureRow(capture: c) }
                        .contextMenu {
                            ShareLink(item: store.url(for: c))
                            Button("Delete", role: .destructive) { store.delete(c) }
                        }
                }
                .onDelete { idx in idx.map { store.captures[$0] }.forEach(store.delete) }
            }
            .navigationTitle("Captures")
            .navigationDestination(for: Capture.self) { CaptureDetail(capture: $0) }
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button { comparing = true } label: { Label("Compare", systemImage: "arrow.left.arrow.right") }
                        .disabled(store.captures.count < 2)
                }
            }
            .sheet(isPresented: $comparing) { CompareView() }
            .refreshable { store.reload() }
        }
    }
}

struct CaptureRow: View {
    let capture: Capture
    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(capture.name).font(.headline)
            HStack {
                Text(capture.startedAt.formatted(date: .abbreviated, time: .shortened))
                Text(String(format: "%.0f s", capture.duration))
                Text("\(capture.events.filter(\.on).count) notes")
            }
            .font(.caption).foregroundStyle(.secondary)
            if !capture.notes.isEmpty {
                Text(capture.notes).font(.caption).lineLimit(2).foregroundStyle(.secondary)
            }
        }
    }
}

struct CaptureDetail: View {
    let capture: Capture
    @Environment(CaptureStore.self) private var store

    var body: some View {
        let sums = capture.summary()
        List {
            Section {
                LabeledContent("Recorded", value: capture.startedAt.formatted(date: .abbreviated, time: .standard))
                LabeledContent("Length", value: String(format: "%.1f s · %d frames", capture.duration, capture.frames.count))
                LabeledContent("Thresholds", value: String(format: "onset %.3f · off %.3f", capture.config.onsetThreshold, capture.config.offsetThreshold))
                if !capture.notes.isEmpty { Text(capture.notes) }
            }
            ForEach(Array(sums.enumerated()), id: \.offset) { i, s in
                Section {
                    SummaryRows(summary: s)
                } header: {
                    StringHeader(index: i)
                }
            }
        }
        .navigationTitle(capture.name)
        .toolbar {
            ToolbarItem { ShareLink(item: store.url(for: capture)) }
        }
    }
}

struct StringHeader: View {
    let index: Int
    var body: some View {
        let s = GuitarString.all[safe: index]
        HStack {
            Text("String \(index + 1)").foregroundStyle(Color.string(index))
            if let s { Text(s.name) }
        }
        .font(.headline)
    }
}

struct SummaryRows: View {
    let summary: StringSummary
    var body: some View {
        ForEach(SummaryMetric.allCases) { m in
            LabeledContent(m.title, value: m.format(summary))
        }
        if !summary.notes.isEmpty {
            LabeledContent("Notes", value: summary.notes.map(Pitch.noteName).joined(separator: " "))
        }
    }
}

/// The per-string numbers shown in a capture and compared between two.
enum SummaryMetric: String, CaseIterable, Identifiable {
    case floor, peak, snr, bleed, dc, clip, onsets, noteOns, confidence
    var id: String { rawValue }

    var title: String {
        switch self {
        case .floor: "Idle noise"
        case .peak: "Pluck peak"
        case .snr: "Peak / noise"
        case .bleed: "Worst bleed"
        case .dc: "Bias offset"
        case .clip: "Clipped frames"
        case .onsets: "Onsets"
        case .noteOns: "MIDI notes"
        case .confidence: "Pitch confidence"
        }
    }

    /// Value used for deltas. nil when the capture can't say.
    func value(_ s: StringSummary) -> Double? {
        switch self {
        case .floor: s.idleFloor.map(Level.dB)
        case .peak: Level.dB(s.peak)
        case .snr: s.snrDB
        case .bleed: s.bleed?.dB
        case .dc: s.meanDC
        case .clip: Double(s.clipFrames)
        case .onsets: Double(s.onsets)
        case .noteOns: Double(s.noteOns)
        case .confidence: s.confidence.map { $0 * 100 }
        }
    }

    func format(_ s: StringSummary) -> String {
        guard let v = value(s) else { return "—" }
        switch self {
        case .floor, .peak: return String(format: "%.1f dBFS", v)
        case .snr: return String(format: "%.1f dB", v)
        case .bleed: return String(format: "%.1f dB → S%d", v, (s.bleed?.string ?? 0) + 1)
        case .dc: return String(format: "%+.0f ct", v)
        case .clip, .onsets, .noteOns: return String(format: "%.0f", v)
        case .confidence: return String(format: "%.0f%%", v)
        }
    }

    /// +1 if a higher number is an improvement, -1 if lower is, 0 if neither (counts depend on what you played).
    var better: Int {
        switch self {
        case .peak, .snr, .confidence: 1
        case .floor, .bleed, .clip: -1
        case .dc, .onsets, .noteOns: 0
        }
    }

    func deltaText(_ d: Double) -> String {
        switch self {
        case .floor, .peak, .snr, .bleed: String(format: "%+.1f", d)
        case .confidence: String(format: "%+.0f%%", d)
        default: String(format: "%+.0f", d)
        }
    }
}

extension Array {
    subscript(safe i: Int) -> Element? { indices.contains(i) ? self[i] : nil }
}
