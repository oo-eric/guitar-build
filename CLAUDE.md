# MIDI Guitar Build

A DIY guitar with per-string pickups and a Teensy 4.0 for real-time pitch-to-MIDI conversion using MPE.

## Project Structure

- `PLAN.md` — phased build plan, parts list, signal chain, and technical notes
- `BUFFER_CIRCUIT.md` — TL072 buffer circuit schematic, breadboard layout, and troubleshooting
- `firmware/adc_test/` — simple ADC test sketch for validating the buffer circuit
- `firmware/guitar_midi/` — Teensy 4.0 Arduino/Teensyduino firmware
  - `config.h` — all tunable constants (thresholds, sample rate, MIDI settings)
  - `adc_sampler.h/.cpp` — timer-driven 20kHz ADC sampling with ring buffer
  - `onset_detector.h/.cpp` — note on/off state machine (RMS-based)
  - `pitch_detector.h/.cpp` — YIN pitch detection algorithm
  - `midi_output.h/.cpp` — MPE MIDI output with pitch bend tracking
  - `guitar_midi.ino` — main entry point and orchestration loop

## Tech Stack

- **Hardware:** Teensy 4.0 (ARM Cortex-M7, 600MHz), Ubertar 77HC single-string pickups, TL072 op-amp buffer circuits
- **Firmware:** C++ via Arduino IDE + Teensyduino
- **Libraries:** Teensy ADC library, built-in USB MIDI
- **Pitch Detection:** YIN / autocorrelation algorithm
- **MIDI Format:** MPE — each string on its own MIDI channel (channels 2-7)

## Key Constraints

- Teensy 4.0 uses micro-USB (not USB-C)
- Do not power Teensy via VIN and USB simultaneously without cutting the VIN-VUSB trace
- Target pitch detection latency: <15ms for upper strings
- ADC: starting with onboard 12-bit; may upgrade to PCM1808 (24-bit I2S) if needed
- Arduino IDE USB Type must be set to "Serial + MIDI" for usbMIDI to compile
- `usbMIDI` is only available in `.ino` files or via `#include <usb_midi.h>` in `.cpp` files

## Future Plans

- Physical controls (knobs/switches) on the guitar body for selecting active pickups, controlling MIDI parameters, etc. Not in scope for early phases but should be kept in mind for hardware/firmware architecture decisions.

## Current Phase

Phase 1 — Single string proof of concept. Buffer circuit is wired on breadboard, currently testing ADC readings to validate the signal chain before moving to pitch detection.
