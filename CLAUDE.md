# MIDI Guitar Build

A DIY guitar with per-string pickups and a Teensy 4.0 for real-time pitch-to-MIDI conversion using MPE.

## Project Structure

- `docs/` — build/design references and datasheets
  - `body_shape.md` — body outline design (Jazzmaster × Iceman hybrid)
  - `buffer_circuit.md` — buffer circuit schematic, breadboard layout, and troubleshooting
  - `guitar_build.md` — physical guitar build specs and decisions
  - `pickup_selection.md` — standard magnetic pickup selection (TV Jones)
  - `plan.md` — phased build plan, parts list, signal chain, and technical notes
  - `teensy-4.0.md` — Teensy 4.0 pinout / reference
  - `ubertar-77hc-pickup.md` — Ubertar 77HC pickup reference
  - `wip.md` — current breadboard wiring details
  - `wood_comparison.md` — body / neck / fretboard tonewood comparison
- `firmware/adc_test/` — Phase 1 single-string test sketch (Audio library + USB Audio, YIN-based)
- `firmware/graphicstest/` — ILI9341 TFT display test sketch (Adafruit GFX). Parked nice-to-have — SPI SCLK noise couples into the ADC; needs SPI moved to alternate pins. Not part of the MIDI signal chain.
- `firmware/guitar_midi/` — Phase 2 modular firmware (6-string, MPE MIDI)
  - `adc_sampler.h/.cpp` — timer-driven 20kHz ADC sampling, 6 channels with independent ring buffers
  - `config.h` — all tunable constants (thresholds, sample rate, MIDI settings, per-string config)
  - `guitar_midi.ino` — 6-string orchestrator with staggered pitch detection
  - `midi_output.h/.cpp` — MPE MIDI output with pitch bend tracking (per-channel)
  - `onset_detector.h/.cpp` — note on/off state machine (RMS-based, per-string)
  - `pitch_detector.h/.cpp` — YIN pitch detection algorithm with hysteresis

## Tech Stack

- **Hardware:** Teensy 4.0 (ARM Cortex-M7, 600MHz), Ubertar 77HC single-string pickups, MCP6002 op-amp buffer circuits (runs on 3.3V from Teensy — replaced the TL072 + 9V battery)
- **Firmware:** C++ via Arduino IDE + Teensyduino
- **Libraries:** Teensy ADC library (`ADC.h`), built-in USB MIDI
- **ADC Sampling:** Timer-driven at 20kHz via IntervalTimer, reads all string pins per tick
- **Pitch Detection:** YIN algorithm (cumulative mean normalized difference) with hysteresis
- **MIDI Format:** MPE — each string on its own MIDI channel (channels 2-7)

## Key Constraints

- Teensy 4.0 uses micro-USB (not USB-C)
- Do not power Teensy via VIN and USB simultaneously without cutting the VIN-VUSB trace
- Arduino IDE USB Type must be set to "Serial + MIDI" for Phase 2 firmware
- `usbMIDI` is only available in `.ino` files or via `#include <usb_midi.h>` in `.cpp` files
- MCP6002 runs on 3.3V from the Teensy — no battery needed. (Replaced the TL072, which needed 7V+; weak 9V batteries caused distorted output.) Switching TL072@9V → MCP6002@3.3V roughly halves output swing, so onset/offset thresholds had to be rescaled (or gain raised)
- Gain resistors connect from pin 2 (-IN) to the input bias point — NOT to the output chain (causes short)

## Current Phase

Phase 2 — 6-string expansion. Modular firmware written in `firmware/guitar_midi/`, currently testing with 1 string on A0. MCP6002 swap done — single string is end-to-end working (pickup → MCP6002 buffer → ADC → onset → pitch → MPE MIDI), no 9V battery in the chain. Onset/offset detection working with rescaled MCP6002 thresholds. Expanding to all 6 strings; pitch detection and per-string gain/threshold calibration in progress.
