import XCTest
@testable import HexScope

final class TelemetryTests: XCTestCase {
    /// Hand-built bytes laid out exactly as firmware/guitar_midi/telemetry.cpp writes them,
    /// so a firmware-side format change without an app-side change fails here.
    func testDecodesFirmwareStatusLayout() throws {
        var b: [UInt8] = [0xF0, 0x7D, 0x47, 0x01, 0x01]
        b += [0x00, 0x00, 0x07, 0x68]            // millis = 1000
        b += [0x01]                               // 1 string
        b += [0x02]                               // SUSTAIN
        b += [0x03, 0x45]                         // onset rms 0x1C5 = 453 → 453/16383
        b += [0x03, 0x40]                         // ac rms 448
        b += [0x40, 0x0A]                         // dc = 8202 - 8192 = +10
        b += [0x0D, 0x00]                         // min 1664
        b += [0x13, 0x00]                         // max 2432
        b += [0x0D, 0x04]                         // freq 1668 → 166.8 Hz
        b += [0x5A]                               // prob 0.90
        b += [0x33]                               // note 51
        b += [0xF7]

        guard case .status(let f) = Telemetry.decode(b) else { return XCTFail("not a status frame") }
        XCTAssertEqual(f.deviceMillis, 1000)
        let s = try XCTUnwrap(f.strings.first)
        XCTAssertEqual(s.state, .sustain)
        XCTAssertEqual(s.onsetRMS, 453.0 / 16383, accuracy: 1e-9)
        XCTAssertEqual(s.dcOffset, 10)
        XCTAssertEqual(s.minRaw, 1664)
        XCTAssertEqual(s.maxRaw, 2432)
        XCTAssertEqual(s.frequency, 166.8, accuracy: 1e-9)
        XCTAssertEqual(s.probability, 0.9, accuracy: 1e-9)
        XCTAssertEqual(s.note, 51)
    }

    func testRoundTrips() {
        let status = StatusFrame(deviceMillis: 123_456, strings: (0..<6).map { i in
            StringStatus(state: .attack, onsetRMS: 0.1, acRMS: 0.09, dcOffset: Double(-i * 7),
                         minRaw: 100 * i, maxRaw: 4000, frequency: 82.4, probability: 0.85, note: 40 + i)
        })
        guard case .status(let s) = Telemetry.decode(TelemetryEncoder.status(status)) else { return XCTFail() }
        XCTAssertEqual(s.strings.count, 6)
        XCTAssertEqual(s.strings[5].dcOffset, -35)
        XCTAssertEqual(s.strings[3].note, 43)
        XCTAssertEqual(s.strings[0].onsetRMS, 0.1, accuracy: 1 / 16383)

        let scope = ScopeFrame(string: 4, sampleRate: 10_000, samples: Array(0..<128).map { $0 * 32 })
        XCTAssertEqual(Telemetry.decode(TelemetryEncoder.scope(scope)), .scope(scope))

        let cfg = DeviceConfig.defaults
        guard case .config(let c) = Telemetry.decode(TelemetryEncoder.config(cfg)) else { return XCTFail() }
        XCTAssertEqual(c.channels, [2, 3, 4, 5, 6, 7])
        XCTAssertEqual(c.onsetThreshold, 0.03, accuracy: 1 / 16383)
        XCTAssertEqual(c.sampleRate, 20_000)
    }

    func testIgnoresOtherSysEx() {
        XCTAssertNil(Telemetry.decode([0xF0, 0x7E, 0x7F, 0x06, 0x01, 0xF7])) // identity request
        XCTAssertNil(Telemetry.decode([0xF0, 0x7D, 0x47, 0x02, 0x01, 0xF7])) // future version
        XCTAssertNil(Telemetry.decode([0xF0, 0x7D, 0x47, 0x01, 0x01, 0x00, 0xF7])) // truncated
    }

    func testCaptureSummary() {
        func row(_ st: NoteState, _ rms: Double) -> StringStatus {
            StringStatus(state: st, onsetRMS: rms, acRMS: rms, dcOffset: 4, minRaw: 1000, maxRaw: 3000,
                         frequency: st == .sustain ? 110 : 0, probability: 0.9, note: 0)
        }
        // String 0 plucked, string 1 picks up 10% of it.
        var frames: [Capture.Frame] = []
        for t in 0..<10 { frames.append(.init(t: Double(t), strings: [row(.idle, 0.01), row(.idle, 0.01)])) }
        for t in 10..<20 { frames.append(.init(t: Double(t), strings: [row(.sustain, 0.2), row(.idle, 0.02)])) }
        let c = Capture(name: "t", notes: "", startedAt: .now, duration: 20, config: .defaults,
                        frames: frames, events: [.init(t: 10, string: 0, on: true, note: 45, velocity: 80)])
        let s = c.summary()
        XCTAssertEqual(s[0].idleFloor, 0.01)
        XCTAssertEqual(s[0].peak, 0.2)
        XCTAssertEqual(s[0].snrDB!, 26.02, accuracy: 0.01)
        XCTAssertEqual(s[0].onsets, 1)
        XCTAssertEqual(s[0].noteOns, 1)
        XCTAssertEqual(s[0].bleed?.string, 1)
        XCTAssertEqual(s[0].bleed!.dB, -20, accuracy: 0.01)
        XCTAssertEqual(s[1].onsets, 0)
    }
}
