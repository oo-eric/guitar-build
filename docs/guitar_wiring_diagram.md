# Guitar Wiring Diagram

Bench sheet — solder from this. The reasoning behind every choice here is in
[`guitar_wiring.md`](guitar_wiring.md); this page is only _what goes where_.

Parts: 6 × Ubertar 77HC, Porter Filtertron (2-conductor), 2 × A500K pots,
33 nF cap (marked `.033`), Les Paul-style 3-way toggle, closed-circuit (switched) mono 1/4"
jack, 13-pin GK socket.

## The diagram

```text
 ═══ HEX ═══════════════════════════════════════════════════════════════════════

                                            ┌──────── 13-PIN GK SOCKET ────────┐
  Ubertar 1 (high E)  hot ─────────────────▶│ 1                                │
  Ubertar 2 (B)       hot ─────────────────▶│ 2                                │
  Ubertar 3 (G)       hot ─────────────────▶│ 3                                │
  Ubertar 4 (D)       hot ─────────────────▶│ 4                                │
  Ubertar 5 (A)       hot ─────────────────▶│ 5                                │
  Ubertar 6 (low E)   hot ─────────────────▶│ 6                                │
                                            │                                  │
  jack NC lug ─────────────────────────────▶│ 7   magnetic                     │
                                            │ 8   ·  empty                     │
                                            │ 9   ·  empty                     │
  toggle outer lug B ──────────────────────▶│ 10  MIDI on/off                  │
                                            │ 11  ·  empty                     │
                                            │ 12  ·  empty   (+7 V in GK gear) │
                                            │ 13  ·  empty   (−7 V in GK gear) │
                                            │                                  │
  STAR HUB ────────────────────────────────▶│ SHELL / ground lug               │
                                            └──────────────────────────────────┘
  Nothing else touches the hex hots. No pot, no switch, no jack contact.


 ═══ MAGNETIC ══════════════════════════════════════════════════════════════════

                   LP TOGGLE, pair A
  Porter hot ───▶ [outer A ── inner A] ───▶ VOL lug 3 ───────▶ TONE lug 3
                                               │
                                           VOL lug 2 (wiper)
                                               │
                                               ▼
                                     ┌── SWITCHED 1/4" JACK ──┐
                                     │ tip lug                │
                                     │ NC lug  ───────────────┼──▶ GK 7
                                     │ sleeve  ───────────────┼──▶ STAR HUB
                                     └────────────────────────┘

  VOL lug 1 ──▶ VOL pot back            TONE lug 2 (wiper) ──[33 nF]──▶ TONE pot back
                                        TONE lug 1 ·  empty


 ═══ MODE SWITCH ═══════════════════════════════════════════════════════════════

                   LP TOGGLE, pair B
  GK 10 ◀────── [outer B ── inner B]
                             │
                          jumper
                             │
                        frame lug ──▶ STAR HUB

  ✗  Do NOT jumper inner A to inner B. Every Les Paul diagram online does.
     That joins the two pairs and breaks the mode switch.


 ═══ STAR GROUND ═══════════════════════════════════════════════════════════════

  Ubertar 1–6 grounds (white stripe) ──┐   six separate wires
  Porter ground ───────────────────────┤
  VOL pot back ────────────────────────┤
  TONE pot back ───────────────────────┤
  jack sleeve ─────────────────────────┼──▶ STAR HUB ──▶ 13-pin SHELL / ground lug
  toggle frame lug ────────────────────┤
  bridge ground wire ──────────────────┤
  cavity shield  (this ONE point only) ┘

  Every ground gets its own wire to the hub. No chaining part → part → hub.
```

**Mode switch positions:**

| Lever       | Pair A | Pair B | Filtertron | MIDI |
| ----------- | ------ | ------ | ---------- | ---- |
| Guitar only | closed | open   | ✓          | off  |
| Mix         | closed | closed | ✓          | ✓    |
| MIDI only   | open   | closed | off        | ✓    |

## Wire list

Tick them off as you go.

| #   | From                   | To                        | Notes                               |
| --- | ---------------------- | ------------------------- | ----------------------------------- |
| 1   | Ubertar 1 (high E) hot | GK 1                      | Unmarked lead = hot                 |
| 2   | Ubertar 2 (B) hot      | GK 2                      |                                     |
| 3   | Ubertar 3 (G) hot      | GK 3                      |                                     |
| 4   | Ubertar 4 (D) hot      | GK 4                      |                                     |
| 5   | Ubertar 5 (A) hot      | GK 5                      |                                     |
| 6   | Ubertar 6 (low E) hot  | GK 6                      |                                     |
| 7   | Ubertar 1–6 grounds    | Star hub                  | White stripe = ground. Six wires    |
| 8   | Porter hot             | Toggle outer A            |                                     |
| 9   | Porter ground          | Star hub                  | Braided shield, if it has one       |
| 10  | Toggle inner A         | VOL lug 3                 |                                     |
| 11  | VOL lug 3              | TONE lug 3                | "Modern" wiring (see below)         |
| 12  | VOL lug 2 (wiper)      | Jack tip lug              |                                     |
| 13  | VOL lug 1              | VOL pot back              | Short bend-over is fine             |
| 14  | TONE lug 2 (wiper)     | 33 nF cap → TONE pot back | No polarity — either way round      |
| 15  | Jack NC lug            | GK 7                      |                                     |
| 16  | Toggle outer B         | GK 10                     |                                     |
| 17  | Toggle inner B         | Toggle frame lug          | Jumper on the switch                |
| 18  | Toggle frame lug       | Star hub                  |                                     |
| 19  | VOL pot back           | Star hub                  |                                     |
| 20  | TONE pot back          | Star hub                  |                                     |
| 21  | Jack sleeve            | Star hub                  |                                     |
| 22  | Bridge ground          | Star hub                  |                                     |
| 23  | Cavity shield          | Star hub                  | One wire only. Pots touching it is OK |
| 24  | Star hub               | 13-pin shell / ground lug | Short and thick                     |

**"50s" tone variant:** move wire 11 so TONE lug 3 goes to VOL lug **2** instead
of lug 3. It keeps more treble as the volume rolls back. One wire; pick by ear.

**Building the hub:** "star hub" is a job, not a product — nobody sells one
under that name. Any of these does it:

- **Solder lug** (also sold as _solder tag_, _ground lug_, _terminal lug_): a
  flat tab with a screw hole and solder holes. Clamp it under one of the 13-pin
  socket's mounting screws. Match the hole to that screw size.
- **Uninsulated ring terminal**: sold for crimping, but solders fine. Same
  screw-size rule. Get the bare-metal kind, not the plastic-sleeved kind.
- **Tag strip / terminal strip**: a row of solder tags on an insulating strip,
  if you want more room to land a dozen wires. Use one tag as the hub.
- **No part at all**: twist the grounds together, solder the bundle, and run
  one short wire (24) to the socket's ground lug.

All four are a star, as long as each ground arrives on its own wire.

**Shield contact is fine.** The pot bodies and the jack will probably touch the
shielding wherever they poke through the cavity roof. That is normal — the loop
it forms is tiny and sits inside the shield. "One point only" means one
_wire_ (23) from the shield to the hub. Don't add more wires from the shield to
other places, and don't sand or tape around pots to keep them off it.

## Before soldering — meter checks

Every one of these is a part whose layout varies by manufacturer. Measure; don't
trust a diagram, including this one.

- [ ] **Pot lugs.** Turn the shaft fully clockwise. The outer lug that now reads
      ~0 Ω to the middle lug is **lug 3**. Lug 2 is always the middle.
- [ ] **Toggle pair A.** Put the lever at the end you want to be **MIDI only**.
      The pair that reads open is pair A; the pair still closed is pair B.
- [ ] **Toggle pairs are independent.** No continuity between the two inner lugs
      in any position. ✓ Checked 2026-09-18.
- [ ] **Jack NC lug.** With no plug in, one lug reads ~0 Ω to the tip lug; insert
      a plug and it opens. That's the NC lug.
- [ ] **Porter leads.** Which is hot, which is ground — Porter's own diagram.
      Measure its DCR across the bare leads and write it down; you'll want it below.
- [ ] **13-pin socket numbering.** Pin numbers are printed for the _front_ of a
      DIN socket. From the solder side the layout is a **mirror image**. Find the
      numbers molded into the socket body, or check against its datasheet.
- [ ] **String order.** Pin 1 is **high E**. It's the GK standard, not a
      preference — a real GK cable and gear assume it.

## After soldering — continuity tests

No power, no cable, meter on resistance, black probe on the 13-pin shell.

| Red probe on        | Condition                      | Expect                                                          |
| ------------------- | ------------------------------ | --------------------------------------------------------------- |
| GK 1 … 6            | —                              | ~2.5 kΩ each (Ubertar DCR). 0 Ω = short                         |
| GK 7                | Lever Guitar or Mix, vol full  | ≈ Porter DCR                                                    |
| GK 7                | Lever MIDI only                | Much higher — pots only, ~hundreds of kΩ                        |
| GK 7                | Plug in the guitar's 1/4" jack | Open                                                            |
| GK 10               | Lever Guitar only              | Open                                                            |
| GK 10               | Lever Mix or MIDI only         | ~0 Ω                                                            |
| GK 8, 9, 11, 12, 13 | —                              | Open. **Especially 12 and 13** — those are ±7 V in real GK gear |

Then a sound check: guitar's 1/4" into an amp, lever on Guitar or Mix, tap the
Filtertron with a screwdriver. Lever to MIDI only — the tap should go silent.
