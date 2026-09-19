# MIDI Guitar Build

A DIY guitar with per-string pickups and a Teensy 4.0 for real-time pitch-to-MIDI conversion using MPE.

## Project Structure

- `docs/` — build/design references and datasheets
  - `body_shape.md` — body outline design (Jazzmaster × Iceman hybrid)
  - `buffer_circuit.md` — **circuit of record.** MCP6002 @ 3.3V preamp schematic, values, BOM, bring-up. Phase-1 TL072 build is a superseded appendix at the bottom.
  - `guitar_build.md` — physical guitar build specs and decisions
  - `guitar_wiring.md` — **guitar cavity wiring of record.** Signal domains, the two-jack switching, knob/switch values, grounding. Read before wiring the body
  - `guitar_wiring_diagram.md` — **bench sheet**: diagram, point-to-point wire list, pre-solder meter checks, post-solder continuity tests
  - `pickup_selection.md` — standard magnetic pickup selection (Porter Pickups, Filtertron-sized)
  - `plan.md` — phased build plan, parts list, signal chain, technical notes, and the **13-pin interface** pin table
  - `stompbox/` — the enclosure that holds everything except the pickups
    - `README.md` — I/O, panel layout, enclosure spec, open items
    - `power.md` — 9V pedalboard supply → 5V → VIN. **Read before wiring power**
    - `controls.md` — footswitches, LEDs, display budget
    - `pin_map.md` — **Teensy pin assignments. Check before assigning anything new**
  - `teensy-4.0.md` — Teensy 4.0 pinout / reference
  - `ubertar-77hc-pickup.md` — Ubertar 77HC pickup reference
  - `wip.md` — **historical.** Phase-1 breadboard wiring for the superseded TL072 + 9V circuit, and it contains a known gain-resistor error. Do not build from it; `buffer_circuit.md` is the circuit of record.
  - `wood_comparison.md` — body / neck / fretboard tonewood comparison
- `hardware/` — KiCad schematic and board (both generated — do not hand-edit)
  - `midi-guitar-preamp.kicad_sch` — 6-channel MCP6002 preamp, A3 sheet, 48 components
  - `midi-guitar-preamp.kicad_pcb` — 82 × 156 mm, 2-layer, all through-hole
  - `pcb-top.pdf` / `pcb-bottom.pdf` — rendered layer views
- `scripts/gen_kicad_schematic.py` — generates the schematic from the values in its CONFIG block. Symbols are embedded, so the file opens without library setup. Edit values here and re-run.
- `scripts/check_kicad_netlist.py` — re-parses the generated schematic, rebuilds the netlist, and asserts the circuit in `buffer_circuit.md`. Run after any regeneration.
- `scripts/gen_kicad_pcb.py` — generates the board. Placement is hand-designed for analog layout; connectivity comes from KiCad's netlist exporter, so board and schematic cannot drift apart. Fills the copper zones as part of generating.
- `scripts/kicad_sexp.py` — shared s-expression reader/writer for the two generators.

**Regenerate order:** schematic → `check_kicad_netlist.py` → PCB. The board reads the schematic, so always regenerate the schematic first.

**Adding a part is a two-file job.** Adding it to the schematic generator is not enough — the PCB generator's placement is hand-designed, so a new part needs an explicit placement entry there too. It will otherwise be dropped from the board _silently_: the run still succeeds, and the only symptom is the footprint count not matching the schematic's component count. Always compare those two numbers, then verify with:

```
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc \
  --schematic-parity --severity-error hardware/midi-guitar-preamp.kicad_pcb
```

Expect 5 pre-existing silkscreen-overlap warnings (R10, R13, R16, R20/C13) — cosmetic, not regressions.

- `firmware/adc_test/` — Phase 1 single-string test sketch (Audio library + USB Audio, YIN-based)
- `firmware/experiments/` — sketches that are **not** part of the MIDI signal chain and are not headed for the pedal. See its `README.md` for why each is parked and what was learned.
  - `graphicstest/` — ILI9341 waveform display (TFT_eSPI + sprites). Bench calibration tool. Parked for two reasons: a 240×200 sprite push costs ~32 ms and stalls six pitch-detection slots, and SPI SCLK (pin 13) noise couples into A0 (pin 14). Both were measured on a breadboard and are worth retesting on the PCB, which has ground pour.
- `firmware/guitar_midi/` — Phase 2 modular firmware (6-string, MPE MIDI)
  - `adc_sampler.h/.cpp` — timer-driven 20kHz ADC sampling, 6 channels with independent ring buffers
  - `config.h` — all tunable constants (thresholds, sample rate, MIDI settings, per-string config)
  - `guitar_midi.ino` — 6-string orchestrator with staggered pitch detection
  - `midi_output.h/.cpp` — MPE MIDI output with pitch bend tracking (per-channel)
  - `onset_detector.h/.cpp` — note on/off state machine (RMS-based, per-string)
  - `pitch_detector.h/.cpp` — YIN pitch detection algorithm with hysteresis

## Tech Stack

- **Hardware:** Teensy 4.0 (ARM Cortex-M7, 600MHz), Ubertar 77HC single-string pickups, MCP6002 op-amp buffer circuits (runs on 3.3V from Teensy — replaced the TL072 + 9V battery)
- **Firmware:** C++ via Arduino IDE + Teensyduino
- **Libraries:** Teensy ADC library (`ADC.h`), built-in USB MIDI
- **ADC Sampling:** Timer-driven at 20kHz via IntervalTimer, reads all string pins per tick
- **Pitch Detection:** YIN algorithm (cumulative mean normalized difference) with hysteresis
- **MIDI Format:** MPE — each string on its own MIDI channel (channels 2-7)

## Key Constraints

- Teensy 4.0 uses micro-USB (not USB-C)
- Do not power Teensy via VIN and USB simultaneously without cutting the VIN-VUSB trace
- Arduino IDE USB Type must be set to "Serial + MIDI" for Phase 2 firmware
- `usbMIDI` is only available in `.ino` files or via `#include <usb_midi.h>` in `.cpp` files
- MCP6002 runs on 3.3V from the Teensy — no battery needed. (Replaced the TL072, which needed 7V+; weak 9V batteries caused distorted output.) Switching TL072@9V → MCP6002@3.3V roughly halves output swing, so onset/offset thresholds had to be rescaled (or gain raised)
- **Preamp is non-inverting: pickup hot goes to +IN, never -IN.** The gain resistor connects from -IN to the 1.65V bias rail (NOT to the output chain — that shorts), and gain is `1 + Rf/Rg`. The Phase-1 breadboard fed the pickup into -IN, which silently makes the circuit inverting; gain then stops matching the formula and starts tracking pickup impedance. See the reconciliation section of `docs/buffer_circuit.md`.
- The bias rail needs its bulk bypass cap. `Rg` is referenced to it, so a bare 10k/10k divider (5k source impedance) sits in series with the gain network and eats gain.
- The +3V3 rail carries its own bulk cap (`C18`, 10µF) on top of the three per-chip 100nF. The 100nF caps handle fast transients; they do not cover low-frequency sag, which the MCP6002 datasheet asks for separately. `check_kicad_netlist.py` asserts exactly one bulk electrolytic on +3V3 with its return leg on GND.
- Nothing band-limits the signal except `Cf` across the feedback resistor. The sampler runs at 20kHz, so that filter is what keeps >10kHz content from aliasing into the pitch detector.
- **Teensy 4.0's VIN accepts 3.6–5.5V only. The 9V pedalboard supply must be regulated to 5V first — 9V on VIN destroys the board.** See `docs/stompbox/power.md`.
- **Check `docs/stompbox/pin_map.md` before assigning any Teensy pin.** Pin 1 is both Serial1 TX and SPI1 MISO and is reserved; pins 13 and 20 flank the analog block and must not carry switching signals.
- **The Teensy header on the PCB is not in A0–A5 order.** Pins are GND, +3V3, A1, A0, A3, A2, A5, A4 — chosen so the six ADC runs fan into the connector without crossing. Wire it from the silkscreen labels, not from memory.

## Physical Architecture

**The electronics do not live in the guitar.** The preamp board is 82 × 156 mm and never fit a control cavity. Decided 2026-08-09:

- **Guitar** — pickups, a 13-pin socket, **its own 1/4" jack**, two knobs (A500K volume/tone on the Porter) and one Les Paul-style 3-way used as a **Guitar / Mix / MIDI mode switch** (one contact pair switches the Porter audio, the other grounds GK pin 10 when MIDI should play). Still entirely passive: no power, no active parts, and no supply rail crosses the cable in either direction. See `docs/guitar_wiring.md`.
- **Stomp box** — preamp board + Teensy + 1/4" jack + USB-C. Target enclosure: Hammond 1590DD.
- **Link** — a **standard Roland GK 13-pin cable and pin assignment**, not a custom pinout. Conforming costs nothing and makes cables purchasable. Hex on pins 1–6 (**pin 1 = string 1 = high E**), magnetic pickup on 7 (switched by the guitar's own 1/4" jack), synth volume on 8 and mode CV on 9 (both unconnected), **S1 on pin 10 carries the mode switch's MIDI on/off** as a closure to ground (S2 on 11 unconnected guitar-side) — every pull-up stays stomp-box side — ±7V on 12/13 (unused), ground on the shell. **Verified 2026-09-18 against two published GK pinouts; the earlier table in `plan.md` was wrong on strings and on every pin from 7 to 13.**
- Mis-plugging: **harmless both ways.** This box never supplies ±7V, so a real GK guitar plugged into it is unpowered. See `plan.md` → "13-Pin Interface".

One item still open there: whether the passive guitar end survives sending raw ~0.1Vpp down a long cable into 1MΩ. Risk order is crosstalk between strings (worst — it attacks per-string pitch detection directly), then hum, then HF loss.

Two rules added 2026-09-02 with the guitar's knobs and switches:

- **No pot or switch may ever sit in the hex path.** Onset detection uses absolute RMS thresholds, so an attenuator there stops the MIDI silently, and opening a hex hot leaves a floating input on a 46× stage — noisier off than on.
- **GK pins 10/11 → Teensy 21/22 (22 spare) each get 10k series + 10k pull-up + 100nF + a BAT54S clamp.** The RC is required: it keeps switch edges off the analog column. The clamp is cheap insurance, not a fix for a known failure. Teensy pin 23/A9 is free since the CC pot was dropped (2026-09-18).

**Do not order boards before running the cable test** — if buffers must move guitar-side, this board may change.

## Current Phase

Phase 2 — 6-string expansion. Modular firmware written in `firmware/guitar_midi/`, currently ramping up on A0/A1 (`NUM_STRINGS = 2`). MCP6002 swap done — single string is end-to-end working (pickup → MCP6002 buffer → ADC → onset → pitch → MPE MIDI), no 9V battery in the chain. Onset/offset detection working with rescaled MCP6002 thresholds. Expanding to all 6 strings; pitch detection and per-string gain/threshold calibration in progress.

Hardware in parallel: neck and body arrived 2026-08-08, Porter pickup acquired, PCB design complete and DRC-clean. Board is ready to fab — gated only on the cable test above.

### As of 2026-08-09

- Added `C18` (10µF) bulk bypass on +3V3; schematic, checker, PCB, and `buffer_circuit.md` all updated. Board is now 48 footprints, DRC clean, zero schematic-parity issues.
- Evaluated Flux.ai as a PCB tool and **rejected it for this design** — its KiCad import dropped all through-hole footprints and every routed trace, and it reported two confident "critical" faults (reversed op-amp supply pins, reversed op-amp inputs) that do not exist in the local files. Only its bulk-cap finding was real. Reads on that MCP server are free; only `create_thread`/`send_message` spend credits.
- Fab path: export Gerbers + Excellon with `kicad-cli`, zip flat, upload to JLCPCB. All through-hole means no BOM, no CPL, no assembly fees. Rough cost ~$25–50 for 5 boards plus $10–25 shipping, ~$10–20 in parts, 1–2 weeks express. The 13-pin interface hardware (~$80–130) costs more than the board.
