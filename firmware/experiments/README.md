# Experiments

Sketches that are **not part of the MIDI signal chain** and are not built into
the pedal. Kept because they were useful on the bench and may be again — not
because they are heading toward the enclosure.

Nothing in here should be treated as current firmware. `firmware/guitar_midi/`
is the real one.

## `graphicstest/`

ILI9341 240×320 SPI display test — draws a live waveform from the ADC using
TFT_eSPI + TFT_eSprite.

**Why it's here and not shipping:** it was invaluable for calibrating onset and
offset thresholds on the breadboard, where seeing the actual waveform beat
guessing at RMS numbers. It is the wrong thing to put in a stage pedal, for two
separate reasons:

1. **CPU cost.** A 240×200 sprite push runs ~32 ms (already 4× better than the
   120 ms Adafruit_ILI9341 took). With `PITCH_STAGGER_US = 5000`, a 32 ms block
   stalls six consecutive pitch-detection slots, which shows up as MIDI timing
   jitter. Budget for any blocking display op in the pedal is **~2–3 ms**.
2. **ADC noise.** SPI SCLK on pin 13 sits next to A0 on pin 14; with the TFT
   connected, idle ADC spread went from ~55 to 1000–34000. Tried and failed:
   0.1µF on A0 (killed the signal), queue flush after draw, queue stop/start
   around draw, moving the input to A4, powering the op-amp buffer.

**Worth retesting before writing the display off.** Both measurements above were
taken on a breadboard — long unshielded jumpers, no ground plane. The PCB has
ground pour on both layers and physically separates the analog section from the
digital header, which may change the noise picture substantially. Retest SPI0
(11/12/13) on real hardware before resorting to the bottom-pad alternates
(MOSI 26, MISO 1, SCK 27 via `SPI.setMOSI/setMISO/setSCK` before `tft.init()`).

Note that pin 1 is both SPI1 MISO and Serial1 TX. If MIDI OUT ends up on
Serial1 the two collide — use **Serial2 TX (pin 8)** instead, or simply leave
MISO unconnected, since the ILI9341 is write-only in this application.

**Setup:** `User_Setup.h` lives in
`~/Documents/Arduino/libraries/TFT_eSPI/User_Setup.h` — ILI9341 driver, CS=10,
DC=9, default SPI0 pins, 40 MHz. Not in this repo.

The stage display, if it happens, is a different program: event-driven redraws,
dirty regions only, and a hex tuner. The waveform view stays a bench tool.
