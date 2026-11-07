import SwiftUI

struct LiveView: View {
    @Environment(GuitarModel.self) private var model
    @Environment(CaptureStore.self) private var store
    @State private var pending: Capture?
    @State private var showLog = false

    var body: some View {
        @Bindable var model = model
        NavigationStack {
            ScrollView {
                VStack(spacing: 12) {
                    TimelineView(.periodic(from: .now, by: 0.5)) { ctx in
                        StatusBanner(state: model.linkState(now: ctx.date))
                    }
                    if model.reportedStrings > 0 && model.reportedStrings < 6 && !model.demo {
                        Label("Firmware is reporting \(model.reportedStrings) of 6 strings — NUM_STRINGS in config.h",
                              systemImage: "exclamationmark.triangle")
                            .font(.footnote).foregroundStyle(.orange)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    Overview(strings: model.strings, config: model.config)
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 330), spacing: 12)], spacing: 12) {
                        ForEach(model.strings, id: \.info.id) { s in
                            StringCard(string: s, config: model.config)
                        }
                    }
                    if showLog { EventLog(events: model.log) }
                }
                .padding()
            }
            .background(Color.pageBackground)
            .navigationTitle("HexScope")
            .toolbar {
                ToolbarItem(placement: .primaryAction) { RecordButton(pending: $pending) }
                ToolbarItem(placement: .secondaryAction) {
                    Menu {
                        Toggle("Demo data", isOn: $model.demo)
                        Toggle("Event log", isOn: $showLog)
                        Button("Reset counters") { model.resetCounters() }
                    } label: { Label("Options", systemImage: "ellipsis.circle") }
                }
            }
            .sheet(item: $pending) { capture in
                SaveCaptureSheet(capture: capture) { saved in
                    if let saved { try? store.save(saved) }
                    pending = nil
                }
            }
        }
    }
}

// MARK: - Header

struct StatusBanner: View {
    let state: LinkState
    @Environment(GuitarModel.self) private var model

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 10) {
            Circle().fill(color).frame(width: 10, height: 10)
            VStack(alignment: .leading, spacing: 2) {
                HStack {
                    Text(state.title).font(.headline)
                    if state == .live || state == .demo {
                        Text(String(format: "%.0f fps", model.frameRate))
                            .font(.caption.monospacedDigit()).foregroundStyle(.secondary)
                        if model.configFromDevice {
                            Text(String(format: "onset %.3f · off %.3f", model.config.onsetThreshold, model.config.offsetThreshold))
                                .font(.caption.monospacedDigit()).foregroundStyle(.secondary)
                        }
                    }
                }
                if state != .live {
                    Text(state.detail).font(.caption).foregroundStyle(.secondary)
                }
                if let e = model.midiError { Text(e).font(.caption).foregroundStyle(.red) }
            }
            Spacer()
        }
        .padding(12)
        .background(Color.cardBackground, in: RoundedRectangle(cornerRadius: 12))
    }

    private var color: Color {
        switch state {
        case .live: .green
        case .demo: .purple
        case .midiOnly: .orange
        case .noDevice: .gray
        }
    }
}

struct RecordButton: View {
    @Environment(GuitarModel.self) private var model
    @Binding var pending: Capture?

    var body: some View {
        if model.isRecording {
            TimelineView(.periodic(from: .now, by: 0.25)) { _ in
                Button {
                    pending = model.stopRecording()
                } label: {
                    Label(elapsed, systemImage: "stop.circle.fill")
                        .labelStyle(.titleAndIcon)
                        .foregroundStyle(.red)
                        .monospacedDigit()
                }
            }
        } else {
            Button { model.startRecording() } label: {
                Label("Record", systemImage: "record.circle")
                    .labelStyle(.titleAndIcon)
            }
        }
    }

    private var elapsed: String {
        let t = Int(model.recorderElapsed)
        return String(format: "%d:%02d", t / 60, t % 60)
    }
}

extension GuitarModel {
    var recorderElapsed: TimeInterval { recorder?.elapsed ?? 0 }
}

struct SaveCaptureSheet: View {
    let capture: Capture
    let done: (Capture?) -> Void
    @State private var name = ""
    @State private var notes = ""

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Name", text: $name, prompt: Text("e.g. G pickup raised 1mm"))
                    TextField("Notes", text: $notes, prompt: Text("What changed since last time?"), axis: .vertical)
                        .lineLimit(3...8)
                }
                Section {
                    LabeledContent("Length", value: String(format: "%.1f s", capture.duration))
                    LabeledContent("Frames", value: "\(capture.frames.count)")
                    LabeledContent("Notes played", value: "\(capture.events.filter(\.on).count)")
                }
                if capture.frames.isEmpty {
                    Text("No telemetry arrived while recording — nothing to compare later.")
                        .foregroundStyle(.orange)
                }
            }
            .formStyle(.grouped)
            .navigationTitle("Save capture")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Discard", role: .destructive) { done(nil) } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        var c = capture
                        c.name = name.trimmingCharacters(in: .whitespaces).isEmpty
                            ? capture.startedAt.formatted(date: .abbreviated, time: .shortened) : name
                        c.notes = notes
                        done(c)
                    }
                }
            }
        }
        #if os(macOS)
        .frame(minWidth: 420, minHeight: 360)
        #endif
    }
}

struct EventLog: View {
    let events: [LogEvent]

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Events").font(.headline)
            if events.isEmpty { Text("Nothing yet").foregroundStyle(.secondary).font(.caption) }
            ForEach(events.prefix(40)) { e in
                HStack {
                    Text(e.at.formatted(.dateTime.hour().minute().second()))
                        .foregroundStyle(.secondary)
                    Text("S\(e.string + 1)").bold().foregroundStyle(Color.string(e.string))
                    Text(e.text)
                    Spacer()
                }
                .font(.caption.monospacedDigit())
            }
        }
        .padding(12)
        .background(Color.cardBackground, in: RoundedRectangle(cornerRadius: 12))
    }
}

extension Color {
    static func string(_ i: Int) -> Color {
        [Color.red, .orange, .yellow, .green, .cyan, .indigo][i % 6]
    }

    static var cardBackground: Color {
        #if os(iOS)
        Color(uiColor: .secondarySystemGroupedBackground)
        #else
        Color(nsColor: .controlBackgroundColor)
        #endif
    }

    static var pageBackground: Color {
        #if os(iOS)
        Color(uiColor: .systemGroupedBackground)
        #else
        Color(nsColor: .windowBackgroundColor)
        #endif
    }
}

/// All six strings at a glance: vertical level bars with the onset threshold, plus the current note.
struct Overview: View {
    let strings: [LiveString]
    let config: DeviceConfig

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            ForEach(strings, id: \.info.id) { s in
                VStack(spacing: 4) {
                    Text(noteText(s)).font(.caption.bold().monospacedDigit())
                        .foregroundStyle(active(s) ? .primary : .tertiary)
                        .lineLimit(1).minimumScaleFactor(0.6)
                    GeometryReader { g in
                        let h = g.size.height
                        ZStack(alignment: .bottom) {
                            RoundedRectangle(cornerRadius: 4).fill(.quaternary)
                            RoundedRectangle(cornerRadius: 4).fill(Color.string(s.info.index).gradient)
                                .frame(height: max(2, frac(s.status?.onsetRMS ?? 0) * h))
                            Rectangle().fill(.primary).frame(height: 2)
                                .offset(y: -frac(config.onsetThreshold) * h + 1)
                            if s.status?.isClipping == true {
                                Rectangle().fill(.red).frame(height: 4).frame(maxHeight: .infinity, alignment: .top)
                            }
                        }
                    }
                    .frame(height: 70)
                    Text("\(s.info.number)").font(.caption2.bold()).foregroundStyle(Color.string(s.info.index))
                    Text(s.info.name).font(.caption2).foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity)
            }
        }
        .padding(12)
        .background(Color.cardBackground, in: RoundedRectangle(cornerRadius: 12))
    }

    private func active(_ s: LiveString) -> Bool { (s.status?.state ?? .idle) != .idle }

    private func noteText(_ s: LiveString) -> String {
        guard let st = s.status, st.state != .idle, let n = Pitch.nearest(st.frequency) else { return "·" }
        return Pitch.noteName(n.note)
    }

    private func frac(_ v: Double) -> CGFloat {
        CGFloat((Level.dB(v) - Level.floor) / -Level.floor).clamped(0, 1)
    }
}
