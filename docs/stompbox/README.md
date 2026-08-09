# Stomp Box

The enclosure that holds everything except the pickups. Decided 2026-08-09 —
see `../plan.md` → "Phase 3" for why the electronics left the guitar.

- [`power.md`](power.md) — 9V pedalboard supply, regulation, the VIN hazard
- [`controls.md`](controls.md) — footswitches, LEDs, display
- [`pin_map.md`](pin_map.md) — **Teensy pin assignments. Single source of truth.**
- [`prior_art.md`](prior_art.md) — pi-Stomp Core: what to steal, what doesn't apply

## What's in the box

|               |                                                  |
| ------------- | ------------------------------------------------ |
| Preamp board  | 6-channel MCP6002, 82 × 156 mm, `hardware/`      |
| Teensy 4.0    | Socketed (both rows — mechanical stability)      |
| Power section | 9V in → 5V → VIN. Does not exist yet             |
| MIDI OUT      | 5-pin DIN + resistor network. Does not exist yet |
| Footswitches  | 4, momentary                                     |
| Display       | ILI9341 240×320 SPI                              |

## I/O

| Connector            | Direction | Notes                                                                       |
| -------------------- | --------- | --------------------------------------------------------------------------- |
| 13-pin DIN           | in        | From the guitar. Roland GK standard — see `../plan.md` → "13-Pin Interface" |
| MIDI OUT (5-pin DIN) | out       | To a hardware synth. **The stage path**                                     |
| 1/4" jack            | out       | Magnetic pickup passthrough → amp. Passive, never touches the preamp        |
| USB-C                | data      | To the laptop. **Desk-only.** Data only once the VUSB trace is cut          |
| 9V DC                | power     | 2.1 mm, center-negative, pedalboard standard                                |

Panel convention follows pedal practice — signal right to left as you face it:

```
        ╔══════════════════════════════════════════════╗
 1/4"   ║              [DC 9V]  [USB-C]                ║   13-pin
 MIDI ──╢                  (display)                   ╟── IN
  OUT   ║   (o)      (o)      (o)      (o)             ║
        ║  PANIC    MODE    PATCH-   PATCH+            ║
        ╚══════════════════════════════════════════════╝
```

## Enclosure

**Decided 2026-08-09: custom build.** Not a stock Hammond. That removes the
space constraint, so the four footswitches stay _and_ an encoder can be added
— see [`controls.md`](controls.md). The encoder was originally a way to cut
switches down to two and fit a 1590DD; that trade no longer has to be made.

For reference, ~45 mm centers is proven spacing (pi-Stomp fits three
footswitches, a colour TFT and two knobs into a 145 mm-wide 1590J). With a
custom box there's no reason to crowd it — use **50 mm** and have the room.

### Spec for the builder

|                 |                                                                                                                            |
| --------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Width           | **~215 mm** — 4 switches × 50 mm = 150 mm span, plus margins                                                               |
| Depth           | Enough for the 82 × 156 mm board laid with its **long dimension across the width**, plus the footswitch row                |
| Internal height | **~50 mm** — board + standoffs (~15 mm) plus footswitch body behind the panel (~30 mm). The switches mount above the board |
| Top panel       | **Slanted.** A screen at floor level must be angled up to be readable                                                      |
| Side walls      | Tall enough for panel-mount jacks (~20 mm)                                                                                 |
| Material        | **Metal, not wood** — see below                                                                                            |

### Metal, and bond it

Use an aluminium or steel enclosure and **bond the chassis to circuit ground at
exactly one point**, conventionally at the input jack.

This is not cosmetic. The box contains a six-channel analog preamp handling
0.1 Vpp signals next to a 600 MHz microcontroller and an SPI display. A metal
enclosure is a Faraday cage around the analog section; a wooden one is a nice
looking box that does nothing. Given this project's history with the ADC —
`firmware/experiments/README.md` — take the shielding.

Single-point bonding matters as much as the metal: ground the chassis in two
places and the enclosure itself becomes a loop.

### Sequencing — box and board in parallel

Custom metalwork raises a chicken-and-egg: does the board fit the box, or the
box fit the board?

**Neither, if Rev B uses peripheral headers** (the pi-Stomp lesson in
[`prior_art.md`](prior_art.md)). With switches, LEDs, display and MIDI on
headers and ribbon cable, the board can sit anywhere inside and the panel
layout can change without a board respin. Dave can start once he has the
outside dimensions; the board only needs to fit _within_ them.

Without headers, the panel layout has to be frozen before the board is routed,
and every change after that is a reorder.

## Two stage-critical consequences

**No laptop means no USB power.** The laptop was supplying the Teensy. The
power section is not a convenience — it is what makes the stage rig possible at
all. See [`power.md`](power.md).

**Most hardware synths do not speak MPE.** The firmware puts each string on its
own channel (2–7) with per-channel pitch bend. An ordinary synth either listens
to one channel and plays one string, or goes omni and turns six independent
bends into garbage. Hence the MODE footswitch. See [`controls.md`](controls.md).

## Ground loops are a desk-only problem

A loop needs two paths to earth. On stage there is no laptop, so there is only
the amp — no loop. At the desk, USB to the computer plus 1/4" to an interface
gives you both, and 60 Hz hum becomes possible.

That makes the DI/ground-lift question a studio question, not a live one. Many
interfaces have enough isolation that it never appears. Test before solving it.

## Open

- **Rev B** — the current PCB is a preamp and nothing else. Power regulation,
  MIDI OUT, footswitch and LED headers, and a display header are all
  unrepresented, so today they would be perfboard and flying leads. Not scoped.
- **The cable test** (`../plan.md` → "13-Pin Interface") still gates ordering
  any board. Do not fab before running it.
- **A 1/4" jack on the guitar as well.** Pin 8 is passive, so the magnetic
  pickup drives the whole 13-pin cable before anything buffers it — that rolls
  off highs and shifts the resonant peak. A second jack on the guitar costs one
  hole and lets you bypass the multicore when analog tone matters. Cheaper to
  drill now than later.
- **Digitizing the magnetic pickup** — deferred, see `../plan.md`.
