# MIDI Guitar Build

A DIY guitar with per-string pickups and a Teensy 4.0 for real-time pitch-to-MIDI conversion using MPE.

## Project Structure

- `PLAN.md` — phased build plan, parts list, signal chain, and technical notes
- `BUFFER_CIRCUIT.md` — TL072 buffer circuit schematic, breadboard layout, and troubleshooting
- `firmware/adc_test/` — ADC + pitch detection + MIDI + USB Audio test sketch (YIN-based)
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
- **Libraries:** Teensy Audio library, built-in USB MIDI
- **Pitch Detection:** YIN algorithm (cumulative mean normalized difference)
- **Audio Output:** USB Audio via Teensy Audio library (AudioInputAnalog → AudioOutputUSB)
- **MIDI Format:** MPE — each string on its own MIDI channel (channels 2-7)

## Key Constraints

- Teensy 4.0 uses micro-USB (not USB-C)
- Do not power Teensy via VIN and USB simultaneously without cutting the VIN-VUSB trace
- Target pitch detection latency: <15ms for upper strings
- ADC: using onboard 12-bit via Audio library (ADC2 for audio, ADC1 for pitch detection); may upgrade to PCM1808 (24-bit I2S) if needed
- Arduino IDE USB Type must be set to "Serial + MIDI + Audio" for usbMIDI and USB Audio to compile
- `usbMIDI` is only available in `.ino` files or via `#include <usb_midi.h>` in `.cpp` files
- `AudioInputAnalog` uses ADC2 via DMA; `analogRead()` on pins A0-A9 uses ADC1 — they coexist safely
- Do NOT call `analogReadResolution()` or `analogReadAveraging()` after creating Audio library objects — these modify both ADC1 and ADC2 config registers
- Do NOT use `analogRead()` on pins A12/A13 — those route to ADC2 and conflict with Audio library DMA

## Future Plans

- Physical controls (knobs/switches) on the guitar body for selecting active pickups, controlling MIDI parameters, etc. Not in scope for early phases but should be kept in mind for hardware/firmware architecture decisions.

## Current Phase

Phase 1 — Single string proof of concept. Buffer circuit is wired on breadboard with gain stage (~21-31x via parallel 10K resistors). YIN pitch detection, MIDI output, and USB Audio streaming all working on the Teensy 4.0. Ready to plan Phase 2 (6-string expansion).
