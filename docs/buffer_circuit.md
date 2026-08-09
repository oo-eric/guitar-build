# Preamp Circuit — MCP6002 @ 3.3V (Phase 2, canonical)

One non-inverting AC preamp per string. Six channels, three dual op-amps, **powered entirely from the Teensy's 3.3V rail — no battery, no external supply.**

This document is the **source of truth** for the circuit. The Phase-1 TL072 + 9V build is kept as a historical appendix at the bottom; do not build from it.

---

## Design rules

1. **No preamp power supply.** MCP6002 runs 1.8–6V rail-to-rail. It takes 3.3V and GND from the Teensy. Total current for all six amps is ~0.6mA (100µA/amp typ.), against a 3.3V regulator good for ~250mA. Power is a non-issue; this is the whole reason for the TL072 → MCP6002 swap.
2. **Non-inverting topology.** A passive magnetic pickup is a high-impedance source and must see a high-impedance load. Input impedance here is set by the 1M bias resistor, not by the gain network.
3. **Everything sits at 1.65V.** With the rails at 0/3.3V, mid-supply is 1.65V — which is also exactly where the Teensy ADC wants its quiescent point. Output is therefore DC-coupled straight to the ADC; no level-shifting network.
4. **Bandwidth is limited on purpose.** The firmware samples at 20kHz, so anything above 10kHz aliases back into the pitch detector. The feedback cap is the anti-alias filter.

---

## Schematic — one channel

```
                                   3.3V (from Teensy)
                                     |
                                   pin 8 (VDD)
                                     |
                                 +---+---+
   Pickup hot                    |       |
   (no stripe) --+--[0.1uF]--+---|+      |
                 |   Cin     |   |       |
                 |           |   |  MCP  |
                 |          [1M] |  6002 |----+----> Teensy A_n
                 |          Rbias|       |    |     (DC-coupled, sits at 1.65V)
                 |           |   |       |    |
                 |           |   +---+---+    |
                 |           |       |        |
                 |         VBIAS   pin 4      |
                 |        (1.65V)  (VSS)      |
                 |                   |        |
   Pickup gnd    |                  GND       |
   (white stripe)+------------------GND       |
                                              |
   Feedback network (OUT back to -IN):        |
                                              |
        -IN ---+-----------[100K Rf]----------+
               |                              |
               |-----------[330pF Cf]---------+
               |
             [Rg]        <-- sets gain, per string
               |
             VBIAS (1.65V rail)


   Bias rail (ONE divider, shared by all 6 channels):

        3.3V
          |
        [10K]
          |
          +-----+------+-------> VBIAS rail (1.65V)
          |     |      |
        [10K] [100uF] [0.1uF]
          |     |      |
         GND   GND    GND


   +3V3 rail bypass:

        3.3V from Teensy ---+------+------+------+---> to U1, U2, U3 pin 8
                            |      |      |      |
                          [10uF] [0.1u] [0.1u] [0.1u]
                           C18     one per chip, at the pin
                            |      |      |      |
                           GND    GND    GND    GND
```

### Gain

```
Gain = 1 + (Rf / Rg)          Rf = 100K
```

| Rg   | Gain  |
| ---- | ----- |
| 4.7K | ~22x  |
| 3.3K | ~31x  |
| 2.2K | ~46x  |
| 1.5K | ~68x  |
| 1.0K | ~101x |

Populate all six at **2.2K (46x)** and trim per string after measuring. Per `pickup_selection.md` / the Ubertar notes, large string-to-string differences are a _pickup height_ problem first — raise the pickups before re-picking resistors.

**Headroom ceiling.** The output can only swing inside 0–3.3V, so usable gain is bounded:

```
max gain ≈ 3.0V / Vpp_pickup
```

Paul's ballpark for the 77HC is ~0.1Vpp, which would cap gain around **30x** — below the 46x starting value. That estimate is unmeasured and single-string output is likely well under it, which is why 46x has been working. If a string shows flat-topped waveforms on the ADC, that is clipping, and Rg goes **up**, not down.

### Component rationale

| Part         | Value                                 | Why this value                                                                                                                                                                                                 |
| ------------ | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Cin`        | 0.1µF **film/C0G — not electrolytic** | With 1M to ground, an electrolytic's leakage current develops a real DC offset at the input. Non-polar part, no polarity to get wrong. High-pass corner = 1/(2π·1M·0.1µF) ≈ **1.6Hz**, far below low E (82Hz). |
| `Rbias`      | 1M                                    | Sets input impedance. Loading a passive pickup with a few kΩ kills output and damps the resonant peak; 1M does neither.                                                                                        |
| `Rf`         | 100K                                  | Feedback. Matches the gain table in `plan.md`.                                                                                                                                                                 |
| `Cf`         | 330pF                                 | Anti-alias. Corner = 1/(2π·100K·330pF) ≈ **4.8kHz**, comfortably under the 10kHz Nyquist limit of the 20kHz sampler. Also kills op-amp noise above the audio band.                                             |
| `Rg`         | 1K–4.7K                               | Gain, per string. See table.                                                                                                                                                                                   |
| Bias divider | 2× 10K                                | Mid-supply reference. No DC current is drawn from it, so the exact value barely matters.                                                                                                                       |
| Bias bypass  | 100µF + 0.1µF                         | **This one matters.** `Rg` is referenced to VBIAS, so VBIAS has to be a real AC ground or it eats the gain. A bare 10K/10K divider is 5kΩ — comparable to `Rg` itself. 100µF brings it to ~20Ω at 80Hz.        |
| Decoupling   | 0.1µF × 3                             | One per MCP6002, right at pins 8/4.                                                                                                                                                                            |
| Rail bulk    | 10µF (`C18`)                          | The three 0.1µF caps handle fast transients but not low-frequency sag on +3V3. The MCP6002 datasheet asks for bulk capacitance on the rail as well; placed at the Teensy end, where the supply enters.         |

**Crosstalk note.** All six channels return their gain current to the same VBIAS rail, so that rail's residual impedance is a shared path between strings. The 100µF makes it small; if measured crosstalk is still a problem, the fix is to buffer VBIAS with a dedicated op-amp follower rather than to add more bulk capacitance.

---

## KiCad files

`hardware/midi-guitar-preamp.kicad_sch` (+ `.kicad_pro`, `.pdf`). Symbols are embedded in the schematic, so it opens without any library setup.

**The schematic is generated. Do not hand-edit it** — change values in the CONFIG block of `scripts/gen_kicad_schematic.py` and re-run. UUIDs are derived deterministically, so regenerating produces a clean git diff instead of churn.

```sh
python3 scripts/gen_kicad_schematic.py     # regenerate
python3 scripts/check_kicad_netlist.py     # verify against this document
export PATH="/Applications/KiCad/KiCad.app/Contents/MacOS:$PATH"
kicad-cli sch erc --severity-all --format report -o /tmp/erc.rpt hardware/midi-guitar-preamp.kicad_sch
kicad-cli sch export pdf -o hardware/midi-guitar-preamp.pdf hardware/midi-guitar-preamp.kicad_sch
```

`check_kicad_netlist.py` re-parses the finished file, rebuilds the netlist from the wires and labels, and asserts this circuit: Rf and Cf bridge OUT↔−IN, Rg reaches VBIAS, `Cin` lands on **+IN** and traces back to a pickup connector, `Rbias` is 1M, the rails are correct, and no two named nets are shorted. Run it after every regeneration. ERC currently reports **0 violations** (KiCad 10.0.5).

The project file sets `lib_symbol_mismatch` and `lib_symbol_issues` to _ignore_. Those fire only because the embedded symbols differ from KiCad's stock symbols of the same name, which is the intended arrangement — without the override they bury real findings under ~78 warnings.

## PCB layout

`hardware/midi-guitar-preamp.kicad_pcb` — **82 × 156 mm, 2 layers, all through-hole.**

Generated the same way as the schematic:

```sh
python3 scripts/gen_kicad_pcb.py     # regenerates and fills the zones
kicad-cli pcb drc --severity-all --schematic-parity \
  --format report -o /tmp/drc.rpt hardware/midi-guitar-preamp.kicad_pcb
```

Connectivity is taken from KiCad's own netlist exporter rather than re-derived, so the board cannot disagree with the schematic about what connects to what. Current state: **0 unconnected items, 0 DRC errors, 0 schematic-parity issues.** Five silkscreen-overlap warnings remain, all a resistor's reference label touching its own outline — cosmetic only.

### Placement

Each MCP6002 is rotated 90°, so a channel's three signal pins (OUT, −IN, +IN) sit side by side instead of stacked 2.54mm apart. `−IN` is the middle pin, so the feedback parts hang straight off it, channel A fans down and channel B fans up, and nothing has to cross. The result keeps `Rf`/`Cf` right against the op-amp and the high-impedance `+IN` trace short — which is the whole reason to hand-place an analog board rather than let a router scatter it.

| Region        | Contents                                                                |
| ------------- | ----------------------------------------------------------------------- |
| Right edge    | Six 2-pin pickup headers, one per channel, beside its own input cap     |
| Centre column | Three DIP-8s at 46mm pitch, each with its decoupling cap at the VDD pin |
| Top           | Bias divider and the VBIAS bulk/ceramic bypass                          |
| Bottom left   | 8-pin Teensy header                                                     |

### Layer strategy

Every part is through-hole, so **each pad exists on both layers and doubles as a layer transition** — the whole board needs only three vias (one per channel-B output).

| Layer | Carries                                                   |
| ----- | --------------------------------------------------------- |
| F.Cu  | Short per-channel analog nets, and the +3V3 spine         |
| B.Cu  | VBIAS spine (x = 61mm) and the six ADC runs to the header |
| both  | GND pour                                                  |

The two crossing-prone nets — the +3V3 spine and the ADC fan — are deliberately on opposite layers so they pass over each other instead of colliding.

### Teensy header pin order is NOT A0–A5

Pins run **GND, +3V3, A1, A0, A3, A2, A5, A4**, matching the physical top-to-bottom order of the op-amp outputs. Fanning six scattered sources into a 2.54mm pin column has no crossing-free solution in A0–A5 order; this ordering makes it planar with no vias. The connector is a flying lead to the Teensy, so the order costs nothing — but **wire it from the silkscreen, not from memory.** Each pin is labelled on B.SilkS.

### Known limitations

- **The board is long.** 156mm may not drop into a control cavity; it is sized for a rear-routed electronics cavity or a body-mounted plate. Moving to SMD passives would roughly halve it. The height is set by three chip blocks at 46mm pitch.
- **No mounting holes.** Add them to suit the cavity before fabricating.
- **Not fabrication-verified.** DRC passes against KiCad's default rules; those are not any particular fab's rules. Load your fab's design rules and re-run before ordering. Gerbers are one command away (`kicad-cli pcb export gerbers`), but have not been generated or checked.
- `lib_footprint_mismatch` is set to _ignore_ in the project file — the generator restyles reference-designator text, so every footprint differs cosmetically from its library copy.

## Reconciliation — what changed and why

The previous version of this doc disagreed with `plan.md`, and internally with itself. Resolved as follows, **Phase 2 taken as source of truth**.

### 1. Topology: the signal now enters +IN (was −IN)

This is the substantive fix.

Every _number_ in both documents describes a non-inverting amplifier:

- This doc's stated formula: `Gain = 1 + (100K / R_in)` — the non-inverting formula.
- `plan.md`'s parts list: "2.2K → ~46x with 100K feedback" (`1 + 100/2.2 = 46.5` ✓) and "1K → ~101x" (`1 + 100/1 = 101` ✓).
- Both docs place the gain resistor from −IN to the bias point — the non-inverting arrangement.

But the _wiring_ tables in this doc and in `wip.md` ran the pickup through the input cap into **−IN**, which builds an inverting amplifier. In that circuit the gain resistor to the bias rail carries no signal current and sets no gain at all; gain instead becomes `Rf / Z_pickup`. That predicts the two symptoms already recorded in these notes:

- **Gain far off the calculated value.** 200K feedback against the 77HC's ~2.5K DCR lands near 80x, which is why "unity" and "11x" configurations behaved nothing like their labels and why parallel 10Ks were needed to chase a number.
- **"High strings need significantly more gain than low strings."** Pickup impedance is inductive, so it rises with frequency; gain `Rf/Z` therefore _falls_ as pitch rises. A frequency-dependent gain slope is exactly what that note describes.

It also loaded the pickup down hard, since in the inverting arrangement the pickup drives the summing node directly.

Moving the input to +IN makes gain equal its formula, flat across the band, and independent of the pickup — and restores a 1M input impedance.

> **Unverified on the bench.** This is an analysis of the documented wiring, not a measurement. Before committing to fab, build one channel in the new topology and confirm the measured gain matches `1 + Rf/Rg`.

### 2. Output coupling cap and second divider: deleted

The Phase-1 output cap + 10K/10K re-bias divider existed because the TL072 on 9V idled at ~4.5V and had to be shifted down into the Teensy's 3.3V window. At 3.3V the op-amp already idles at 1.65V — DC gain is unity because no DC current flows through `Rg` or `Rf` — so the output is already sitting exactly where the ADC wants it. The network is now redundant.

Removed per channel: 1× 10µF, 2× 10K. Across six channels: **6 caps and 12 resistors deleted.** This is a direct dividend of dropping the battery.

### 3. Feedback: 100K single (was "200K, as two 100K in series")

`wip.md` records 200K, reached by stacking resistors to chase gain in the mis-wired topology. With gain now set correctly by `Rg`, a single 100K restores agreement with `plan.md`'s gain table and gives `Cf` a sane value.

### 4. Gain resistor: single per-string value (was 3× 10K in parallel)

Three 10K in parallel is 3.33K — an arbitrary value arrived at empirically. Replaced with a single resistor from the standard table.

### 5. Additions not present in either doc

- **`Cf` (330pF) anti-alias filter.** Neither document had any band-limiting whatsoever ahead of a 20kHz sampler. Content above 10kHz was folding down into the audio band and into the YIN detector. This was a real gap, not a refinement.
- **`Cin` respecified as film.** 10µF electrolytic into a 1M bias node leaks enough to produce a DC offset.
- **100µF bias-rail bypass.** Required for `Rg` to see an AC ground; without it the divider's 5kΩ impedance is in series with the gain network.

### 6. Unchanged

MCP6002 @ 3.3V from the Teensy, no battery. Three DIP-8 chips, two channels each. Strings mapped to A0–A5. Pickup ground = white-stripe wire. Phase-1 breadboard column maps are superseded and live in the appendix.

---

## Bill of materials — all 6 channels

| Part               | Qty | Where                                   |
| ------------------ | --- | --------------------------------------- |
| MCP6002 (DIP-8)    | 3   | 2 channels each                         |
| 0.1µF film/C0G     | 6   | `Cin`, one per channel                  |
| 1M resistor        | 6   | `Rbias`, one per channel                |
| 100K resistor      | 6   | `Rf`, one per channel                   |
| 330pF C0G          | 6   | `Cf`, one per channel                   |
| 2.2K resistor      | 6   | `Rg`, one per channel (trim per string) |
| 10K resistor       | 2   | Bias divider (shared)                   |
| 100µF electrolytic | 1   | `C13`, bias rail bulk bypass            |
| 10µF electrolytic  | 1   | `C18`, +3V3 rail bulk bypass            |
| 0.1µF ceramic      | 4   | 3× chip decoupling + 1× bias rail       |
| 2-pin connector    | 6   | Pickup in (hot / ground)                |
| 8-pin header       | 1   | To Teensy: 3.3V, GND, A0–A5             |

Resistor count drops from 44 (old doc) to 26. Capacitor count is flat but the parts are smaller and cheaper.

---

## Pin reference — MCP6002 (DIP-8)

```
        +---v---+
 OUTA   | 1   8 |  VDD  (3.3V)
 -INA   | 2   7 |  OUTB
 +INA   | 3   6 |  -INB
 VSS    | 4   5 |  +INB
        +-------+
        (GND)
```

Pinout is identical to the TL072, so the chips are drop-in on the existing breadboard footprint.

## String → channel map

| String | Chip | Channel | Op-amp pins (OUT/−IN/+IN) | ADC |
| ------ | ---- | ------- | ------------------------- | --- |
| 1 (E2) | U1   | A       | 1 / 2 / 3                 | A0  |
| 2 (A2) | U1   | B       | 7 / 6 / 5                 | A1  |
| 3 (D3) | U2   | A       | 1 / 2 / 3                 | A2  |
| 4 (G3) | U2   | B       | 7 / 6 / 5                 | A3  |
| 5 (B3) | U3   | A       | 1 / 2 / 3                 | A4  |
| 6 (E4) | U3   | B       | 7 / 6 / 5                 | A5  |

---

## Bring-up and troubleshooting

Measure with no string vibrating unless stated.

| Symptom                                      | Check                                                                                                                                                                                     |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Quiescent voltage at A_n is not 1.65V**    | Probe VBIAS first. If VBIAS is wrong, it's the 10K/10K divider. If VBIAS is right but the output is at a rail, the op-amp is railed — check `Rf` continuity and that `Rbias` reaches +IN. |
| **ADC pinned at 0 or 4095**                  | Output railed. Usually a missing feedback path or +IN floating.                                                                                                                           |
| **Sits at 1.65V but no signal**              | Pickup wiring or `Cin`. Confirm continuity from the connector through `Cin` to +IN.                                                                                                       |
| **Measured gain ≠ 1 + Rf/Rg**                | The classic cause is the input landing on −IN instead of +IN. Verify VBIAS is stiff — a missing 100µF makes gain read low.                                                                |
| **Flat-topped waveform**                     | Clipping. Increase `Rg`.                                                                                                                                                                  |
| **Weak, dull, or thin output**               | Something is loading the pickup. `Rbias` should be 1M and the pickup should see nothing else.                                                                                             |
| **Strings audible in each other's channels** | VBIAS crosstalk. Check the 100µF; consider buffering the rail.                                                                                                                            |
| **Hash/noise correlated with the display**   | Known issue — ILI9341 SPI SCLK couples into the ADC. See `CLAUDE.md`; display is parked.                                                                                                  |

---

# Appendix — Phase 1 (TL072 + 9V battery) — SUPERSEDED

Historical record of the first working single-string build. **Do not build from this.** It requires a 9V battery, biases at 4.5V, needs an output level-shifter, and its gain notes reflect the mis-wired topology described above.

### Phase 1 schematic

```
   77HC Pickup ──> [10uF] ──> TL072 pin 2 (-IN)
                                    |
                             [100K feedback] from pin 1
                                    |
                             pin 1 (OUT) ──> [10uF] ──> 10K/10K divider ──> Teensy A0
```

- V+ = pin 8 = +9V battery; V− = pin 4 = GND. 0.1µF decoupling at the chip, 10µF bulk at the rail.
- Input bias: 10K/10K from Teensy 3.3V → 1.65V → pin 3 (+IN).
- Output bias: 10K/10K from Teensy 3.3V, output cap into the midpoint → A0.
- All grounds common: battery −, TL072 pin 4, Teensy GND, pickup white-stripe.

### Phase 1 breadboard placement

830-point board. Teensy at col 3, TL072 at col 55, both straddling the center channel. Signal components on the bottom side.

| Connection          | From                    | To              | Component            |
| ------------------- | ----------------------- | --------------- | -------------------- |
| 9V red / black      | battery                 | + rail / − rail | —                    |
| TL072 V+ / GND      | col 55 top / col 58 bot | + rail / − rail | jumper               |
| Decoupling          | + rail                  | − rail          | 0.1µF, near chip     |
| Input bias divider  | Teensy 3.3V             | col 35 → − rail | 2× 10K               |
| Bias to +IN         | col 35                  | col 57          | jumper               |
| Feedback            | col 55                  | col 56          | 100K (later 2× 100K) |
| Input cap           | col 45                  | col 56          | 10µF, + leg at chip  |
| Output cap          | col 55                  | col 41          | 10µF, + leg at chip  |
| Output bias divider | Teensy 3.3V             | col 41 → − rail | 2× 10K               |
| ADC                 | col 41                  | Teensy A0       | jumper               |
| Pickup hot / gnd    | pickup                  | col 45 / − rail | —                    |

Later modifications recorded in `wip.md`: feedback raised to 200K (two 100K in series, junction at col 53) and multiple 10K resistors placed in parallel from col 56 to the input bias point at col 21. Both were attempts to raise gain in the inverting topology; neither is carried forward.

### Why it was replaced

TL072 needs 7V+. The 9V battery drained quickly, and a sagging battery produced distorted output — the failure that prompted the move to MCP6002 at 3.3V.
