import SwiftUI

struct StringCard: View {
    let string: LiveString
    let config: DeviceConfig

    private var info: GuitarString { string.info }
    private var tint: Color { .string(info.index) }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            header
            if let s = string.status {
                pitchRow(s)
                LevelMeter(level: s.onsetRMS, peak: string.peakHold,
                           onset: config.onsetThreshold, offset: config.offsetThreshold, tint: tint)
                Sparkline(values: string.history, onset: Level.dB(config.onsetThreshold),
                          offset: Level.dB(config.offsetThreshold), tint: tint)
                    .frame(height: 44)
                ScopeView(frame: string.scope, tint: tint)
                    .frame(height: 70)
                footer(s)
                warnings(s)
            } else {
                Text("No data for this string yet")
                    .font(.callout).foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, minHeight: 120)
            }
        }
        .padding(12)
        .background(Color.cardBackground, in: RoundedRectangle(cornerRadius: 14))
        .overlay(RoundedRectangle(cornerRadius: 14).strokeBorder(activeBorder, lineWidth: 2))
    }

    private var activeBorder: Color {
        guard let st = string.status?.state, st != .idle else { return .clear }
        return tint.opacity(0.7)
    }

    private var header: some View {
        HStack(alignment: .firstTextBaseline) {
            Text("\(info.number)")
                .font(.title2.bold().monospacedDigit())
                .foregroundStyle(tint)
            Text(info.name).font(.title3.weight(.semibold))
            Text(String(format: "%.1f Hz open", info.openFrequency))
                .font(.caption).foregroundStyle(.secondary)
            Spacer()
            if let st = string.status?.state { StateBadge(state: st) }
        }
    }

    private func pitchRow(_ s: StringStatus) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            if let (note, cents) = Pitch.nearest(s.frequency) {
                Text(Pitch.noteName(note)).font(.title2.bold())
                    .foregroundStyle(s.state == .idle ? .secondary : .primary)
                Text(String(format: "%+.0f¢", cents)).font(.callout.monospacedDigit())
                    .foregroundStyle(abs(cents) < 10 ? .green : .orange)
                Text(String(format: "%.1f Hz", s.frequency)).font(.callout.monospacedDigit())
                    .foregroundStyle(.secondary)
                Text(String(format: "%.0f%%", s.probability * 100)).font(.caption.monospacedDigit())
                    .foregroundStyle(.secondary)
            } else {
                Text("no pitch").font(.title3).foregroundStyle(.tertiary)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 0) {
                Text("\(string.noteOns)").font(.headline.monospacedDigit())
                Text("notes").font(.caption2).foregroundStyle(.secondary)
            }
        }
    }

    private func footer(_ s: StringStatus) -> some View {
        let biasV = ADC.volts(counts: 2048 + s.dcOffset)
        return HStack(spacing: 14) {
            Metric(label: "Bias", value: String(format: "%.3f V", biasV),
                   sub: String(format: "%+.0f ct", s.dcOffset), warn: abs(s.dcOffset) > 150)
            Metric(label: "Swing", value: String(format: "%.2f–%.2f V", ADC.volts(counts: Double(s.minRaw)), ADC.volts(counts: Double(s.maxRaw))),
                   sub: "\(s.maxRaw - s.minRaw) ct p-p", warn: s.isClipping)
            Metric(label: "AC RMS", value: String(format: "%.1f dB", Level.dB(s.acRMS)),
                   sub: String(format: "%.4f", s.acRMS), warn: false)
        }
    }

    @ViewBuilder
    private func warnings(_ s: StringStatus) -> some View {
        let items = warningList(s)
        if !items.isEmpty {
            VStack(alignment: .leading, spacing: 3) {
                ForEach(items, id: \.self) { w in
                    Label(w, systemImage: "exclamationmark.triangle.fill")
                        .font(.caption).foregroundStyle(.orange)
                }
            }
        }
    }

    private func warningList(_ s: StringStatus) -> [String] {
        var w: [String] = []
        if s.isClipping { w.append("Clipping at the ADC — too much gain or pickup too close") }
        if abs(s.dcOffset) > 150 {
            w.append(String(format: "Bias is %+.0f counts off mid-rail — check the 1.65 V divider / input", s.dcOffset))
        }
        if s.state == .idle && s.onsetRMS > config.onsetThreshold {
            w.append("Idle noise is above the onset threshold — this string will false-trigger")
        }
        if s.note > 0 && !Pitch.fretRange(info).contains(s.note) {
            w.append("\(Pitch.noteName(s.note)) can't be played on this string — wires swapped?")
        }
        return w
    }
}

struct StateBadge: View {
    let state: NoteState
    var body: some View {
        Text(state.label)
            .font(.caption2.bold())
            .padding(.horizontal, 7).padding(.vertical, 3)
            .background(color.opacity(0.18), in: Capsule())
            .foregroundStyle(color)
    }
    private var color: Color {
        switch state {
        case .idle: .gray
        case .attack: .yellow
        case .sustain: .green
        case .releasing: .blue
        }
    }
}

struct Metric: View {
    let label: String
    let value: String
    let sub: String
    let warn: Bool
    var body: some View {
        VStack(alignment: .leading, spacing: 1) {
            Text(label).font(.caption2).foregroundStyle(.secondary)
            Text(value).font(.caption.monospacedDigit().weight(.medium))
                .foregroundStyle(warn ? .orange : .primary)
            Text(sub).font(.caption2.monospacedDigit()).foregroundStyle(.secondary)
        }
    }
}

// MARK: - Graphics

/// Horizontal dBFS meter with the firmware's onset/offset thresholds marked.
struct LevelMeter: View {
    let level: Double
    let peak: Double
    let onset: Double
    let offset: Double
    let tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            GeometryReader { g in
                let w = g.size.width
                ZStack(alignment: .leading) {
                    Capsule().fill(.quaternary)
                    Capsule().fill(tint.gradient).frame(width: max(4, x(level, w)))
                    tick(x(offset, w), .blue)
                    tick(x(onset, w), .primary)
                    Rectangle().fill(.red).frame(width: 2).offset(x: x(peak, w) - 1)
                }
            }
            .frame(height: 12)
            HStack {
                Text(String(format: "%.1f dBFS", Level.dB(level))).monospacedDigit()
                Spacer()
                Text(String(format: "peak %.1f", Level.dB(peak))).monospacedDigit().foregroundStyle(.red)
                Text("onset").foregroundStyle(.primary)
                Text("off").foregroundStyle(.blue)
            }
            .font(.caption2)
            .foregroundStyle(.secondary)
        }
    }

    private func x(_ v: Double, _ w: CGFloat) -> CGFloat {
        let db = Level.dB(v)
        return CGFloat((db - Level.floor) / -Level.floor).clamped(0, 1) * w
    }

    private func tick(_ x: CGFloat, _ c: Color) -> some View {
        Rectangle().fill(c).frame(width: 2, height: 16).offset(x: x - 1)
    }
}

/// Last few seconds of onset RMS (dBFS) with threshold lines.
struct Sparkline: View {
    let values: [Double]
    let onset: Double
    let offset: Double
    let tint: Color

    var body: some View {
        Canvas { ctx, size in
            func y(_ db: Double) -> CGFloat {
                let lo = Level.floor, hi = -6.0
                return size.height * (1 - CGFloat((db - lo) / (hi - lo)).clamped(0, 1))
            }
            for (db, color) in [(onset, Color.primary), (offset, Color.blue)] {
                var p = Path()
                p.move(to: CGPoint(x: 0, y: y(db)))
                p.addLine(to: CGPoint(x: size.width, y: y(db)))
                ctx.stroke(p, with: .color(color.opacity(0.35)), style: StrokeStyle(lineWidth: 1, dash: [3, 3]))
            }
            guard values.count > 1 else { return }
            let n = GuitarModel.historyLength
            let dx = size.width / CGFloat(n - 1)
            let start = n - values.count
            var line = Path()
            for (i, v) in values.enumerated() {
                let pt = CGPoint(x: CGFloat(start + i) * dx, y: y(v))
                i == 0 ? line.move(to: pt) : line.addLine(to: pt)
            }
            var fill = line
            fill.addLine(to: CGPoint(x: size.width, y: size.height))
            fill.addLine(to: CGPoint(x: CGFloat(start) * dx, y: size.height))
            fill.closeSubpath()
            ctx.fill(fill, with: .color(tint.opacity(0.15)))
            ctx.stroke(line, with: .color(tint), lineWidth: 1.5)
        }
        .background(.quaternary.opacity(0.4), in: RoundedRectangle(cornerRadius: 6))
    }
}

/// The most recent ~12.8 ms of raw ADC samples. Auto-scales around the signal so a quiet
/// string is still readable; the label gives the true peak-to-peak.
struct ScopeView: View {
    let frame: ScopeFrame?
    let tint: Color

    var body: some View {
        Canvas { ctx, size in
            var mid = Path()
            mid.move(to: CGPoint(x: 0, y: size.height / 2))
            mid.addLine(to: CGPoint(x: size.width, y: size.height / 2))
            ctx.stroke(mid, with: .color(.secondary.opacity(0.3)), lineWidth: 0.5)

            guard let f = frame, f.samples.count > 1 else { return }
            let mean = Double(f.samples.reduce(0, +)) / Double(f.samples.count)
            let span = max(40.0, f.samples.map { abs(Double($0) - mean) }.max() ?? 1) * 1.15
            let dx = size.width / CGFloat(f.samples.count - 1)
            var p = Path()
            for (i, v) in f.samples.enumerated() {
                let y = size.height / 2 - CGFloat((Double(v) - mean) / span) * size.height / 2
                let pt = CGPoint(x: CGFloat(i) * dx, y: y)
                i == 0 ? p.move(to: pt) : p.addLine(to: pt)
            }
            ctx.stroke(p, with: .color(tint), lineWidth: 1.25)
        }
        .background(.quaternary.opacity(0.4), in: RoundedRectangle(cornerRadius: 6))
        .overlay(alignment: .topTrailing) {
            if let f = frame, let lo = f.samples.min(), let hi = f.samples.max() {
                Text(String(format: "%.1f ms · %d ct p-p", Double(f.samples.count) / f.sampleRate * 1000, hi - lo))
                    .font(.caption2.monospacedDigit()).foregroundStyle(.secondary).padding(4)
            }
        }
    }
}

extension Comparable {
    func clamped(_ lo: Self, _ hi: Self) -> Self { min(max(self, lo), hi) }
}
