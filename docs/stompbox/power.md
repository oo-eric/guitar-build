# Power

The box runs from a standard pedalboard supply so it can sit on the board with
everything else. That decision has one hazard attached, and it is fatal.

## Do NOT put 9V on VIN

> **Teensy 4.0's VIN accepts 3.6–5.5V. Nine volts destroys it immediately.**

This is not the Teensy 3.x behaviour. The 9V from the pedalboard supply **must**
be regulated down to 5V before it reaches VIN. That regulator does not exist
yet — it is the main piece of hardware still missing from the box.

## Chain

```
9V DC jack (2.1mm, center-negative)
    |
[Schottky]           reverse-polarity protection (1N5817 or similar).
    |                0.3V drop is irrelevant when dropping to 5V anyway.
    +--[100uF]--[0.1uF]--GND        input filtering, at the jack
    |
[7805 linear regulator]             tab bolted to the enclosure
    |
    +--[100uF]--[0.1uF]--GND        output filtering
    |
   5V --> Teensy VIN
              |
         Teensy's own 3.3V regulator (250mA available)
              |
              +--> preamp board +3V3 (uses ~0.6mA of it)
```

## Linear, not switching — deliberately

A buck converter is the efficient modern choice and it is the wrong one here.

It is a switching supply inside a metal box, centimetres from a six-channel
analog preamp handling 0.1 Vpp signals feeding an ADC that has already cost real
effort to de-noise. This project has lost this fight once already — see
`firmware/experiments/README.md` for what SPI did to the ADC.

At ~150 mA the 7805 dissipates about 0.6W. Bolt the tab to the enclosure and
it is warm and fine. Pay the heat, keep the noise floor.

## Current budget

| Load                        | Draw                         |
| --------------------------- | ---------------------------- |
| Teensy 4.0 @ 600 MHz        | ~100 mA (`../teensy-4.0.md`) |
| MCP6002 preamp × 3          | ~0.6 mA                      |
| Indicator LEDs × 2          | ~10–20 mA                    |
| ILI9341 display + backlight | ~50–80 mA                    |
| **Total**                   | **~200 mA, budget 250**      |

**Check the supply's per-output rating.** Many pedalboard supplies provide
**100 mA** per output — fine for analog stompboxes, not enough for this. Use one
of the higher-current outputs (250 mA / 500 mA) intended for digital pedals.

**Use an isolated output** if the supply has them (Voodoo Lab, Strymon Zuma,
Cioks all do). A cheap non-isolated daisy chain shares ground across every pedal
on the board, and this box already has an amp and a laptop in its grounding
story. Do not add a third path.

## Cut the VUSB trace

Once external power exists, USB and VIN must not both feed the Teensy. Cutting
the VUSB trace makes USB **data-only**.

Consequence worth being deliberate about: after the cut, the Teensy will **not**
run from USB alone. The box needs its power supply at the desk too, not just on
stage. That is normal pedal behaviour and it is the robust choice — the
alternative is relying on never plugging both in at once, which holds until the
night it doesn't. The cut is re-bridgeable with solder, but annoyingly so.
