# Prior art — pi-Stomp Core

- Wiki: <https://www.treefallsound.com/wiki/doku.php?id=pi-stomp_core>
- Source: <https://github.com/TreeFallSound/pi-stomp>

An open-source DIY multi-effects stompbox platform from Tree Fall Sound.
Raspberry Pi (1.4 GHz quad-core) running MOD with 350+ LV2 plugins, 24-bit
48–96 kHz stereo audio, 2.67 ms latency. Over 110 built in 20+ countries.

**The signal path is irrelevant to us** — they do real-time audio DSP on Linux,
we do pitch→MIDI on a microcontroller, and we are explicitly not doing audio
synthesis on the Teensy. What transfers is the **chassis**: footswitches,
display, DIN MIDI, jacks, power, enclosure. Those problems are identical, and
theirs are solved and shipping.

## Take: headers for every peripheral, not hard-wiring

pi-Stomp Core's whole premise. The board exposes headers — display (SPI),
momentary switches (up to 5, with debounce), analog controls (up to 8 via ADC),
UART for DIN MIDI, plus 3 uncommitted GPIO — and the builder decides the panel.

> "This is possible by providing interface headers for all of the peripheral
> functions."

**Why this matters for Rev B:** the panel layout is not settled and won't be
until Dave builds something. Headers decouple the board from the metalwork.
Hard-wire the switches and every layout change is a board reorder — $40 and two
weeks. This is the single most valuable idea on the page.

## Take: LED halos on the footswitches

Their footswitches have LED rings around the switch itself rather than separate
indicator LEDs elsewhere on the panel. Better answer to the glanceability
problem in [`controls.md`](controls.md) — the state appears where the eye is
already going, which matters on a dark stage mid-song.

## Take: encoder for navigation, footswitches only for performance

pi-Stomp does _all_ menu work — pedalboard select, preset select, deep parameter
editing, global settings — through **one rotary encoder**, and reserves
footswitches for what you actually do with your feet during a song.

Applied here: **PATCH ± is setup-time browsing, not performance.** An encoder
handles it, plus whatever the display grows into later. That would take the
footswitch count from four to **two — PANIC and MODE** — which fits a stock
enclosure comfortably and removes the custom-box requirement.

**Open decision.** It changes the enclosure spec, so settle it before any metal
is cut. See the table in [`README.md`](README.md).

## Take: buy the DIN MIDI breakout

> "UART header for serial communication or DIN MIDI In/Out (optional $10
> module)"

Confirms not hand-building the resistor network, and sidesteps the unresolved
3.3V resistor-value question in [`controls.md`](controls.md).

## Confirmations

- **1 MΩ buffered input impedance** — matches our `Rbias`. Independent
  confirmation that value is right for a passive pickup.
- **Footswitch spacing ~45 mm** — three switches plus a TFT and two knobs in a
  145 mm-wide 1590J. Corrected our earlier 50–60 mm estimate.
- **Total cost ~$160–200** including Pi, audio card, TFT, enclosure and power.
  Useful sanity check; our parts count is smaller.
- They publish an **Enclosure Consideration Guide** and tell builders to read it
  _before_ building, because build choices depend on the box. Same conclusion we
  reached independently.

## Does not transfer

- **Hardware debounce.** They debounce in hardware because Linux has no reliable
  interrupt timing. On a Teensy, Bounce2 is genuinely fine.
- **True-bypass latching relay** on In1/Out1. Our magnetic pickup path is a
  passive pin-8 passthrough and has no bypass state to switch.
- **Switches on ADC inputs via resistor ladders** (their route to 13 switches).
  Clever, but we have the entire left-hand pin column free — see
  [`pin_map.md`](pin_map.md).
- **The whole audio DSP stack.** Not doing synthesis on the Teensy.
