import Foundation
import Observation

/// A recorded stretch of telemetry. Status frames only (not scopes) so files stay small:
/// a minute is ~1,200 frames.
struct Capture: Codable, Identifiable, Hashable {
    var id = UUID()
    var name: String
    var notes: String
    var startedAt: Date
    var duration: TimeInterval
    var config: DeviceConfig
    var frames: [Frame]
    var events: [NoteEvent]

    struct Frame: Codable, Hashable {
        /// Seconds since the capture started (host clock).
        var t: Double
        var strings: [StringStatus]
    }

    struct NoteEvent: Codable, Hashable {
        var t: Double
        var string: Int
        var on: Bool
        var note: Int
        var velocity: Int
    }

    static func == (a: Capture, b: Capture) -> Bool { a.id == b.id }
    func hash(into h: inout Hasher) { h.combine(id) }
}


// MARK: - Summary

struct StringSummary: Equatable {
    var idleFloor: Double?      // median onset RMS while IDLE
    var peak: Double            // max onset RMS
    var snrDB: Double?
    var meanDC: Double          // ADC counts from mid-scale
    var clipFrames: Int
    var onsets: Int             // IDLE → active transitions seen in frames
    var noteOns: Int            // MIDI note-ons the firmware actually sent
    var notes: [Int]            // distinct notes, ascending
    var confidence: Double?     // mean YIN probability while sustaining
    var bleed: (string: Int, dB: Double)?

    static func == (a: StringSummary, b: StringSummary) -> Bool {
        a.idleFloor == b.idleFloor && a.peak == b.peak && a.onsets == b.onsets && a.noteOns == b.noteOns
            && a.bleed?.string == b.bleed?.string && a.bleed?.dB == b.bleed?.dB
    }
}

extension Capture {
    var stringCount: Int { frames.first?.strings.count ?? 0 }

    func summary() -> [StringSummary] {
        (0..<stringCount).map { summarize(string: $0) }
    }

    private func summarize(string s: Int) -> StringSummary {
        let rows = frames.compactMap { $0.strings.indices.contains(s) ? $0.strings[s] : nil }
        let idle = rows.filter { $0.state == .idle }.map(\.onsetRMS).sorted()
        let floor = idle.isEmpty ? nil : idle[idle.count / 2]
        let peak = rows.map(\.onsetRMS).max() ?? 0
        let snr = floor.flatMap { $0 > 0 && peak > 0 ? 20 * log10(peak / $0) : nil }

        var onsets = 0
        for (a, b) in zip(rows, rows.dropFirst()) where a.state == .idle && b.state != .idle { onsets += 1 }

        let sustained = rows.filter { $0.state == .sustain && $0.frequency > 0 }.map(\.probability)
        let mine = events.filter { $0.string == s && $0.on }

        return StringSummary(
            idleFloor: floor,
            peak: peak,
            snrDB: snr,
            meanDC: rows.isEmpty ? 0 : rows.map(\.dcOffset).reduce(0, +) / Double(rows.count),
            clipFrames: rows.filter(\.isClipping).count,
            onsets: onsets,
            noteOns: mine.count,
            notes: Array(Set(mine.map(\.note))).sorted(),
            confidence: sustained.isEmpty ? nil : sustained.reduce(0, +) / Double(sustained.count),
            bleed: bleed(from: s))
    }

    /// How loudly string `s` shows up on its neighbours. Uses only frames where `s` is the one
    /// string playing, so it isolates leakage from chords. Returns the worst neighbour.
    /// Includes the neighbour's own noise floor, so "no crosstalk" reads as that string's
    /// floor relative to the plucked level — compare between captures, not against zero.
    private func bleed(from s: Int) -> (string: Int, dB: Double)? {
        var sums = [Double](repeating: 0, count: stringCount)
        var n = 0
        for f in frames where f.strings.indices.contains(s) {
            let me = f.strings[s]
            guard me.state == .sustain || me.state == .attack, me.acRMS > 0 else { continue }
            let othersQuiet = f.strings.enumerated().allSatisfy { $0.offset == s || $0.element.state == .idle }
            guard othersQuiet else { continue }
            for (j, o) in f.strings.enumerated() where j != s { sums[j] += o.acRMS / me.acRMS }
            n += 1
        }
        guard n >= 3 else { return nil }
        let worst = sums.enumerated().filter { $0.offset != s }.max { $0.element < $1.element }!
        return (worst.offset, 20 * log10(max(worst.element / Double(n), 1e-6)))
    }
}

// MARK: - Recording

struct CaptureRecorder {
    let startedAt = Date()
    var config: DeviceConfig
    var frames: [Capture.Frame] = []
    var events: [Capture.NoteEvent] = []

    var elapsed: TimeInterval { Date().timeIntervalSince(startedAt) }

    mutating func add(_ frame: StatusFrame) {
        frames.append(.init(t: elapsed, strings: frame.strings))
    }

    mutating func add(string: Int, on: Bool, note: Int, velocity: Int) {
        events.append(.init(t: elapsed, string: string, on: on, note: note, velocity: velocity))
    }

    func finish(name: String, notes: String) -> Capture {
        Capture(name: name, notes: notes, startedAt: startedAt, duration: elapsed,
                config: config, frames: frames, events: events)
    }
}

// MARK: - Storage

/// One JSON file per capture in Documents/Captures — visible in the Files app on iOS
/// (UIFileSharingEnabled) and in ~/Library/Containers/… or ~/Documents on the Mac.
@MainActor @Observable
final class CaptureStore {
    private(set) var captures: [Capture] = []
    var loadError: String?

    let directory: URL

    init(directory: URL? = nil) {
        self.directory = directory ?? URL.documentsDirectory.appending(path: "Captures", directoryHint: .isDirectory)
        try? FileManager.default.createDirectory(at: self.directory, withIntermediateDirectories: true)
        reload()
    }

    func url(for c: Capture) -> URL { directory.appending(path: "\(fileStem(c)).hexscope.json") }

    func reload() {
        let files = (try? FileManager.default.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil)) ?? []
        var loaded: [Capture] = []
        var bad = 0
        for f in files where f.pathExtension == "json" {
            if let data = try? Data(contentsOf: f), let c = try? Self.decoder.decode(Capture.self, from: data) {
                loaded.append(c)
            } else {
                bad += 1
            }
        }
        captures = loaded.sorted { $0.startedAt > $1.startedAt }
        loadError = bad > 0 ? "\(bad) file(s) in Captures couldn't be read" : nil
    }

    func save(_ c: Capture) throws {
        let data = try Self.encoder.encode(c)
        try data.write(to: url(for: c), options: .atomic)
        reload()
    }

    func delete(_ c: Capture) {
        try? FileManager.default.removeItem(at: url(for: c))
        reload()
    }

    private func fileStem(_ c: Capture) -> String {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd_HHmmss"
        let safe = c.name.replacingOccurrences(of: "[^A-Za-z0-9-]+", with: "-", options: .regularExpression)
            .trimmingCharacters(in: CharacterSet(charactersIn: "-"))
        return "\(f.string(from: c.startedAt))_\(safe.prefix(40))_\(c.id.uuidString.prefix(4))"
    }

    static let encoder: JSONEncoder = {
        let e = JSONEncoder()
        e.dateEncodingStrategy = .iso8601
        e.outputFormatting = [.sortedKeys]
        return e
    }()

    static let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.dateDecodingStrategy = .iso8601
        return d
    }()
}
