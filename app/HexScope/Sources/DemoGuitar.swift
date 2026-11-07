import Foundation

/// A pretend Teensy for working on the app without hardware. Emits the same SysEx bytes the
/// firmware does and runs them through the real decoder, so demo mode exercises that path too.
@MainActor
final class DemoGuitar {
    private var timer: Timer?
    private var sink: ((MIDIConnection.Event) -> Void)?
    private var level = [Double](repeating: 0, count: 6)
    private var freq = [Double](repeating: 0, count: 6)
    private var note = [Int](repeating: 0, count: 6)
    private var state = [NoteState](repeating: .idle, count: 6)
    private var tick = 0
    private var phase = [Double](repeating: 0, count: 6)
    private let config = DeviceConfig.defaults
    private let source: Int32 = -1

    func start(_ sink: @escaping (MIDIConnection.Event) -> Void) {
        self.sink = sink
        emit(TelemetryEncoder.config(config))
        timer = Timer.scheduledTimer(withTimeInterval: 0.05, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated { self?.step() }
        }
    }

    func stop() {
        timer?.invalidate()
        timer = nil
        sink = nil
    }

    private func emit(_ bytes: [UInt8]) {
        if let m = Telemetry.decode(bytes) { sink?(.telemetry(m, source: source)) }
    }

    private func step() {
        tick += 1
        let noise = 0.013
        var rows: [StringStatus] = []
        for s in 0..<6 {
            let open = GuitarString.all[s]
            // String 4 is "badly wired" in the demo: hot, noisy and biased, so the warnings show.
            let floor = s == 3 ? 0.05 : noise
            if state[s] == .idle, Double.random(in: 0...1) < 0.012 {
                let fret = [0, 0, 2, 3, 5, 7, 12].randomElement()!
                note[s] = open.openNote + fret
                freq[s] = Pitch.frequency(ofNote: Double(note[s])) * (1 + Double.random(in: -0.004...0.004))
                level[s] = Double.random(in: 0.06...0.3)
                state[s] = .attack
            } else if state[s] == .attack {
                state[s] = .sustain
                let vel = Int(20 + min(1, level[s] / 0.3) * 107)
                sink?(.noteOn(channel: config.channels[s], note: note[s], velocity: vel, source: source))
            } else if state[s] == .sustain || state[s] == .releasing {
                level[s] *= 0.93
                if level[s] < config.offsetThreshold {
                    state[s] = .idle
                    sink?(.noteOff(channel: config.channels[s], note: note[s], source: source))
                    note[s] = 0
                    level[s] = 0
                }
            }
            // Bleed from the neighbours, a few percent each.
            let bleed = (s > 0 ? level[s - 1] : 0) * 0.04 + (s < 5 ? level[s + 1] : 0) * 0.04
            let rms = sqrt(level[s] * level[s] + floor * floor + bleed * bleed)
            let amp = rms * 2048 * 1.41
            let dc = s == 3 ? 310.0 : Double.random(in: -6...6)
            rows.append(StringStatus(
                state: state[s], onsetRMS: rms, acRMS: rms, dcOffset: dc,
                minRaw: max(0, Int(2048 + dc - amp)), maxRaw: min(4095, Int(2048 + dc + amp)),
                frequency: state[s] == .idle ? 0 : freq[s],
                probability: state[s] == .idle ? 0 : Double.random(in: 0.86...0.98),
                note: state[s] == .idle ? 0 : note[s]))

            if (tick + s) % 3 == 0 { emit(TelemetryEncoder.scope(scope(s, rms: rms, dc: dc, floor: floor))) }
        }
        emit(TelemetryEncoder.status(StatusFrame(deviceMillis: UInt32(tick * 50), strings: rows)))
        if tick % 20 == 0 { emit(TelemetryEncoder.config(config)) }
    }

    private func scope(_ s: Int, rms: Double, dc: Double, floor: Double) -> ScopeFrame {
        let rate = 10_000.0
        let f = freq[s] > 0 && state[s] != .idle ? freq[s] : 60 // idle: mains hum
        let a = (state[s] == .idle ? floor : level[s]) * 2048 * 1.41
        phase[s] += Double.random(in: 0...(2 * .pi))
        let samples = (0..<128).map { i -> Int in
            let t = Double(i) / rate
            let w = 2 * Double.pi * f * t + phase[s]
            let v = a * (0.8 * sin(w) + 0.3 * sin(2 * w) + 0.1 * sin(3 * w))
                + Double.random(in: -1...1) * floor * 900
            return max(0, min(4095, Int(2048 + dc + v)))
        }
        return ScopeFrame(string: s, sampleRate: rate, samples: samples)
    }
}
