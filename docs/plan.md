# MIDI Guitar Build

A DIY guitar that functions as a MIDI controller using individual single-string pickups and pitch-to-MIDI conversion.

## Goal

Build a guitar with per-string pickups that converts each string's audio signal into MIDI data in real time, supporting pitch bend and continuous control via the MPE (MIDI Polyphonic Expression) standard.

## Phased Approach

### Phase 1 — Single String Proof of Concept

Validate the entire signal chain with one string before committing to a full build.

**Status: Complete**

**Success criteria:**

- [x] One string reliably triggers MIDI Note On/Off over USB
- [x] Pitch detection latency is acceptable (~34ms with 1536-sample buffer at 44100 Hz)
- [x] USB Audio streaming working (combined pickup audio visible as audio input on computer)
- [ ] Pitch bend tracking works when bending the string

### Phase 2 — Expand to 6 Strings

**Status: In Progress**

- Full 6-pickup set wired to 6 analog inputs on Teensy (A0-A5, manual analogRead via ADC library)
- 3x MCP6002 op-amps (replacing TL072 — runs on Teensy 3.3V, no battery needed)
- Per-string gain resistors (high strings need more gain than low strings)
- MPE output: each string on its own MIDI channel (channels 2-7)
- 6 independent YIN pitch detectors (staggered — one per 5ms tick, each string checked every 30ms)
- RMS-based onset/offset detection with hysteresis and retrigger blocking
- Pitch bend tracking during sustain
- No USB Audio for Phase 2 (MIDI only, simplifies architecture)
- Firmware: modular `guitar_midi/` directory (config.h, adc_sampler, onset_detector, pitch_detector, midi_output)

### Phase 3 — Guitar Body Integration

- Mount pickups and electronics into an actual guitar body
- Final wiring, enclosure, and physical build
- 1/4" analog output jack (split from buffer circuit)
- USB-C breakout board mounted on body — wire VBUS, GND, D+, D- to Teensy USB pads, replacing the micro-USB connector

---

## Phase 1 Parts List

### Core Components

| Part                      | Purpose                                                                                               | Est. Price | Source                                                                    | Acquired |
| ------------------------- | ----------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------- | -------- |
| Teensy 4.0 (with pins)    | 600MHz ARM Cortex-M7, USB MIDI built-in, 2x 12-bit ADC, 14 analog pins                                | ~$30       | [Adafruit](https://www.adafruit.com/product/4323)                         | [x]      |
| Ubertar 77HC Pickups (x6) | Single-string pickup (upgraded from HC series by Ubertar — more powerful, better sound, more durable) | $50        | [Ubertar](https://ubertar.com/hexaphonic/one_and_two_string_pickups.html) | [x]      |
| 1/4" mono jack            | Connect pickup to circuit                                                                             | ~$3        | DigiKey / Mouser                                                          | [ ]      |

### Prototyping Supplies

| Part                                     | Purpose                                               | Est. Price | Source                                           | Acquired |
| ---------------------------------------- | ----------------------------------------------------- | ---------- | ------------------------------------------------ | -------- |
| Breadboard (full size, 830 pts)          | Build circuit without soldering                       | $5.95      | [Adafruit](https://www.adafruit.com/product/239) | [x]      |
| Jumper wire bundle                       | Breadboard connections                                | ~$7        | [Adafruit](https://www.adafruit.com/product/153) | [x]      |
| USB-C to micro-USB cable                 | Power + MIDI data to computer (Teensy uses micro-USB) | ~$5        | Any                                              | [x]      |
| Male header pins (breakaway strip, 2x40) | Solder onto Teensy for breadboard mounting            | ~$2        | DigiKey / Adafruit                               | [x]      |
| Single guitar string + tuning peg        | Test source (mount on scrap wood)                     | ~$5        | Any music store                                  | [x]      |

### Signal Conditioning (Phase 1 — original, TL072 + 9V battery)

| Part                                   | Purpose                                          | Est. Price | Source                                            | Acquired |
| -------------------------------------- | ------------------------------------------------ | ---------- | ------------------------------------------------- | -------- |
| TL072 op-amp (x2)                      | Buffer/amplify pickup signal                     | ~$2        | DigiKey / Mouser                                  | [x]      |
| 10K resistors (25 pack)                | Voltage divider biasing                          | $0.75      | [Adafruit](https://www.adafruit.com/product/2784) | [x]      |
| 100K resistors (25 pack)               | Op-amp gain/feedback                             | $0.75      | [Adafruit](https://www.adafruit.com/product/2787) | [x]      |
| 0.1uF ceramic capacitors (10 pack)     | Decoupling                                       | $0.95      | [Adafruit](https://www.adafruit.com/product/753)  | [x]      |
| 10uF electrolytic capacitors (10 pack) | DC blocking, power filtering                     | $1.50      | [Adafruit](https://www.adafruit.com/product/2195) | [x]      |
| 9V battery snap connector (wire leads) | Clean op-amp power (isolated from digital noise) | ~$2        | DigiKey / Amazon                                  | [x]      |
| 9V battery                             | Power for op-amp                                 | ~$3        | Any                                               | [x]      |

### Signal Conditioning (Phase 2 — upgraded, MCP6002 + Teensy 3.3V power)

Switching from TL072 (needs 7V+) to MCP6002 (runs on 1.8-6V, rail-to-rail). Powered directly from Teensy 3.3V — no battery needed.

| Part                                   | Purpose                                              | Est. Price | Source         | Acquired |
| -------------------------------------- | ---------------------------------------------------- | ---------- | -------------- | -------- |
| MCP6002 (DIP-8) x3                     | Dual op-amp, 2 channels each, covers all 6 strings   | ~$3        | DigiKey/Mouser | [ ]      |
| 2.2K resistors (pack)                  | Gain resistor (~46x with 100K feedback)              | ~$1        | DigiKey/Mouser | [ ]      |
| 1K resistors (pack)                    | Alternate gain resistor (~101x) if 46x isn't enough  | ~$1        | DigiKey/Mouser | [ ]      |
| 10K resistors (25 pack)                | Voltage dividers — need 24 more (4 per channel)      | $0.75      | Adafruit       | [ ]      |
| 100K resistors                         | Feedback — need 6 (one per channel), may have enough | —          | —              | [x]      |
| 10uF electrolytic capacitors (10 pack) | DC blocking — need 12 more (2 per channel)           | $1.50      | Adafruit       | [ ]      |
| 0.1uF ceramic capacitors               | Decoupling — need 3 (one per chip), may have enough  | —          | —              | [x]      |
| Second breadboard (830 pts)            | 6 channels won't fit on one board                    | $5.95      | Adafruit       | [ ]      |

**Estimated Phase 2 order: ~$265**

---

## Signal Chain

```
Guitar String
    |
[77HC Pickup]
    |
[1/4" Jack] --> [MCP6002 Buffer Circuit] --> [Teensy 4.0 Analog Pin]
                 (powered by Teensy 3.3V)          |
                                             [Teensy 4.0]
                                                   |
                                             [micro-USB to Computer]
                                                   |
                                           DAW sees MIDI device
```

## Software Stack

- **Arduino IDE + Teensyduino** — development environment
- **Teensy ADC Library** — optimized analog reading, supports high-speed sampling on both ADCs
- **USB MIDI** — built into Teensy hardware, no extra libraries
- **YIN algorithm** — pitch detection (cumulative mean normalized difference, implemented and working)
- **Teensy Audio Library** — USB audio streaming (AudioInputAnalog → AudioOutputUSB)

## Key Technical Challenges

### Pitch Detection Latency

Need ~1-2 full waveform cycles to detect pitch:

- High E (330Hz) → ~6ms (very playable)
- Low E (82Hz) → ~24ms (noticeable)

Mitigations: onset detection (trigger note on attack, refine pitch after), hybrid detection approaches.

### ADC Strategy

**Phase 1: Onboard ADC (validated)**
Teensy's built-in 12-bit ADC works for pitch detection. The Audio library's `AudioInputAnalog` uses ADC2 via DMA for USB audio streaming. Manual `analogRead()` on A1-A6 uses ADC1 for per-string pitch detection — these coexist safely on separate ADC hardware units.

**Important ADC constraints:**

- Do NOT call `analogReadResolution()` or `analogReadAveraging()` after Audio library init — these modify both ADC1 and ADC2 registers, corrupting Audio library's DMA setup.
- Pins A12/A13 route to ADC2 — do not use with `analogRead()` when Audio library is active.
- Consider using Teensy ADC library (`ADC.h` by pedvide) for explicit ADC1 targeting if per-ADC configuration is needed.

**Upgrade option: PCM1808 modules**
24-bit stereo ADC, up to 96kHz, I2S interface. ~$5-8 per module. Three modules cover all 6 strings. Worth upgrading to if pitch detection struggles with 12-bit resolution.

### MIDI Output Format

Using MPE standard — each string gets its own MIDI channel:

- Channel 1: master channel
- Channels 2-7: one per string
- Per-channel pitch bend for string bends
- Per-channel CC for vibrato / pressure

### Audio Output Strategy

**Dual output — USB audio + 1/4" analog jack:**

The pickup signal splits at the buffer circuit. One path feeds the Teensy ADC for pitch detection (and optionally USB audio), the other goes straight to a standard 1/4" output jack for a traditional analog signal.

- **1/4" jack:** Zero-latency analog output, works without a computer (amps, pedalboards, DI boxes)
- **USB audio:** Teensy supports "Serial + MIDI + Audio" USB type, allowing combined MIDI + raw audio over a single USB cable. The DAW sees both a MIDI instrument and an audio input from one device.

**USB Audio: Implemented.** Teensy Audio library streams combined pickup audio over USB (Arduino IDE USB Type = "Serial + MIDI + Audio"). Computer sees both a MIDI device and an audio input from one USB connection. The 1/4" analog jack remains a Phase 3 addition for the physical build.

---

## Research & References

- [Ubertar Hexaphonic Pickups](https://ubertar.com/hexaphonic/one_and_two_string_pickups.html)
- [PJRC Teensy 4.0](https://www.pjrc.com/store/teensy40.html)
- [Teensy ADC Library](https://github.com/pedvide/ADC)
- [Teensy ADC Documentation](https://www.pjrc.com/teensy/adc.html)
- [PCM1808 Datasheet (TI)](https://www.ti.com/lit/ds/symlink/pcm1808.pdf)
- [PCM1808 Breakout Modules](https://www.diymore.cc/products/pcm1808-105db-snr-audio-stereo-adc-single-ended-analog-input-decoder-24bit-amplifier-board-player-diy-electronic-diy-kit)
- [MIDI Polyphonic Expression (MPE) Spec](https://www.midi.org/midi-articles/midi-polyphonic-expression-mpe)

## Future Exploration

### MPU-6050 Accelerometer/Gyroscope (HW-123)

6-axis motion sensor (3-axis accelerometer + 3-axis gyroscope) that communicates over I2C. Could be mounted on the guitar body or neck to generate MIDI CC data from physical gestures — tilt for filter sweeps, shake for vibrato, orientation for effect parameters, etc. Teensy 4.0 has multiple I2C buses so integration should be straightforward.

## Notes

- **Op-amp change:** TL072 requires 7V+ and a 9V battery that drains fast (especially rechargeable). Switching to MCP6002 which runs on 3.3V from the Teensy directly — no battery needed.
- **Gain findings:** 77HC pickup signal is very weak for single strings. Unity gain and 11x were not enough. Need ~46-101x gain depending on string. High strings need more gain than low strings.
- **USB-C breakout board:** Available with VBUS, GND, CC1, CC2, D+, D- pins. Could be used for USB-C connector on guitar body in Phase 3 (passthrough to Teensy micro-USB).
