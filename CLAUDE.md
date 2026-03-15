# MIDI Guitar Build

A DIY guitar with per-string pickups and a Teensy 4.0 for real-time pitch-to-MIDI conversion using MPE.

## Project Structure

- `PLAN.md` — phased build plan, parts list, signal chain, and technical notes
- `BUFFER_CIRCUIT.md` — TL072 buffer circuit schematic, breadboard layout, and troubleshooting
- `WIP.md` — current breadboard wiring details
- `firmware/adc_test/` — Phase 1 single-string test sketch (Audio library + USB Audio, YIN-based)
- `firmware/guitar_midi/` — Phase 2 modular firmware (6-string, MPE MIDI)
  - `config.h` — all tunable constants (thresholds, sample rate, MIDI settings, per-string config)
  - `adc_sampler.h/.cpp` — timer-driven 20kHz ADC sampling, 6 channels with independent ring buffers
  - `onset_detector.h/.cpp` — note on/off state machine (RMS-based, per-string)
  - `pitch_detector.h/.cpp` — YIN pitch detection algorithm with hysteresis
  - `midi_output.h/.cpp` — MPE MIDI output with pitch bend tracking (per-channel)
  - `guitar_midi.ino` — 6-string orchestrator with staggered pitch detection

## Tech Stack

- **Hardware:** Teensy 4.0 (ARM Cortex-M7, 600MHz), Ubertar 77HC single-string pickups, TL072 op-amp buffer circuits (switching to MCP6002)
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
- TL072 requires 7V+ minimum — weak 9V batteries cause distorted output. Switching to MCP6002 (runs on 3.3V from Teensy)
- Gain resistors connect from pin 2 (-IN) to the input bias point — NOT to the output chain (causes short)

## Current Phase

Phase 2 — 6-string expansion. Modular firmware written in `firmware/guitar_midi/`, currently testing with 1 string on A0. Onset/offset detection working. Waiting on MCP6002 chips to replace TL072 (eliminates 9V battery dependency). Pitch detection and threshold calibration in progress.
