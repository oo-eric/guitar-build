# Teensy 4.0 pin map — single source of truth

Every pin the stomp box uses. **Check here before assigning anything new** —
this conversation has already produced one collision (pin 1) that would have
been silent until the display and MIDI were tested together.

## Physical layout

Teensy 4.0 has 14 pins per side. USB at the top.

```
              ___USB___
      GND  --|         |--  Vin      <- 5V from the power section
        0  --|         |--  GND
        1  --|  ! ! !  |--  3.3V     -> preamp board
        2  --|         |--  23
        3  --|         |--  22
        4  --|         |--  21
        5  --|         |--  20       <- flanks the analog block, keep clear
        6  --|         |--  19 / A5
        7  --|         |--  18 / A4
        8  --|         |--  17 / A3
        9  --|         |--  16 / A2
       10  --|         |--  15 / A1
       11  --|         |--  14 / A0
       12  --|_________|--  13       <- flanks the analog block. SPI0 SCK
```

**The rule:** analog lives on the right column. Keep switching digital signals
on the left column. Pins **13** and **20** flank the analog block and are the
two most dangerous places to put anything that toggles.

## Assignments

| Pin   | Use                       | Notes                                              |
| ----- | ------------------------- | -------------------------------------------------- |
| 0     | LED halo — PANIC          | Left column, away from analog                      |
| **1** | **RESERVED — do not use** | Collision: Serial1 TX _and_ SPI1 MISO. See below   |
| 2     | Footswitch — PANIC        | Momentary, Bounce2                                 |
| 3     | Footswitch — MODE         | Momentary, Bounce2                                 |
| 4     | Footswitch — PATCH −      | Momentary, Bounce2                                 |
| 5     | Footswitch — PATCH +      | Momentary, Bounce2                                 |
| 6     | Encoder — switch (click)  | Bounce2, same as the footswitches                  |
| 7     | Encoder — A               | `Encoder.h`                                        |
| 8     | **MIDI OUT TX**           | Serial2 TX → 5-pin DIN resistor network            |
| 9     | TFT DC                    |                                                    |
| 10    | TFT CS                    |                                                    |
| 11    | TFT MOSI                  | SPI0                                               |
| 12    | Encoder — B               | `Encoder.h`                                        |
| 13    | TFT SCK                   | SPI0. **Known noise risk** — see below             |
| 14–19 | **A0–A5, preamp inputs**  | Six hex channels from the board's J7 header        |
| 20    | **keep clear**            | Flanks A5. Nothing that toggles                    |
| 21    | LED halo — MODE           | Right column, but LEDs only switch on state change |
| 22    | LED halo — PATCH −        | ditto                                              |
| 23    | LED halo — PATCH +        | ditto                                              |
| 3.3V  | → preamp board            | Teensy's regulator, 250 mA available, ~0.6 mA used |
| Vin   | ← 5V from power section   | **Never 9V.** See [`power.md`](power.md)           |

## The budget is now full

Every perimeter pin is allocated except pin 1 (reserved) and pin 20 (kept
clear). There is **no spare**.

Two things that had to give to make it fit:

- **No separate MIDI-activity LED.** The four halos cover switch state; MIDI
  activity goes on the display instead. Reinstating it costs a pin nobody has.
- **Three halos sit on the right column** (21–23). LEDs only change on a state
  change — not continuously like SPI — so the coupling risk is much lower than
  pin 13's. Pin 20 stays empty as the buffer next to A5.

**Relief valves, if something else needs a pin:**

1. **Drive the halos from a 74HC595** on the existing SPI bus. One latch pin
   replaces four LED pins, freeing three, and the shift register can drive more
   LEDs later at no extra pin cost.
2. **Bottom-side pads (24–33)** are unused. Fine for low-speed signals, awkward
   to reach once the Teensy is socketed.

Take option 1 before option 2.

## Collision: pin 1

Pin 1 is **Serial1 TX** and **SPI1 MISO** at the same time. Both were candidates:
Serial1 was the obvious choice for MIDI OUT, and SPI1 is the escape route for
the display's noise problem.

Resolved two ways, and both are applied:

- MIDI OUT uses **Serial2 TX (pin 8)** instead. Serial3 and Serial4 land on
  A0–A3 and are unusable; Serial2 (RX 7 / TX 8) is clear of everything
- The **ILI9341 is write-only** — TFT_eSPI runs fine with no MISO defined, so
  SPI1 MISO would not be needed even if SPI1 were used

Pin 1 stays reserved rather than reassigned, so the conflict can't reappear.

## Known risk: SCK on pin 13

SPI0's clock is fixed at pin 13, directly adjacent to pin 14 / A0. On the
breadboard, connecting the TFT drove idle ADC spread from ~55 to 1000–34000.

**Plan A: retest on the PCB before designing around it.** That measurement came
from a breadboard — long unshielded jumpers, no ground plane. The board has
ground pour on both layers and separates the analog section from the digital
header. The picture may change substantially.

**Plan B, only if A fails:** move to SPI1 — MOSI 26, MISO 1, SCK 27 — via
`SPI.setMOSI(26); SPI.setMISO(1); SPI.setSCK(27);` before `tft.init()`. Note
that **26 and 27 are bottom-side SMT pads, not perimeter pins**, so socketing
the Teensy does not expose them; this means soldering fine wires to the
underside of a chip that then sits in a socket. It is the awkward path, which is
why it is Plan B.

Fixes already tried and ruled out on the breadboard: 0.1 µF on A0 (killed the
signal), queue flush after draw, queue stop/start around draw, moving the input
to A4, powering the op-amp buffer.

## Preamp header order

The board's 8-pin Teensy header (J7) is **not** in A0–A5 order. Physical order
is `GND, +3V3, A1, A0, A3, A2, A5, A4` — chosen so the six ADC runs fan into the
connector without crossing. **Wire it from the silkscreen labels, not from
memory.**
