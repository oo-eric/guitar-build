import Foundation

/// One string of the hex pickup. Index 0 is string 1, high E — GK pin 1 → J1 → A0.
struct GuitarString: Identifiable, Hashable {
    let index: Int
    let openNote: Int

    var id: Int { index }
    var number: Int { index + 1 }
    var name: String { Pitch.noteName(openNote) }
    var openFrequency: Double { Pitch.frequency(ofNote: Double(openNote)) }

    static let all: [GuitarString] = [64, 59, 55, 50, 45, 40].enumerated().map {
        GuitarString(index: $0.offset, openNote: $0.element)
    }
}

enum Pitch {
    static let names = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"]

    static func noteName(_ midi: Int) -> String {
        guard midi > 0 else { return "—" }
        return names[midi % 12] + String(midi / 12 - 1)
    }

    static func frequency(ofNote note: Double) -> Double { 440 * pow(2, (note - 69) / 12) }

    static func midiNote(ofFrequency f: Double) -> Double { 69 + 12 * log2(f / 440) }

    /// Nearest note and cents away from it.
    static func nearest(_ f: Double) -> (note: Int, cents: Double)? {
        guard f > 0 else { return nil }
        let m = midiNote(ofFrequency: f)
        let n = Int(m.rounded())
        return (n, (m - Double(n)) * 100)
    }

    /// Lowest/highest playable notes on a string with a 24-fret neck.
    static func fretRange(_ s: GuitarString) -> ClosedRange<Int> { s.openNote...(s.openNote + 24) }
}

enum Level {
    /// Fraction of ADC full scale → dBFS, floored so silence doesn't run off the chart.
    static func dB(_ x: Double) -> Double { x > 0 ? max(-72, 20 * log10(x)) : -72 }
    static let floor = -66.0
}

/// ADC counts → volts at the Teensy pin (3.3 V reference, 12-bit).
enum ADC {
    static let fullScale = 4095.0
    static let vref = 3.3
    static func volts(counts: Double) -> Double { counts / fullScale * vref }
}
