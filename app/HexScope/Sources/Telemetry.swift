import Foundation

// Decoder for the firmware's diagnostic SysEx (firmware/guitar_midi/telemetry.h).
// Wire format: F0 7D 47 <version> <type> <payload> F7, all values in 7-bit groups,
// most significant first. Change both sides together and bump `version`.

enum NoteState: Int, Codable, CaseIterable {
    case idle, attack, sustain, releasing

    var label: String {
        switch self {
        case .idle: "IDLE"
        case .attack: "ATTACK"
        case .sustain: "SUSTAIN"
        case .releasing: "RELEASE"
        }
    }
}

struct StringStatus: Codable, Hashable {
    var state: NoteState
    /// RMS the onset detector compares against its thresholds (fraction of full scale, not DC-removed).
    var onsetRMS: Double
    /// RMS over the last ~51 ms with DC removed — the actual signal level.
    var acRMS: Double
    /// Mean of the raw signal relative to mid-scale (2048), in ADC counts. Healthy bias ≈ 0.
    var dcOffset: Double
    var minRaw: Int
    var maxRaw: Int
    /// Most recent YIN result in Hz, 0 when none.
    var frequency: Double
    var probability: Double
    /// Active MIDI note, 0 when none.
    var note: Int

    var isClipping: Bool { minRaw <= 8 || maxRaw >= 4087 }
}

struct StatusFrame: Codable, Equatable {
    var deviceMillis: UInt32
    var strings: [StringStatus]
}

struct ScopeFrame: Equatable {
    var string: Int
    var sampleRate: Double
    /// Raw ADC counts, 0...4095.
    var samples: [Int]
}

struct DeviceConfig: Codable, Hashable {
    var sampleRate: Double
    var onsetThreshold: Double
    var offsetThreshold: Double
    var yinThreshold: Double
    var channels: [Int]

    /// Values from config.h at the time the app was written; replaced by the device's own on connect.
    static let defaults = DeviceConfig(sampleRate: 20000, onsetThreshold: 0.03, offsetThreshold: 0.018,
                                       yinThreshold: 0.25, channels: [2, 3, 4, 5, 6, 7])
}

enum TelemetryMessage: Equatable {
    case status(StatusFrame)
    case scope(ScopeFrame)
    case config(DeviceConfig)
}

enum Telemetry {
    static let manufacturer: UInt8 = 0x7D
    static let signature: UInt8 = 0x47
    static let version: UInt8 = 1

    enum Kind: UInt8 { case status = 0x01, scope = 0x02, config = 0x03 }

    /// Decodes a SysEx body with or without the surrounding F0/F7. Returns nil for anything
    /// that isn't ours or doesn't parse — other gear on the MIDI bus is not an error.
    static func decode(_ raw: [UInt8]) -> TelemetryMessage? {
        var bytes = raw[...]
        if bytes.first == 0xF0 { bytes = bytes.dropFirst() }
        if bytes.last == 0xF7 { bytes = bytes.dropLast() }
        var r = Reader(bytes: bytes)
        guard r.u7() == Int(manufacturer), r.u7() == Int(signature), r.u7() == Int(version),
              let kindByte = r.u7(), let kind = Kind(rawValue: UInt8(kindByte)) else { return nil }

        switch kind {
        case .status:
            guard let ms = r.u28(), let n = r.u7() else { return nil }
            var strings: [StringStatus] = []
            for _ in 0..<n {
                guard let st = r.u7(), let onset = r.u14(), let ac = r.u14(), let dc = r.u14(),
                      let lo = r.u14(), let hi = r.u14(), let f = r.u14(), let p = r.u7(), let note = r.u7()
                else { return nil }
                strings.append(StringStatus(
                    state: NoteState(rawValue: st) ?? .idle,
                    onsetRMS: level(onset), acRMS: level(ac),
                    dcOffset: Double(dc - 8192),
                    minRaw: lo, maxRaw: hi,
                    frequency: Double(f) / 10, probability: Double(p) / 100,
                    note: note))
            }
            return .status(StatusFrame(deviceMillis: ms, strings: strings))

        case .scope:
            guard let s = r.u7(), let rate = r.u14(), let n = r.u14() else { return nil }
            var samples: [Int] = []
            samples.reserveCapacity(n)
            for _ in 0..<n {
                guard let v = r.u14() else { return nil }
                samples.append(v)
            }
            return .scope(ScopeFrame(string: s, sampleRate: Double(rate) * 10, samples: samples))

        case .config:
            guard let n = r.u7(), let rate = r.u14(), let on = r.u14(), let off = r.u14(),
                  let yin = r.u7() else { return nil }
            var channels: [Int] = []
            for _ in 0..<n {
                guard let c = r.u7() else { return nil }
                channels.append(c)
            }
            return .config(DeviceConfig(sampleRate: Double(rate) * 10, onsetThreshold: level(on),
                                        offsetThreshold: level(off), yinThreshold: Double(yin) / 100,
                                        channels: channels))
        }
    }

    private static func level(_ v: Int) -> Double { Double(v) / 16383 }

    private struct Reader {
        var bytes: ArraySlice<UInt8>
        mutating func u7() -> Int? {
            guard let b = bytes.popFirst(), b < 0x80 else { return nil }
            return Int(b)
        }
        mutating func u14() -> Int? {
            guard let hi = u7(), let lo = u7() else { return nil }
            return hi << 7 | lo
        }
        mutating func u28() -> UInt32? {
            guard let a = u7(), let b = u7(), let c = u7(), let d = u7() else { return nil }
            return UInt32(a << 21 | b << 14 | c << 7 | d)
        }
    }
}

/// Encoder mirroring the firmware. Used by tests and demo mode so both exercise the real decoder.
enum TelemetryEncoder {
    static func status(_ frame: StatusFrame) -> [UInt8] {
        var w = Writer(kind: .status)
        w.u28(frame.deviceMillis)
        w.u7(frame.strings.count)
        for s in frame.strings {
            w.u7(s.state.rawValue)
            w.level(s.onsetRMS); w.level(s.acRMS)
            w.u14(Int(s.dcOffset.rounded()) + 8192)
            w.u14(s.minRaw); w.u14(s.maxRaw)
            w.u14(Int((s.frequency * 10).rounded()))
            w.u7(Int((s.probability * 100).rounded()))
            w.u7(s.note)
        }
        return w.message
    }

    static func scope(_ frame: ScopeFrame) -> [UInt8] {
        var w = Writer(kind: .scope)
        w.u7(frame.string)
        w.u14(Int(frame.sampleRate / 10))
        w.u14(frame.samples.count)
        frame.samples.forEach { w.u14($0) }
        return w.message
    }

    static func config(_ c: DeviceConfig) -> [UInt8] {
        var w = Writer(kind: .config)
        w.u7(c.channels.count)
        w.u14(Int(c.sampleRate / 10))
        w.level(c.onsetThreshold); w.level(c.offsetThreshold)
        w.u7(Int((c.yinThreshold * 100).rounded()))
        c.channels.forEach { w.u7($0) }
        return w.message
    }

    private struct Writer {
        var bytes: [UInt8]
        init(kind: Telemetry.Kind) {
            bytes = [0xF0, Telemetry.manufacturer, Telemetry.signature, Telemetry.version, kind.rawValue]
        }
        mutating func u7(_ v: Int) { bytes.append(UInt8(max(0, min(0x7F, v)))) }
        mutating func u14(_ v: Int) {
            let c = max(0, min(0x3FFF, v))
            bytes.append(UInt8(c >> 7 & 0x7F)); bytes.append(UInt8(c & 0x7F))
        }
        mutating func u28(_ v: UInt32) {
            for shift in [21, 14, 7, 0] { bytes.append(UInt8(v >> UInt32(shift) & 0x7F)) }
        }
        mutating func level(_ v: Double) { u14(Int((v * 16383).rounded())) }
        var message: [UInt8] { bytes + [0xF7] }
    }
}
