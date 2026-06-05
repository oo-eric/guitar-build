# MIDI Guitar Build

A DIY guitar that doubles as a polyphonic MIDI controller. Six individual
single-string pickups feed a Teensy 4.0, which converts each string's vibration
into MIDI in real time — pitch, note on/off, and per-string pitch bend — using
the MPE (MIDI Polyphonic Expression) standard so every string lives on its own
channel and bends independently.

It's a _hybrid_ instrument: alongside the six hex pickups there's one standard
magnetic pickup wired straight to a 1/4" jack, so it still plays and sounds like
a normal guitar through an amp while the digital side drives soft synths.

## Status

**Phase 2 — 6-string expansion (in progress).**

- **Phase 1 (complete):** single-string proof of concept — pickup → buffer → ADC
  → onset detection → YIN pitch detection → MPE MIDI, end-to-end into a DAW.
- **Phase 2 (current):** modular 6-string firmware written; bringing up channels
  one at a time on the breadboard. Single string is working end-to-end on the new
  MCP6002 buffer (no battery). Threshold calibration and per-string gain in
  progress.
- **Phase 3 (planned):** mount pickups and electronics into a real guitar body.
- **Future exploration:** an MPU-6050 accelerometer/gyro on the body or neck to
  turn physical gestures (tilt, shake, orientation) into MIDI CC.

See [`docs/plan.md`](docs/plan.md) for the full phased plan and parts list.

## Signal chain

```mermaid
flowchart LR
    S["Guitar string"] --> P["77HC hex pickup<br>(one per string)"]
    P --> B["MCP6002 buffer + gain<br>(3.3V from Teensy, no battery)"]
    B --> ADC["Teensy 4.0<br>analog pin A0-A5"]
    ADC --> DSP["Onset detection →<br>YIN pitch → MPE MIDI"]
    DSP --> USB["micro-USB"]
    USB --> C["Computer / DAW<br>(sees a MIDI device)"]
```

## Hardware

- **Teensy 4.0** — 600MHz ARM Cortex-M7, dual 12-bit ADC, built-in USB MIDI
- **Ubertar 77HC** single-string ("hexaphonic") pickups ×6
- **MCP6002** rail-to-rail op-amps ×3 (dual channel each = 6 buffer/gain stages),
  running on 3.3V from the Teensy — replaced the original TL072 + 9V battery
- One standard magnetic pickup (TV Jones, neck) → 1/4" jack for analog tone
- Breadboard prototype today; guitar body integration is Phase 3

Buffer circuit schematic and breadboard layout: [`docs/buffer_circuit.md`](docs/buffer_circuit.md).
Current wiring notes: [`docs/wip.md`](docs/wip.md).

## Firmware

Arduino IDE + Teensyduino. Two sketches live under `firmware/`:

- **`firmware/adc_test/`** — Phase 1 single-string sketch. Uses the Teensy Audio
  library + USB Audio for monitoring; YIN pitch detection.
- **`firmware/guitar_midi/`** — Phase 2 modular 6-string firmware. MIDI only
  (no USB Audio). Components:
  - `config.h` — all tunable constants (thresholds, sample rate, MIDI, per-string)
  - `adc_sampler.h/.cpp` — timer-driven 20kHz ADC sampling, 6 channels, per-channel ring buffers
  - `onset_detector.h/.cpp` — RMS-based per-string note on/off state machine
  - `pitch_detector.h/.cpp` — YIN pitch detection with hysteresis
  - `midi_output.h/.cpp` — MPE MIDI output with per-channel pitch bend tracking
  - `guitar_midi.ino` — orchestrator with staggered per-string pitch detection

### Flashing

1. Open the sketch in the Arduino IDE with Teensyduino installed.
2. Select **Tools → Board → Teensy 4.0**.
3. Set **Tools → USB Type → "Serial + MIDI"** (Phase 2). The Phase 1 `adc_test`
   sketch uses **"Serial + MIDI + Audio"**.
4. Upload. The Teensy enumerates as a USB MIDI device — add it as an MPE
   instrument in your DAW.

> **Power note:** don't power the Teensy via VIN and USB at the same time without
> cutting the VIN-VUSB trace.

## Tooling

`scripts/` holds host-side helpers for bring-up and debugging:

- `teensy_serial.py` — serial reader for the Teensy CDC port
- `guitar_monitor.py` — live monitoring of onset / pitch output

## Repository layout

```text
firmware/        Teensy sketches (adc_test = Phase 1, guitar_midi = Phase 2)
docs/            build plan, hardware references, circuit + design notes
scripts/         host-side serial monitoring / debug tools
enclosure/       OpenSCAD models (pickup enclosure)
brainstorm/      concept sketches
output/          captured stage notes / logs
CLAUDE.md        project instructions for Claude Code
```

## Documentation

| Doc                                                          | What's in it                                                 |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| [`docs/plan.md`](docs/plan.md)                               | Phased build plan, parts list, signal chain, technical notes |
| [`docs/guitar_build.md`](docs/guitar_build.md)               | Physical build specs and decisions                           |
| [`docs/body_shape.md`](docs/body_shape.md)                   | Body outline design (Jazzmaster × Iceman hybrid)             |
| [`docs/wood_comparison.md`](docs/wood_comparison.md)         | Body / neck / fretboard tonewood comparison                  |
| [`docs/pickup_selection.md`](docs/pickup_selection.md)       | Standard magnetic pickup selection (TV Jones)                |
| [`docs/buffer_circuit.md`](docs/buffer_circuit.md)           | Buffer/amp circuit schematic and breadboard layout           |
| [`docs/wip.md`](docs/wip.md)                                 | Current breadboard wiring details                            |
| [`docs/teensy-4.0.md`](docs/teensy-4.0.md)                   | Teensy 4.0 pinout / reference                                |
| [`docs/ubertar-77hc-pickup.md`](docs/ubertar-77hc-pickup.md) | Ubertar 77HC pickup reference                                |
