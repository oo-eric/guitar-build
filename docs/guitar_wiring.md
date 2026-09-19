# Guitar Wiring

Everything inside the guitar's control cavity. The guitar stays **entirely
passive** — no supply rail crosses into it, in either direction.

Decided 2026-09-02: the guitar carries **two output jacks**, a 13-pin GK socket
and its own 1/4". Revised 2026-09-18 to the parts actually in hand — **two A500K
pots, a Les Paul-style 3-way toggle as a Guitar / Mix / MIDI mode switch, and a
2-conductor Porter** — and to the
real GK pinout, which the earlier table in `plan.md` had wrong (see
[Pinout correction](#pinout-correction-2026-09-18)).

**Soldering? Use [`guitar_wiring_diagram.md`](guitar_wiring_diagram.md)** — the
bench sheet with the wire list and meter checks. This page is the reasoning.

## Three signal domains, and they don't mix

| Domain       | Carries                     | Controls                  | Goes to                              |
| ------------ | --------------------------- | ------------------------- | ------------------------------------ |
| **Hex**      | 6 × Ubertar, ~0.1 Vpp, hi-Z | **None. Ever.**           | GK pins 1–6                          |
| **Magnetic** | Porter, ~0.5–1 Vpp          | Mode pair A, volume, tone | GK pin 7 _or_ the guitar's 1/4" jack |
| **Control**  | DC only, no audio           | Mode pair B               | GK pin 10 → Teensy                   |

```
  6× Ubertar ═════════════════════════════════════════▶ GK 1–6   (1 = high E … 6 = low E)
                                                                  no controls, ever

  Porter hot ──[mode pair A]──▶ VOL lug 3 ── VOL wiper ──▶ 1/4" TIP ─ NC ──▶ GK 7
                                  │                          (opens on plug insert)
                             TONE lug 3
                             TONE wiper ──[33n]── GND

  GND ──[mode pair B]──▶ GK 10 (S1)    closure to ground only; low = send MIDI.
                                       Pull-up lives in the stompbox.

  Star ground ──▶ 13-pin socket shell
     (pot bodies, jack sleeve, toggle frame, bridge, cavity shield,
      Porter ground, all six Ubertar grounds)

  GK 8, 9, 11, 12, 13 — not connected.
```

## Hex: coil to pin, six times

| GK pin | String     | Ubertar hot → | Ubertar ground (white stripe) → |
| ------ | ---------- | ------------- | ------------------------------- |
| 1      | 1 (high E) | pin 1         | star ground                     |
| 2      | 2 (B)      | pin 2         | star ground                     |
| 3      | 3 (G)      | pin 3         | star ground                     |
| 4      | 4 (D)      | pin 4         | star ground                     |
| 5      | 5 (A)      | pin 5         | star ground                     |
| 6      | 6 (low E)  | pin 6         | star ground                     |

String 1 is high E, as Roland numbers them. This settles the long-open
string-direction question: stompbox side, wire **GK pin N → preamp input JN →
A(N−1)**, so `config.h` index 0 is high E. Nothing in the firmware depends on
the order — `MIN_FREQUENCY`/`MAX_FREQUENCY` are global — so this costs no code.

### Rule: nothing in the hex path

No pot, no switch, no jack contact, no series anything.

Two reasons, and the second is the one that bites:

1. **A floating hi-Z input is worse than a live one.** The preamp is
   non-inverting with the pickup on +IN at 46× gain. Open-circuit that node and
   the channel picks up hum and crosstalk from its five neighbours — a switch
   marked "off" makes that channel _noisier_, not quieter. If a passive hex kill
   is ever genuinely wanted it must short hot to ground, never open the hot.
2. **Onset detection uses absolute RMS thresholds** (onset 0.03, offset 0.018,
   idle ~0.014 — see `../AGENTS.md`). Any attenuator in the hex path lets a
   knocked knob drop the signal below onset, and the MIDI stops with nothing
   anywhere explaining why. That is a bad failure: silent, intermittent, and it
   looks like a firmware bug.

This is why the earlier "6 toggle switches — individual pickup on/off" plan was
dropped. Per-string enable is a firmware variable on a box that already has a
Teensy, a display and an encoder; done in hardware it costs six holes, twelve
joints, and six control runs sharing a cavity with the six unbuffered hi-Z lines
whose crosstalk is the top-ranked risk in `plan.md`.

## Magnetic: the Porter

| Part     | Value                   | Wiring                                                 |
| -------- | ----------------------- | ------------------------------------------------------ |
| Volume   | **A500K** (audio taper) | Lug 3 ← Porter hot. Wiper → jack tip. Lug 1 → ground   |
| Tone     | **A500K** (audio taper) | Lug 3 → volume lug 3. Wiper → 33 nF → ground. Lug 1 NC |
| Tone cap | 0.033 µF (33 nF)        | In hand, marked `.033`. Darker than the 22 nF standard |

That is "modern" wiring — tone on the volume's input. "50s" wiring moves tone
lug 3 to the volume **wiper** instead, which keeps more treble as the volume
rolls back. Either is one wire; pick by ear.

**The Porter is 2-conductor**, so there is no coil split, no series/parallel,
and nothing for a 3-way to select between. That is what freed the toggle to
become the mode switch below. One wire is hot and one is ground — if one is a braided shield, that one
is ground. Otherwise **check Porter's own diagram** rather than assuming a
Gibson or Duncan colour code.

### Volume at zero still sends MIDI

Worth stating because it will otherwise read as a bug: the volume pot is in the
magnetic path only. Roll it to zero and the guitar is silent while the hex
pickups keep driving the Teensy at full level. That is the correct behaviour and
it is genuinely useful — silent practice of MIDI parts through headphones on the
synth side.

## The two jacks

Both jacks want the magnetic pickup, and wiring them in parallel is the wrong
answer — it halves the load impedance, loses treble, and creates a genuine
ground loop the moment the two jacks land in different gear.

**Use a closed-circuit (switched) mono jack for the guitar's 1/4".** It carries
a normally-closed contact that rests against the tip terminal with no plug
inserted:

- Volume wiper → **tip terminal**
- **NC contact** → GK pin 7
- Sleeve → star ground

| State               | Pin 7  | Guitar 1/4" | Result                                           |
| ------------------- | ------ | ----------- | ------------------------------------------------ |
| Nothing in the 1/4" | live   | —           | Magnetic rides the GK cable to the stompbox jack |
| Plug in the 1/4"    | opened | live        | Short cable straight to the amp, pin 7 dead      |

Correct behaviour in both rigs with nothing to remember, and it can never drive
both at once. **Verify the exact part number against its datasheet before
ordering** — the function is standard on any "closed circuit" jack, but the
Switchcraft numbering is not something to take on trust.

### Why the second jack is worth a hole

Pin 7 is passive, so the Porter drives the entire multicore before anything
buffers it. Taking the pickup at 2–4 H into roughly 500 pF of GK cable, the
resonant peak lands near **3.5–4 kHz** — audibly darker and peakier than the
same pickup through a short cable. Assumption stated so it can be checked: that
inductance is a typical Filtertron-class figure, not a measured Porter value.

The guitar jack is the escape hatch for when analog tone matters, which is
exactly what `stompbox/README.md` flagged as worth drilling early.

## The mode switch: Guitar / Mix / MIDI

Revised 2026-09-18. The Les Paul-style 3-way is a **mode switch** — the same
three positions as Roland's GK-3 (Guitar / Mix / Synth), done passively.

| Position        | Pair A (audio) | Pair B (GK 10) | Filtertron | MIDI |
| --------------- | -------------- | -------------- | ---------- | ---- |
| **Guitar only** | closed         | open → high    | ✓          | off  |
| **Mix**         | closed         | closed → low   | ✓          | ✓    |
| **MIDI only**   | open           | closed → low   | off        | ✓    |

It works because a Les Paul toggle is two **independent** contact pairs on one
lever, each closed in the middle and at one end. One pair switches the
magnetic audio directly; the other tells the Teensy whether to send MIDI.
**Verified on the toggle in hand (2026-09-18): no continuity between the two
inner lugs in any position**, so the pairs are separate. A toggle that fails
that test has an internally shared common and cannot do this — the fallback is
a DPDT on-on-on mini toggle.

### Wiring

```
  Pair A:  Porter hot ──▶ outer lug A    inner lug A ──▶ VOL lug 3 (+ TONE lug 3)
  Pair B:  GND ─────────▶ inner lug B    outer lug B ──▶ GK 10
  Frame lug ──▶ star ground
  GK 11 — not connected
```

- **Do not jumper the two inner lugs.** Standard Les Paul wiring does, and that
  is exactly what would break this.
- **Pair A goes before the pots, not after.** Open, the pickup is disconnected
  but the output is still tied to ground through the volume pot, so the amp and
  pin 7 see a terminated line rather than a floating one that hums.
- Because the switch is in the guitar, **MIDI only silences the Filtertron on
  both outputs** — the guitar's own 1/4" and pin 7. A stompbox-side mute could
  not reach the guitar jack.
- **Find which pair is which with a meter.** Each pair opens at one end. Pair
  A is the one open at the end you want to be MIDI only. Lug layouts differ
  between Switchcraft and imports; trust the meter, not a diagram.

### Why pin 10 and not pin 9

GK does have a dedicated mode pin — pin 9 carries the GK-3's switch position as
an analog voltage (~0.5 / 1.0 / 1.5 V). Generating that needs a supply in the
guitar. A closure to ground on S1 needs none, and the firmware only needs one
bit: send MIDI or don't. The Mix/MIDI-only difference is purely analog and
already handled by pair A.

### What this replaced, and what it buys

The 2026-09-02 plan was two momentaries (S1 = MUTE, S2 = patch ±); the first
revision on 2026-09-18 was the toggle as MUTE / normal / spare. The mode switch
keeps what mattered from both:

- **MUTE survives as "Guitar only".** And the lever is the indicator — the old
  plan's hardest problem was that a firmware mute is invisible from a guitar
  that cannot have an LED without powering the cable.
- **No reboot state.** Firmware reads the lever at boot. The EEPROM-persisted
  mute the momentary design needed goes away.
- **A real MIDI-only mode**, which the MUTE/normal design could not do: the
  firmware has no way to silence a passive magnetic path.

What it costs: patch ± on the guitar (the stompbox PATCH ± footswitches still do
it), the spare third position, and cable detection — pin 10 high now means
either "Guitar only" or "nothing plugged in". Both mean _don't send MIDI_, so
the firmware doesn't need to tell them apart.

### Firmware notes

- **GK 10 low → send MIDI. High → MIDI muted.** Show the muted state on the box.
- Read **levels, not edges**, including at boot.
- Debounce with a ~30 ms hold before acting on a change.

### The stompbox side

```
        +3.3V
          │
        [10k]  pull-up
          │
  GK 10 ──┴──[10k]──┬──── Teensy pin 21
        (series)    │
                  [100n]   ── and a Schottky clamp (BAT54S) to +3.3V and GND
                    │
                   GND
```

GK 11 → Teensy 22 is no longer driven by this guitar. Keep the same input
circuit on it anyway if the board space is there — its pull-up holds it high,
and a real GK guitar's S2 would work on it.

**The RC is required.** It is what makes switch closures safe on the analog
column: a 1 ms time constant means there is no fast edge anywhere near A0–A5.
See `stompbox/pin_map.md`.

**The clamp is cheap insurance, no longer a known-failure fix.** An earlier
version of this document called it mandatory because a real GK guitar would put
+7 V on these pins. With the corrected pinout that can't happen from a normal GK
pickup or Roland-Ready guitar: they are powered from ±7 V on pins 12/13, which
this box never supplies, so they arrive unpowered. The clamp still covers ESD
on a line that leaves the box on 5 m of cable, and any self-powered
GK-compatible oddity. It costs about the price of the resistor — keep it.

## Dropped

- **The CC pot (GK 13 → Teensy 23).** Two pots in hand, both A500K, both needed
  for the Porter. An A500K is also the wrong part for it: against a 10k pull-up,
  a 500k rheostat puts ~85% of its output swing in the first tenth of its
  rotation. If a CC knob comes back, it is a 10k linear on **GK pin 8** (synth
  volume, the pin GK actually reserves for a guitar-mounted level control) —
  a new hole and a new part, not a rewire.
- **Momentary S1 / S2**, and **patch ± on the guitar** — replaced by the mode
  switch, above.

## Mis-plugging

With the corrected pinout and only pins 1–7, 10 and the shell connected,
**both directions are harmless.**

- **This guitar into real GK gear.** The synth's ±7 V on pins 12/13 lands on
  nothing. Pin 7 carries the Porter — exactly what a GK synth expects there.
  Pins 1–6 are raw passive pickups where the synth expects buffered low-Z:
  weak, harmless. In Mix and MIDI only the mode switch holds S1 "pressed", so
  expect the synth to step patches or ignore it — odd, not damaging. Pin 8 is open; what a
  given synth does with an open volume pin is untested.
- **A real GK guitar into this box.** It gets no ±7 V here, so its electronics
  are dead and it sends nothing. Its own S1 is a closure to ground — the
  same convention — so it would even work as the MIDI on/off.

## Grounding and shielding

Star ground at the 13-pin socket's **shell / ground lug** — GK carries ground on
the shell, not on a numbered pin. Everything meets there once: both pot bodies,
the jack sleeve, the toggle frame, the bridge ground, the Porter ground, the six
Ubertar grounds and the cavity shield. Shield the cavity with copper tape or
conductive paint and **bond it at that one point only**; ground it twice and
the shield is a loop.

This matters more here than on a normal guitar. Six unbuffered high-impedance
lines share the cavity with a magnetic pickup running 5–10× hotter, and
`plan.md` already ranks crosstalk as the risk most likely to break per-string
pitch detection.

Two routing rules inside the cavity:

- **Hex leads travel as their own bundle**, as short as possible, straight to
  the 13-pin socket. Nothing else in that bundle.
- **Keep them away from the magnetic and control wiring.** Coupling from the
  Porter into a hex line arrives downstream as a phantom seventh string that
  tracks whatever you played.

### Placement

A toggle is harder to hit by accident than a momentary, but a mode change
thrown mid-strum is still a dead song. The upper bout — where a Les Paul puts it — is
out of the strumming arc. Mock it up on the outline and play against it before
committing a hole. See [`body_shape.md`](body_shape.md).

## Pinout correction (2026-09-18)

`plan.md`'s original GK table was wrong on every row from 7 to 13, and had the
strings reversed. Checked against two independent pin-by-pin listings (the
flamisch.at GK/Variax connector sheet and johnp.net's Roland pinouts), which
agree with each other:

| Pin   | Real GK                      | Old table said |
| ----- | ---------------------------- | -------------- |
| 1–6   | Strings 1–6 (**1 = high E**) | 1 = low E      |
| 7     | Normal guitar pickup         | Ground         |
| 8     | Synth volume (0–5 V DC)      | Normal pickup  |
| 9     | GK mode switch (analog CV)   | +7 V           |
| 10    | S1 — active low              | −7 V           |
| 11    | S2 — active low              | S1             |
| 12    | +7 V                         | S2             |
| 13    | −7 V                         | Volume         |
| Shell | Ground                       | —              |

Nothing had been built from it — no generator, board or firmware references the
GK pins. But wired as the old table said, this guitar plugged into real GK gear
would have put a switch and a 0–10k rheostat straight across the synth's ±7 V
rails.

## Open

- **The cable test** still gates everything. If the passive guitar end fails and
  buffers have to move guitar-side, this whole document changes — that is when
  pins 12/13 come back into play and the "no supply in the cable" property is
  lost. Run it first.
- **Which end is Guitar only** — lever up or down. Decided by which pair goes
  in the audio path, so settle it before soldering, after the mock-up.
- **Modern vs 50s tone wiring** — by ear.
