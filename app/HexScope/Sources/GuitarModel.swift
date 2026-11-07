import Foundation
import Observation
import CoreMIDI

struct LiveString {
    let info: GuitarString
    var status: StringStatus?
    var updatedAt: Date?
    /// Onset RMS in dBFS, oldest first.
    var history: [Double] = []
    var scope: ScopeFrame?
    var peakHold = 0.0
    var peakHoldAt = Date.distantPast
    var noteOns = 0
    var lastNote = 0
    var lastVelocity = 0
    var lastNoteAt: Date?
}

struct LogEvent: Identifiable {
    let id = UUID()
    let at: Date
    let string: Int
    let text: String
}

enum LinkState: Equatable {
    case demo, live, midiOnly(String), noDevice

    var title: String {
        switch self {
        case .demo: "Demo data"
        case .live: "Live"
        case .midiOnly: "No telemetry"
        case .noDevice: "No Teensy"
        }
    }

    var detail: String {
        switch self {
        case .demo: "Synthetic guitar — turn off in the menu to use the Teensy."
        case .live: "Receiving diagnostics from the Teensy."
        case .midiOnly(let name): "\(name) is connected but sending no diagnostics. Flash the firmware with telemetry.cpp, USB Type “Serial + MIDI”."
        case .noDevice: "Connect the Teensy’s USB port. On iPhone/iPad use a USB-C to micro-USB cable."
        }
    }
}

@MainActor @Observable
final class GuitarModel {
    static let historyLength = 120 // 6 s at 20 Hz

    var strings = GuitarString.all.map { LiveString(info: $0) }
    var config = DeviceConfig.defaults
    var configFromDevice = false
    var sources: [MIDIConnection.Source] = []
    var telemetrySource: MIDIUniqueID?
    var lastFrameAt: Date?
    var frameRate = 0.0
    var reportedStrings = 0
    var log: [LogEvent] = []
    private(set) var recorder: CaptureRecorder?
    var midiError: String?

    var demo = false {
        didSet {
            guard demo != oldValue else { return }
            resetLive()
            if demo { demoGuitar.start { [weak self] e in self?.handle(e) } } else { demoGuitar.stop() }
        }
    }

    @ObservationIgnored private let midi = MIDIConnection()
    @ObservationIgnored private let demoGuitar = DemoGuitar()

    func start() {
        midi.onEvent = { [weak self] e in MainActor.assumeIsolated { if self?.demo == false { self?.handle(e) } } }
        midi.onSourcesChanged = { [weak self] s in MainActor.assumeIsolated { self?.sources = s } }
        midi.start()
        midiError = midi.startError
        if ProcessInfo.processInfo.arguments.contains("-demo") { demo = true }
    }

    func linkState(now: Date) -> LinkState {
        if demo { return .demo }
        if let t = lastFrameAt, now.timeIntervalSince(t) < 1.5 { return .live }
        let teensy = sources.first { $0.name.localizedCaseInsensitiveContains("teensy") }
        if let teensy { return .midiOnly(teensy.name) }
        return .noDevice
    }

    // MARK: - Recording

    var isRecording: Bool { recorder != nil }

    func startRecording() {
        recorder = CaptureRecorder(config: config)
    }

    /// Stops recording and returns the capture for the caller to name and save.
    func stopRecording(name: String = "", notes: String = "") -> Capture? {
        defer { recorder = nil }
        return recorder?.finish(name: name, notes: notes)
    }

    func resetCounters() {
        for i in strings.indices {
            strings[i].noteOns = 0
            strings[i].peakHold = 0
        }
        log.removeAll()
    }

    // MARK: - Ingest

    func handle(_ event: MIDIConnection.Event) {
        switch event {
        case .telemetry(let m, let src):
            telemetrySource = src
            ingest(m)
        case .noteOn(let ch, let note, let vel, let src):
            guard acceptNotes(from: src), let s = config.channels.firstIndex(of: ch), strings.indices.contains(s) else { return }
            strings[s].noteOns += 1
            strings[s].lastNote = note
            strings[s].lastVelocity = vel
            strings[s].lastNoteAt = Date()
            recorder?.add(string: s, on: true, note: note, velocity: vel)
            appendLog(s, "note on \(Pitch.noteName(note)) vel \(vel)")
        case .noteOff(let ch, let note, let src):
            guard acceptNotes(from: src), let s = config.channels.firstIndex(of: ch), strings.indices.contains(s) else { return }
            recorder?.add(string: s, on: false, note: note, velocity: 0)
        }
    }

    /// Note events only count from the device that's sending telemetry, so a keyboard
    /// plugged into the Mac doesn't show up as string activity.
    private func acceptNotes(from src: MIDIUniqueID) -> Bool {
        telemetrySource == nil || telemetrySource == src
    }

    private func ingest(_ m: TelemetryMessage) {
        let now = Date()
        switch m {
        case .config(let c):
            config = c
            configFromDevice = true
        case .scope(let f):
            guard strings.indices.contains(f.string) else { return }
            strings[f.string].scope = f
        case .status(let frame):
            if let last = lastFrameAt {
                let dt = now.timeIntervalSince(last)
                if dt > 0 { frameRate = frameRate == 0 ? 1 / dt : frameRate * 0.9 + 0.1 / dt }
            }
            lastFrameAt = now
            reportedStrings = frame.strings.count
            for (i, s) in frame.strings.enumerated() where strings.indices.contains(i) {
                let previous = strings[i].status?.state
                let wasClipping = strings[i].status?.isClipping ?? false
                strings[i].status = s
                strings[i].updatedAt = now
                strings[i].history.append(Level.dB(s.onsetRMS))
                if strings[i].history.count > Self.historyLength {
                    strings[i].history.removeFirst(strings[i].history.count - Self.historyLength)
                }
                if s.onsetRMS >= strings[i].peakHold || now.timeIntervalSince(strings[i].peakHoldAt) > 3 {
                    strings[i].peakHold = s.onsetRMS
                    strings[i].peakHoldAt = now
                }
                if previous == .idle && s.state != .idle {
                    appendLog(i, String(format: "onset  %.1f dBFS", Level.dB(s.onsetRMS)))
                }
                if s.isClipping && !wasClipping {
                    appendLog(i, "clipping")
                }
            }
            recorder?.add(frame)
        }
    }

    private func appendLog(_ s: Int, _ text: String) {
        log.insert(LogEvent(at: Date(), string: s, text: text), at: 0)
        if log.count > 200 { log.removeLast(log.count - 200) }
    }

    private func resetLive() {
        strings = GuitarString.all.map { LiveString(info: $0) }
        lastFrameAt = nil
        frameRate = 0
        telemetrySource = nil
        log.removeAll()
    }
}
