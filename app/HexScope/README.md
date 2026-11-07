# HexScope

Per-string diagnostics for the hex pickup, on iPhone, iPad, or Mac. One SwiftUI target.

## How it talks to the Teensy

iOS won't let an app open a USB **serial** port. It will talk to a class-compliant **USB MIDI**
device through CoreMIDI. So the firmware sends its diagnostics as SysEx
(`firmware/guitar_midi/telemetry.{h,cpp}`) over the MIDI interface it already has, and the
Serial debug prints don't change.

- USB Type in Arduino must stay **Serial + MIDI**.
- iPhone 17 / iPad: plug a USB-C → micro-USB cable straight into the Teensy. The phone powers it.
- Mac: the same cable you flash with.
- Wire format is documented in `telemetry.h`; the decoder is `Sources/Telemetry.swift`.
  `Tests/TelemetryTests.swift` has a hand-built frame in the firmware's byte layout, so if
  the two sides drift apart that test fails. Change both together and bump the version.

## What each string shows

- State (IDLE / ATTACK / SUSTAIN / RELEASE), note count
- Detected pitch, cents off, YIN confidence
- Level meter in dBFS, with the firmware's onset (black) and offset (blue) thresholds and a 3 s peak hold
- 6 s level history, plus a 12.8 ms raw-ADC scope
- Bias (DC) in volts and counts, swing min–max, AC RMS
- Warnings: clipping, bias off mid-rail, idle noise above the onset threshold, and a note the
  string physically can't play (which means wires are swapped)

The strip at the top shows all six at once. String 1 is high E (GK pin 1 → A0).

## Captures

Record → play → Stop → name it ("raised G pickup 1 mm"). Files are JSON in
`Documents/Captures`, which shows up in the Files app on iOS. **Compare** puts two captures
side by side for each string: idle noise, pluck peak, peak/noise, worst bleed into another
string, bias, clipped frames, onsets, MIDI notes, pitch confidence. Green means better, red worse.

The "worst bleed" figure counts the neighbour's noise floor as well as real crosstalk. Use it to
compare captures with each other; it will never read as zero.

## Build

```
cd app/HexScope && xcodegen generate   # after editing project.yml or adding files
open HexScope.xcodeproj
```

Use the **Demo data** menu item (or the `-demo` launch argument) to run without hardware.
In the demo, string 4 is deliberately miswired so the warnings appear.
