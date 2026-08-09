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

**Architecture decision (2026-08-09): the electronics do NOT live in the guitar.**
The preamp board is 82 × 156 mm and was never going to fit a control cavity.
Instead the guitar carries only pickups and a 13-pin socket, and everything
else lives in a stompbox-style enclosure connected by a **standard 13-pin
(Roland GK) cable**.

- Mount pickups in the body; wire all six hex outputs plus the magnetic
  pickup to a panel-mount 13-pin DIN socket
- Preamp board + Teensy go in the enclosure (see [13-Pin Interface](#13-pin-interface))
- 1/4" analog output jack on the enclosure (split from buffer circuit)
- USB-C breakout on the **enclosure**, not the body — wire VBUS, GND, D+, D-
  to the Teensy USB pads, replacing the micro-USB connector
- Enclosure: a Hammond **1590DD** (~188 × 120 mm) clears the 82 × 156 mm
  board. The 1590BB and 1590XX are both too small.

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
                GUITAR                    |            ENCLOSURE
                                          |
Guitar String                             |
    |                                     |
[77HC Pickup] x6 ------.                  |
                       |                  |
[Porter magnetic] -----+--> [13-pin  ]====|==> [13-pin ] --+--> [1/4" Jack] (magnetic)
                            [ socket ]  cable  [ socket ]  |
                                          |                '--> [MCP6002 Preamp]
                                          |                      (Teensy 3.3V)
                                          |                          |
                                          |                     [Teensy 4.0] --> [USB-C]
                                          |                                          |
                                          |                                DAW sees MIDI device
```

The guitar end is **entirely passive** — pickups and a socket, no power, no
active parts. See [13-Pin Interface](#13-pin-interface) for the open question
about whether buffers eventually move guitar-side.

## 13-Pin Interface

Guitar-to-enclosure link uses the **standard 13-pin Roland GK connector and
pin assignment**. Own pinout was considered and rejected: conforming costs
nothing, and it makes cables a thing you buy rather than build.

> **Verify the pin numbers against a published GK reference before ordering a
> PCB or drilling a panel.** The assignment below is the widely-used de-facto
> standard, not an official Roland-published spec, and a wrong hole in an
> enclosure is annoying but a wrong trace on a board is a reorder.

| Pin | GK standard       | This build                                 |
| --- | ----------------- | ------------------------------------------ |
| 1   | String 6 (low E)  | Hex channel → ADC                          |
| 2   | String 5 (A)      | Hex channel → ADC                          |
| 3   | String 4 (D)      | Hex channel → ADC                          |
| 4   | String 3 (G)      | Hex channel → ADC                          |
| 5   | String 2 (B)      | Hex channel → ADC                          |
| 6   | String 1 (high E) | Hex channel → ADC                          |
| 7   | Ground            | Common ground                              |
| 8   | Normal pickup     | **Porter magnetic → 1/4" jack.** Free fit. |
| 9   | +7V               | _Unused._ Guitar end is passive.           |
| 10  | −7V               | _Unused._ Guitar end is passive.           |
| 11  | S1 (switch)       | _Unused._ Reserved for future control.     |
| 12  | S2 (switch)       | _Unused._ Reserved for future control.     |
| 13  | Volume            | _Unused._ Reserved for future control.     |

**String-to-ADC direction is not yet decided.** `config.h` maps string index 0
to `A0`, but nothing states whether index 0 is low E or high E. Pick one and
write it down before the cable is wired — it is a one-line firmware change
now and a rewiring job later.

### Why conforming is safe

Both mis-plug directions are harmless, which is the argument for the standard
over a custom pinout:

- **This guitar into real GK gear** — the synth puts ±7V on pins 9/10, which
  connect to nothing here. The hex pickups would be read at the wrong levels
  and impedance, so it would behave oddly, but nothing is damaged.
- **A real GK guitar into this enclosure** — it expects ±7V to run its
  internal preamp, does not get it, and stays silent. Also harmless.

### Open item: buffering

Pins 9/10 stay unused **only while the guitar end is passive**, which means the
raw ~0.1 Vpp pickup signal travels the full cable into a 1 MΩ input. The risks,
worst first: **crosstalk** between six unbuffered high-impedance lines sharing
one jacket (this attacks per-string pitch detection directly), **hum**, and
HF rolloff (least concerning — already low-passing at 4.8 kHz).

Every commercial hex system, GK included, buffers at the guitar. Whether this
one needs to is an empirical question, and there is a cheap test:

> Put a few metres of cable between one pickup and the breadboard preamp.
> Compare idle RMS against the current ~0.014 and check that pitch tracking
> still holds. If idle barely moves, the passive guitar end stands.

If it fails, guitar-side buffers become necessary and pins 9/10 exist for
exactly that — though note the Teensy cannot produce ±7V, so a conforming
supply would need a charge pump or small dual supply in the enclosure.

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

### The magnetic pickup is a passive pass-through

**Pin 8 never touches the preamp board.** It enters the enclosure and goes
straight to the 1/4" jack. Two reasons:

1. The board has exactly six inputs (J1–J6 → A0–A5). There is no seventh.
2. Every channel is a **46× gain stage** sized for a ~0.1 Vpp hex pickup. A
   Filtertron-sized humbucker puts out roughly 0.5–1 Vpp — an order of
   magnitude hotter. Through 46× into a 3.3V rail it clips to a square wave.

**Open — deferred 2026-08-09:** whether to also digitize the magnetic pickup so
it reaches the DAW over USB alongside the MIDI. It is a real option but it is a
**seventh channel at roughly unity gain**, which means a board revision, not a
wiring change. Not scoped yet. In the meantime the analog jack feeds an audio
interface, which covers the desk case.

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
