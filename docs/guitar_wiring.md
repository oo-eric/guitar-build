# Guitar Wiring

Everything inside the guitar's control cavity. The guitar stays **entirely
passive** — no supply rail crosses into it, in either direction.

Decided 2026-09-02: the guitar carries **two output jacks**, a 13-pin GK socket
and its own 1/4", and the three spare GK control pins are put to work.

## Three signal domains, and they don't mix

| Domain       | Carries                     | Controls        | Goes to                              |
| ------------ | --------------------------- | --------------- | ------------------------------------ |
| **Hex**      | 6 × Ubertar, ~0.1 Vpp, hi-Z | **None. Ever.** | GK pins 1–6                          |
| **Magnetic** | Porter, ~0.5–1 Vpp          | Volume, tone    | GK pin 8 _or_ the guitar's 1/4" jack |
| **Control**  | DC only, no audio           | CC pot, S1, S2  | GK pins 13, 11, 12 → Teensy          |

```
  6× Ubertar ═══════════════════════════════════════▶ GK 1-6   (no controls)

                      ┌──[500k VOL]──┬──[500k TONE + 22n]──┐
  Porter ─────────────┤              │                     ├──▶ 1/4" TIP
                      └──────────────┴─────────────────────┴──▶ NC contact ──▶ GK 8
                                                                (opens on plug insert)

  10k lin pot ──▶ GK 13 ┐
  S1 (momentary) ▶ GK 11 ├─ passive, to ground only. Pull-ups live in the stompbox.
  S2 (momentary) ▶ GK 12 ┘

  Star ground ────────────▶ GK 7   (pot bodies, jack sleeves, bridge, cavity shield)
```

## Rule: nothing in the hex path

No pot, no switch, no jack contact, no series anything. Coil to pin, six times.

Two reasons, and the second is the one that bites:

1. **A floating hi-Z input is worse than a live one.** The preamp is
   non-inverting with the pickup on +IN at 46× gain. Open-circuit that node and
   the channel picks up hum and crosstalk from its five neighbours — a switch
   marked "off" makes that channel _noisier_, not quieter. If a passive hex kill
   is ever genuinely wanted it must short hot to ground, never open the hot.
2. **Onset detection uses absolute RMS thresholds** (onset 0.03, offset 0.018,
   idle ~0.014 — see `../CLAUDE.md`). Any attenuator in the hex path lets a
   knocked knob drop the signal below onset, and the MIDI stops with nothing
   anywhere explaining why. That is a bad failure: silent, intermittent, and it
   looks like a firmware bug.

This is why the earlier "6 toggle switches — individual pickup on/off" plan was
dropped. Per-string enable is a firmware variable on a box that already has a
Teensy, a display and an encoder; done in hardware it costs six holes, twelve
joints, and six control runs sharing a cavity with the six unbuffered hi-Z lines
whose crosstalk is the top-ranked risk in `plan.md`.

## The two jacks

Both jacks want the magnetic pickup, and wiring them in parallel is the wrong
answer — it halves the load impedance, loses treble, and creates a genuine
ground loop the moment the two jacks land in different gear.

**Use a closed-circuit (switched) mono jack for the guitar's 1/4".** It carries
a normally-closed contact that rests against the tip terminal with no plug
inserted:

- Pickup output → **tip terminal**
- **NC contact** → GK pin 8
- Sleeve → star ground

| State               | Pin 8  | Guitar 1/4" | Result                                           |
| ------------------- | ------ | ----------- | ------------------------------------------------ |
| Nothing in the 1/4" | live   | —           | Magnetic rides the GK cable to the stompbox jack |
| Plug in the 1/4"    | opened | live        | Short cable straight to the amp, pin 8 dead      |

Correct behaviour in both rigs with nothing to remember, and it can never drive
both at once. **Verify the exact part number against its datasheet before
ordering** — the function is standard on any "closed circuit" jack, but the
Switchcraft numbering is not something to take on trust.

### Why the second jack is worth a hole

Pin 8 is passive, so the Porter drives the entire multicore before anything
buffers it. Taking the pickup at 2–4 H into roughly 500 pF of GK cable, the
resonant peak lands near **3.5–4 kHz** — audibly darker and peakier than the
same pickup through a short cable. Assumption stated so it can be checked: that
inductance is a typical Filtertron-class figure, not a measured Porter value.

The guitar jack is the escape hatch for when analog tone matters, which is
exactly what `stompbox/README.md` flagged as worth drilling early.

## Magnetic controls

| Control | Part                            | Notes                                              |
| ------- | ------------------------------- | -------------------------------------------------- |
| Volume  | 500k **audio** taper            | Standard for a humbucker-sized pickup              |
| Tone    | 500k **audio** taper + 0.022 µF | Cap from wiper to ground, standard humbucker value |

Confirm Porter's own lead colour code from the diagram that shipped with the
pickup. Do **not** assume the Gibson or Seymour Duncan code — small shops vary,
and getting it wrong on a humbucker means an out-of-phase or dead coil.

Coil-splitting via a push-pull tone pot stays available at zero extra holes
**if** the Porter turns out to be 4-conductor. Count the leads before deciding.

### Volume at zero still sends MIDI

Worth stating because it will otherwise read as a bug: the volume pot is in the
magnetic path only. Roll it to zero and the guitar is silent while the hex
pickups keep driving the Teensy at full level. That is the correct behaviour and
it is genuinely useful — silent practice of MIDI parts through headphones on the
synth side.

## Control pins 11 / 12 / 13

GK reserves pin 11 (S1), pin 12 (S2) and pin 13 (Volume) for guitar-mounted
controls. In a real GK rig those work against the ±7 V the synth supplies. This
guitar is passive and no supply crosses the cable, so they are wired **to ground
only** and every pull-up lives in the stompbox.

| GK pin | Guitar side                                | Teensy side         |
| ------ | ------------------------------------------ | ------------------- |
| 11     | Momentary SPST to ground — **S1**          | Pin 21, digital in  |
| 12     | Momentary SPST to ground — **S2**          | Pin 22, digital in  |
| 13     | **10k linear** pot as a rheostat to ground | Pin 23 / A9, analog |

Rheostat wiring: tie the wiper to one outer lug — that pair is the pin-13
terminal, the other outer lug goes to ground. **Linear taper, not audio** — the
divider below already curves the response, and an audio taper would curve it
twice.

Momentary rather than latching on both switches, matching the reasoning already
settled for the footswitches in `stompbox/controls.md`: firmware owns the state,
it survives a reboot via emulated EEPROM, and a third mode later costs no
rewiring.

### The stompbox side, per line

```
        +3.3V
          │
        [10k]  pull-up
          │
  GK pin ─┴──[10k]──┬──── Teensy pin
        (series)    │
                  [100n]   ── and a Schottky clamp (BAT54S) to +3.3V and GND
                    │
                   GND
```

The pull-up sits on the **connector** side of the series resistor. Put it after,
and the two 10k resistors form a divider that squashes the pot's usable swing
from 1.65 V down to about 0.55 V.

Transfer function, 10k pull-up against a 0–10k rheostat:

```
V = 3.3 · R / (R + 10k)          →  0 V to 1.65 V
```

That is 0–2048 counts on the 12-bit ADC, or ~16 counts per step of a 7-bit MIDI
CC — plenty. The curve is compressed toward the top, so linearise in firmware
before scaling:

```c
R    = 10000.0f * v / (3.3f - v);     // volts back to ohms
cc   = (uint8_t)(127.0f * R / 10000.0f);
```

The 10k/100nF gives a 1 ms time constant. For a knob that is invisible; for the
switches it guarantees there is no fast edge anywhere near the analog column,
which is what makes pins 21–23 safe to use (below).

### This changes a safety claim in `plan.md`

Until now, plugging a **real GK guitar into this enclosure** was harmless
because pins 11/12/13 went nowhere. Connected to Teensy pins, that guitar's
controls — powered by its own ±7 V — can present up to **+7 V to a 3.3 V pin
with no 5 V tolerance**. Do not rely on the Teensy's internal protection; it
does not have the headroom and the part is unforgiving.

The clamp above is the fix, and it is cheap. Checked at +7 V on a line: 0.34 mA
through the series resistor into the clamp, 0.37 mA back through the pull-up
into a 3.3 V rail that the Teensy core itself already loads at ~100 mA. Nothing
strains. At −7 V, 0.67 mA into the lower Schottky. Also fine.

**The clamp is not optional and it is not a later refinement.** It is the only
thing standing between a borrowed GK guitar and three dead ADC pins.

## Grounding and shielding

Star ground at the 13-pin jack — pin 7 is the common. Everything meets there
once: both pot bodies, both jack sleeves, the bridge ground, and the cavity
shield. Shield the cavity with copper tape or conductive paint and **bond it at
that one point only**; ground it twice and the shield is a loop.

This matters more here than on a normal guitar. Six unbuffered high-impedance
lines share the cavity with a magnetic pickup running 5–10× hotter, and
`plan.md` already ranks crosstalk as the risk most likely to break per-string
pitch detection.

Two routing rules inside the cavity:

- **Hex leads travel as their own bundle**, as short as possible, straight to
  the 13-pin jack. Nothing else in that bundle.
- **Keep them away from the magnetic and control wiring.** Coupling from the
  Porter into a hex line arrives downstream as a phantom seventh string that
  tracks whatever you played.

## Open

- **Porter lead count** — 2-conductor or 4? Decides whether a push-pull coil
  split is on the table. Count the wires.
- **String-to-ADC direction** still undecided — `config.h` maps index 0 to A0,
  but nothing says whether that is low E or high E. Unchanged by this document,
  still needs settling before a cable is wired. See `plan.md`.
- **The cable test** still gates everything. If the passive guitar end fails and
  buffers have to move guitar-side, this whole document changes — that is when
  pins 9/10 come back into play and the "no supply in the cable" property is
  lost. Run it first.
- **What S1, S2 and the CC pot actually do** is firmware, deliberately not
  decided here. Candidates: MIDI mute, patch ±, mode toggle; CC assignable from
  the display menu.
