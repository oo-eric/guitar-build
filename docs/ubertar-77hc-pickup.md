# Ubertar 77HC Pickup Reference

Source: <https://ubertar.com/hexaphonic/faq.html>, plus direct correspondence with Paul Rubenstein (<paul@ubertar.com>, 2026-06-06).

## DC Resistance

- **New/improved pickup (what we have):** ~2.5K ohms, and _hotter_ than either older model despite the lower DCR. Paul: "DCR doesn't tell you much on its own."
- **Old standard HC coils:** ~7.5K ohms
- **Old "plus" coils:** ~3K ohms (more powerful than standard)

## Wiring

- **Single-string model (what we have):** 2 wires
  - White stripe = ground = the _starting end of the coil_ (inside)
  - No stripe = hot
  - Reversing hot/cold just flips phase — harmless for pitch detection (confirmed by Paul)
- **Hex pickup wire colors (high to low):** white, black, red, green, yellow, blue
- One shared ground wire

## Signal Characteristics

- **Output level:** ~0.1V peak-to-peak (Paul's estimate — he hasn't measured these, so treat as a ballpark for sizing the preamp)
- Output impedance: not measured by Paul; expect high-Z, typical of passive magnetic pickups
- **String-to-string consistency:** intended to be "very close" across a matched set. Thinner strings have somewhat less gain (less mass), but no more so than any other e/m pickup — so large per-string gain differences point at _pickup height/placement_, not the pickups themselves.
- Crosstalk between strings is measured but not numerically specified in FAQ

## Pickup Placement (Paul's recommendation)

- Position the pickups **as close as possible to the strings**.
- Rule of thumb: a vibrating string should _just barely clear_ the pickup when fretted at the highest fret.
- Raising pickup height is a mechanical lever for both more signal and more even string-to-string output — try this before chasing level differences in the gain stage.

## Mic vs. Instrument Level (for audio-interface use)

- Paul's advice assumes feeding a multichannel **audio interface / sound card** with instrument-level inputs: enough instrument-level inputs → no impedance matching needed; mic inputs work but need more gain and tone may suffer. He suggests a **reverse DI** to convert instrument level → mic level if only mic inputs are available.
- **Not directly applicable to this build** — we feed a Teensy ADC, not an audio interface. The MCP6002 buffer/preamp already does the impedance + gain job a reverse DI would. Noted for completeness.

## Notes for this project

- Passive magnetic pickup → high impedance output → needs buffer circuit before ADC
- Signal level from a single-string pickup will be low — may need gain stage beyond unity buffer
- The new pickup is an upgraded model Paul made for us — "more powerful, better sound, more durable" than the original HC series (he's phased out the bare HCs, which were fragile)
