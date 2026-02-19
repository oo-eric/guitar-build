# MIDI Guitar Build

A DIY guitar that functions as a MIDI controller using individual single-string pickups and pitch-to-MIDI conversion.

## Goal

Build a guitar with per-string pickups that converts each string's audio signal into MIDI data in real time, supporting pitch bend and continuous control via the MPE (MIDI Polyphonic Expression) standard.

## Phased Approach

### Phase 1 — Single String Proof of Concept

Validate the entire signal chain with one string before committing to a full build.

**Success criteria:**

- One string reliably triggers MIDI Note On/Off over USB
- Pitch detection latency is acceptable (<15ms for upper strings)
- Pitch bend tracking works when bending the string

### Phase 2 — Expand to 6 Strings

- Full 6-pickup set
- Full 6-pickup set wired to 6 analog inputs on Teensy
- Proper PCB or protoboard layout (6x buffer circuits)
- MPE output: each string on its own MIDI channel

### Phase 3 — Guitar Body Integration

- Mount pickups and electronics into an actual guitar body
- Final wiring, enclosure, and physical build

---

## Phase 1 Parts List

### Core Components

| Part | Purpose | Est. Price | Source | Acquired |
|------|---------|-----------|--------|----------|
| Teensy 4.1 (with pins) | 600MHz ARM Cortex-M7, USB MIDI built-in, 2x 12-bit ADC, 18 analog pins | ~$45 | [PJRC](https://www.pjrc.com/store/teensy41.html) / [Adafruit](https://www.adafruit.com/product/4622) / [SparkFun](https://www.sparkfun.com/teensy-4-1.html) | [ ] |
| Ubertar Little Torpedo (single) | Single-string pickup | $50 | [Ubertar](https://ubertar.com/hexaphonic/one_and_two_string_pickups.html) | [ ] |
| 1/4" mono jack | Connect pickup to circuit | ~$3 | Any electronics supplier | [ ] |

### Prototyping Supplies

| Part | Purpose | Est. Price | Acquired |
|------|---------|-----------|----------|
| Breadboard (full size) | Build circuit without soldering | ~$7 | [ ] |
| Jumper wire kit | Breadboard connections | ~$7 | [ ] |
| USB-C cable | Power + MIDI data to computer | ~$5 | [ ] |
| Single guitar string + tuning peg | Test source (mount on scrap wood) | ~$5 | [ ] |

### Signal Conditioning

| Part | Purpose | Est. Price | Acquired |
|------|---------|-----------|----------|
| TL072 op-amp | Buffer/amplify pickup signal | ~$1 | [ ] |
| Resistor assortment (1/4W) | Biasing and gain setting | ~$5 | [ ] |
| Capacitor assortment (ceramic + electrolytic) | DC blocking, filtering, decoupling | ~$5 | [ ] |
| 9V battery + snap connector | Clean op-amp power (isolated from digital noise) | ~$3 | [ ] |

**Estimated Phase 1 total: ~$135**

---

## Signal Chain

```
Guitar String
    |
[Little Torpedo Pickup]
    |
[1/4" Jack] --> [TL072 Buffer Circuit] --> [Teensy 4.1 Analog Pin]
                 (on breadboard)                   |
                                             [Teensy 4.1]
                                                   |
                                             [USB-C to Computer]
                                                   |
                                           DAW sees MIDI device
```

## Software Stack

- **Arduino IDE + Teensyduino** — development environment
- **Teensy ADC Library** — optimized analog reading, supports high-speed sampling on both ADCs
- **USB MIDI** — built into Teensy hardware, no extra libraries
- **YIN / autocorrelation algorithm** — pitch detection (to be written or adapted)

## Key Technical Challenges

### Pitch Detection Latency

Need ~1-2 full waveform cycles to detect pitch:

- High E (330Hz) → ~6ms (very playable)
- Low E (82Hz) → ~24ms (noticeable)

Mitigations: onset detection (trigger note on attack, refine pitch after), hybrid detection approaches.

### ADC Strategy

**Phase 1: Onboard ADC (simplest start)**
Use Teensy's built-in 12-bit ADC via analog pin. Minimal wiring, no extra hardware. Good enough to validate the concept and test pitch detection.

**Upgrade option: PCM1808 modules**
24-bit stereo ADC, up to 96kHz, I2S interface. ~$5-8 per module. Three modules cover all 6 strings. Significantly cleaner signal which may improve pitch tracking accuracy, especially on low strings. Worth upgrading to if 12-bit proves noisy or if pitch detection struggles.

**Decision point:** After Phase 1, evaluate whether 12-bit resolution is sufficient for reliable pitch detection. If yes, scale with onboard ADC (6 analog pins). If no, switch to PCM1808 modules (3x for 6 strings via I2S).

### MIDI Output Format

Using MPE standard — each string gets its own MIDI channel:

- Channel 1: master channel
- Channels 2-7: one per string
- Per-channel pitch bend for string bends
- Per-channel CC for vibrato / pressure

---

## Research & References

- [Ubertar Hexaphonic Pickups](https://ubertar.com/hexaphonic/one_and_two_string_pickups.html)
- [PJRC Teensy 4.1](https://www.pjrc.com/store/teensy41.html)
- [Teensy ADC Library](https://github.com/pedvide/ADC)
- [Teensy ADC Documentation](https://www.pjrc.com/teensy/adc.html)
- [PCM1808 Datasheet (TI)](https://www.ti.com/lit/ds/symlink/pcm1808.pdf)
- [PCM1808 Breakout Modules](https://www.diymore.cc/products/pcm1808-105db-snr-audio-stereo-adc-single-ended-analog-input-decoder-24bit-amplifier-board-player-diy-electronic-diy-kit)
- [MIDI Polyphonic Expression (MPE) Spec](https://www.midi.org/midi-articles/midi-polyphonic-expression-mpe)

## Notes

_Add build notes, observations, and decisions here as the project progresses._
