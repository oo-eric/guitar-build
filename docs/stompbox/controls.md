# Controls — footswitches, LEDs, display

## Footswitches

Four, in the order they earn their place:

| Switch      | Function                             | Why                                                                                                                                                                                                        |
| ----------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **PANIC**   | All Notes Off (CC 123), all channels | The song-ender. Note-offs come from an RMS threshold, and thresholds miss. With no laptop on stage, nothing else can stop a hardware synth droning. Every commercial MIDI guitar interface has this button |
| **MODE**    | MPE ↔ single-channel                 | Most hardware synths do not speak MPE (below)                                                                                                                                                              |
| **PATCH −** | Program Change down                  | Change synth sounds without walking back to the rack                                                                                                                                                       |
| **PATCH +** | Program Change up                    | ditto                                                                                                                                                                                                      |

**MUTE is resolved, and it is not a footswitch.** It went to the guitar — first
as a momentary S1 (2026-09-02), now as the "Guitar only" position of a
Guitar / Mix / MIDI mode switch on GK pin 10 (2026-09-18) — stopping notes for tuning or between-song silence is something
you do while holding the instrument, not something you kick. See
[`../guitar_wiring.md`](../guitar_wiring.md). The floor keeps PANIC, which is
the different job: cleanup after a missed note-off rather than prevention.

Patch stepping lives here only. It was briefly also on a guitar momentary; the
mode switch that replaced those switches is latched, so it can't step.

**Settled: all four stay.** The encoder was floated as a way to drop to two
switches and fit a stock 1590DD. The box is custom
([`README.md`](README.md)), so that trade is off — the panel has room for both.

**LED halos.** Ring the switches themselves rather than placing indicators
elsewhere on the panel — the state appears where the eye already is. See
[`prior_art.md`](prior_art.md).

## Rotary encoder

Now an addition rather than a substitute, and worth including.

Footswitches are for what you do **with your feet, mid-song** — they are
coarse, and there are four of them. The moment the display grows past two or
three screens, something has to navigate menus, and stomping through a list
with a boot is miserable. pi-Stomp navigates its entire interface — pedalboard
select, preset select, deep parameter editing, global settings — through one
encoder with a push-click.

Put it on the upper panel near the display, where a hand reaches it during
setup. It costs one component and three pins (A, B, switch), and the pin budget
has room — see [`pin_map.md`](pin_map.md).

What it should drive:

- Menu navigation and settings on the display
- Patch browsing at setup time (PATCH ± footswitches stay for mid-song jumps)
- Anything the display grows later — calibration, per-string gain trim,
  threshold tuning

Use `Encoder.h` (bundled with Teensyduino) and debounce the push-click with
Bounce2 like the footswitches.

### Momentary, not latching

Both work. Latching (3PDT) makes the switch position _be_ the state — simple,
survives reboot. Momentary makes firmware hold the state — costs a variable and
a debounce, but scales to three modes later without rewiring.

**Use momentary**, and store the current mode in the Teensy's emulated EEPROM
(1080 bytes, currently unused) so the box powers up in the mode it was left in.
That removes latching's only real advantage. Debounce with Bounce2, which
Teensyduino already bundles.

### The MPE problem this exists to solve

The firmware puts each string on its own MIDI channel (2–7) with per-channel
pitch bend. Feed that to a synth that isn't MPE-aware and either it listens on
one channel and you hear a single string, or it goes omni and six independent
pitch bends become garbage.

- **MPE mode** — channels 2–7, per-string bend. DAW and MPE-capable gear
- **Single-channel mode** — all six strings on one channel, pitch bend
  suppressed or global. Everything else

Secondary benefit: DIN MIDI runs at 31250 baud ≈ 3125 bytes/sec. Current traffic
(6 strings, ~20 ms updates, 3 bytes) is ~900 B/s and fits fine, but MPE bend
streams are what overruns a DIN link if that interval ever tightens.
Single-channel mode removes the risk.

## LEDs

Two, and **not on pin 13** — that pin is the onboard LED, shared with SPI SCLK,
and sits directly next to A0. It is the exact adjacency that wrecked the ADC
during the display experiments. Put LEDs on the left-hand column, physically
opposite the analog pins. See [`pin_map.md`](pin_map.md).

Keep LEDs even with a display fitted. On a dark stage mid-song you **glance**,
you don't read. A screen tells you everything in two seconds; an LED tells you
one thing in zero.

- **MODE** — which MIDI mode is active
- **MIDI activity** — proof the box is alive and sending
- **MIDI MUTE** — lit when the guitar's mode switch is on "Guitar only" (or no
  guitar is plugged in). Recommended, no longer required: the lever already
  shows it at the guitar, so this lamp is
  for whoever is looking at the floor instead

The halos moved to a 74HC595 to free pins for the guitar controls, which leaves
four spare outputs — enough for the mute lamp and the activity LED that was
previously cut for lack of a pin. See [`pin_map.md`](pin_map.md).

## Display

ILI9341 240×320 SPI, already owned and working. Two constraints govern it, both
learned the hard way — full writeup in `firmware/experiments/README.md`.

### Budget: ~2–3 ms per blocking operation

The ADC sampler is on an IntervalTimer, so it never misses a sample regardless
of the display. What suffers is **YIN in the main loop**. With
`PITCH_STAGGER_US = 5000`, one string is analysed every 5 ms — a 32 ms blocking
`pushSprite` stalls six consecutive slots and shows up as MIDI timing jitter.

How to stay inside the budget, cheapest first:

1. **Redraw on change, not on a frame timer.** Mode changes when stomped. Patch
   number changes when stomped. There is no reason for a render loop
2. **Dirty regions only.** Render time scales with pixel count — a 40 × 30 px
   patch number is 0.25% of a 240 × 200 sprite
3. **Drop color depth.** 240 × 200 at 16bpp is 96 KB. An 8-bit sprite halves the
   transfer; nothing in this UI needs 65k colors
4. **DMA** if large updates are still needed. TFT_eSPI supports it on Teensy 4,
   and the 32-channel DMA controller is idle. Converts a 32 ms block into ~0 ms
   of CPU. Note it does **not** help the noise problem — SCLK still toggles

### Tuner mode is allowed to be expensive

When tuning you are not playing, so MIDI latency doesn't matter. The one mode
that wants a fast refresh is the one where the CPU is free. Full-screen
redraws, 16-bit color, whatever looks good.

**A six-string tuner is the best argument for the screen.** YIN already runs per
string — all six strings at once, no switching, no plucking one at a time, is
nearly free firmware on hardware already owned.

### Not shipping: the waveform view

Invaluable for calibrating thresholds on the breadboard, and the single most
expensive thing that could go on a stage display. It stays a bench tool in
`firmware/experiments/graphicstest/`.
