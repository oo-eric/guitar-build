# Ubertar 77HC Pickup Reference

Source: https://ubertar.com/hexaphonic/faq.html

## DC Resistance

- **Standard coils:** ~7.5K ohms
- **Plus coils:** ~3K ohms (but more powerful than standard)

## Wiring

- **Single-string model (what we have):** 2 wires
  - White stripe = ground
  - No stripe = hot
- **Hex pickup wire colors (high to low):** white, black, red, green, yellow, blue
- One shared ground wire

## Signal Characteristics

- Output voltage/signal level: not documented publicly
- Output impedance: not documented (expect high-Z, typical of passive magnetic pickups)
- Crosstalk between strings is measured but not numerically specified in FAQ

## What's NOT in the docs

- No output voltage specs
- No recommended buffer/preamp circuits
- No frequency response data
- Contact paul@ubertar.com for detailed electrical specs

## Notes for this project

- Passive magnetic pickup → high impedance output → needs buffer circuit before ADC
- 7.5K DC resistance (standard) is typical for a single-coil pickup
- Signal level from a single-string pickup will be low — may need gain stage beyond unity buffer
- The 77HC is an upgraded model Paul made for us — "more powerful, better sound, more durable" than the original HC series
