import CoreMIDI
import Foundation

/// Listens to every MIDI source and turns traffic into telemetry messages and note events.
///
/// The Teensy enumerates as a class-compliant USB MIDI device ("Teensy MIDI"), which is the
/// one USB interface iOS lets an app talk to — the serial port is invisible on iPhone/iPad.
/// Everything is decoded on CoreMIDI's receive thread and handed to the main queue.
final class MIDIConnection: @unchecked Sendable {
    struct Source: Identifiable, Equatable {
        let id: MIDIUniqueID
        let name: String
    }

    enum Event {
        case telemetry(TelemetryMessage, source: MIDIUniqueID)
        case noteOn(channel: Int, note: Int, velocity: Int, source: MIDIUniqueID)
        case noteOff(channel: Int, note: Int, source: MIDIUniqueID)
    }

    /// Called on the main queue.
    var onEvent: ((Event) -> Void)?
    /// Called on the main queue whenever devices come or go.
    var onSourcesChanged: (([Source]) -> Void)?

    private var client = MIDIClientRef()
    private var port = MIDIPortRef()
    private var connected: [MIDIEndpointRef] = []
    /// Touched only from the receive callback, which CoreMIDI calls serially per port.
    private var sysex: [MIDIUniqueID: [UInt8]] = [:]
    private(set) var startError: String?

    func start() {
        var status = MIDIClientCreateWithBlock("HexScope" as CFString, &client) { [weak self] note in
            if note.pointee.messageID == .msgSetupChanged {
                DispatchQueue.main.async { self?.connectSources() }
            }
        }
        guard status == noErr else { startError = "MIDI client error \(status)"; return }

        status = MIDIInputPortCreateWithProtocol(client, "HexScope In" as CFString, ._1_0, &port) { [weak self] list, refCon in
            let uid = MIDIUniqueID(truncatingIfNeeded: Int(bitPattern: refCon))
            self?.receive(list, from: uid)
        }
        guard status == noErr else { startError = "MIDI port error \(status)"; return }
        connectSources()
    }

    func connectSources() {
        for src in connected { MIDIPortDisconnectSource(port, src) }
        connected.removeAll()

        var found: [Source] = []
        for i in 0..<MIDIGetNumberOfSources() {
            let src = MIDIGetSource(i)
            var uid: MIDIUniqueID = 0
            MIDIObjectGetIntegerProperty(src, kMIDIPropertyUniqueID, &uid)
            MIDIPortConnectSource(port, src, UnsafeMutableRawPointer(bitPattern: Int(uid)))
            connected.append(src)
            found.append(Source(id: uid, name: Self.name(of: src)))
        }
        onSourcesChanged?(found)
    }

    private static func name(of endpoint: MIDIEndpointRef) -> String {
        var cf: Unmanaged<CFString>?
        if MIDIObjectGetStringProperty(endpoint, kMIDIPropertyDisplayName, &cf) == noErr, let cf {
            return cf.takeRetainedValue() as String
        }
        return "Unknown source"
    }

    // MARK: - Universal MIDI Packet parsing (MIDI 1.0 protocol)

    /// Words per UMP, indexed by message type (top nibble of the first word).
    private static let umpSize = [1, 1, 1, 2, 2, 4, 1, 1, 2, 2, 2, 3, 3, 4, 4, 4]

    private func receive(_ list: UnsafePointer<MIDIEventList>, from uid: MIDIUniqueID) {
        var out: [Event] = []
        for packet in list.unsafeSequence() {
            let count = Int(packet.pointee.wordCount)
            let base = UnsafeRawPointer(packet) + MemoryLayout<MIDIEventPacket>.offset(of: \.words)!
            let words = base.bindMemory(to: UInt32.self, capacity: count)
            var i = 0
            while i < count {
                let w0 = words[i]
                let type = Int(w0 >> 28)
                let size = Self.umpSize[type]
                guard i + size <= count else { break }
                switch type {
                case 0x2: // MIDI 1.0 channel voice
                    let status = Int(w0 >> 16 & 0xF0)
                    let channel = Int(w0 >> 16 & 0x0F) + 1
                    let d1 = Int(w0 >> 8 & 0x7F), d2 = Int(w0 & 0x7F)
                    if status == 0x90 && d2 > 0 {
                        out.append(.noteOn(channel: channel, note: d1, velocity: d2, source: uid))
                    } else if status == 0x80 || status == 0x90 {
                        out.append(.noteOff(channel: channel, note: d1, source: uid))
                    }
                case 0x3: // 7-bit SysEx data, up to 6 bytes per packet
                    let w1 = words[i + 1]
                    let form = Int(w0 >> 20 & 0xF) // 0 complete, 1 start, 2 continue, 3 end
                    let n = min(6, Int(w0 >> 16 & 0xF))
                    let all: [UInt8] = [UInt8(w0 >> 8 & 0xFF), UInt8(w0 & 0xFF),
                                        UInt8(w1 >> 24), UInt8(w1 >> 16 & 0xFF),
                                        UInt8(w1 >> 8 & 0xFF), UInt8(w1 & 0xFF)]
                    let chunk = all[0..<n]
                    switch form {
                    case 0:
                        if let m = Telemetry.decode(Array(chunk)) { out.append(.telemetry(m, source: uid)) }
                    case 1:
                        sysex[uid] = Array(chunk)
                    case 2:
                        sysex[uid]?.append(contentsOf: chunk)
                        if (sysex[uid]?.count ?? 0) > 65_536 { sysex[uid] = nil } // runaway, not ours
                    case 3:
                        if var buf = sysex.removeValue(forKey: uid) {
                            buf.append(contentsOf: chunk)
                            if let m = Telemetry.decode(buf) { out.append(.telemetry(m, source: uid)) }
                        }
                    default: break
                    }
                default: break
                }
                i += size
            }
        }
        guard !out.isEmpty else { return }
        DispatchQueue.main.async { [weak self] in
            guard let handler = self?.onEvent else { return }
            out.forEach(handler)
        }
    }
}
