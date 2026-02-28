# MIDI Guitar Build

A DIY guitar with per-string pickups and a Teensy 4.1 for real-time pitch-to-MIDI conversion using MPE.

## Project Structure

- `PLAN.md` — phased build plan, parts list, signal chain, and technical notes
- `firmware/` — Teensy 4.1 Arduino/Teensyduino firmware

## Tech Stack

- **Hardware:** Teensy 4.1 (ARM Cortex-M7, 600MHz), Ubertar single-string pickups, TL072 op-amp buffer circuits
- **Firmware:** C++ via Arduino IDE + Teensyduino
- **Libraries:** Teensy ADC library, built-in USB MIDI
- **Pitch Detection:** YIN / autocorrelation algorithm
- **MIDI Format:** MPE — each string on its own MIDI channel (channels 2-7)

## Key Constraints

- Teensy 4.1 uses micro-USB (not USB-C)
- Do not power Teensy via VIN and USB simultaneously without cutting the VIN-VUSB trace
- Target pitch detection latency: <15ms for upper strings
- ADC: starting with onboard 12-bit; may upgrade to PCM1808 (24-bit I2S) if needed

## Future Plans

- Physical controls (knobs/switches) on the guitar body for selecting active pickups, controlling MIDI parameters, etc. Not in scope for early phases but should be kept in mind for hardware/firmware architecture decisions.

## Current Phase

Phase 1 — Single string proof of concept. Validate the full signal chain with one string before scaling to six.
