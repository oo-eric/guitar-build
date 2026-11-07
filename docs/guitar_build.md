# Guitar Build

Physical guitar build notes and decisions.

## Specs

- **Scale length:** 25.5" (standard)
- **Body:** Korina (limba), pre-routed blank, offset shape
- **Bridge:** Hipshot Hardtail
- **Neck:** Pre-routed blank, modern tiltback headstock construction, SRV profile, paddle headstock (custom cut)
- **Neck wood:** Purpleheart
- **Fretboard:** Pau ferro, 13" radius (straight) — see "Fretboard radius" below
- **Frets:** 24, 6105 (narrow-tall) nickel-silver. Tall crown for easy bends and vibrato, narrow for precise fretting; nickel-silver over stainless because it's friendlier to level and dress by hand
- **Nut width:** 1-11/16" (42.86 mm), standard Fender
- **Pickups:** 6x Ubertar 77HC single-string pickups (bridge), Porter Pickups Filtertron-sized humbucker, 2-conductor (neck)
- **Finish:** Osmo 1101 hardwax oil throughout, body tinted with Mixol, open-pore — see "Finishing supplies"
- **Tuning:** E standard

### Fretboard radius

**Straight 13".** Started from the Les Paul's 12", which the player likes in
hand, and went one inch flatter for lower action and more bend headroom. A
half-inch step (12.5") is barely noticeable, and 16" would feel modern rather
than LP. At 12–13" fret-out on bends isn't a concern, and a straight radius is
simpler to cut, fret and level than a compound (10–16" was the alternative).

Radius is feel only. It has no effect on the hex pickups or MIDI: string
heights over the hex array are set per string by the 3D-printed bracket.

## Bridge

**Hipshot Hardtail**, string-through, individual saddles.

- **Tuning stability is the main reason.** A tremolo bends pitch constantly,
  which fights YIN pitch detection and per-string MIDI tracking.
- **Individual saddles** give per-string intonation and a fixed, known string
  spacing at the bridge.
- **One plate** sets radius, height and spacing. Six single-string bridges
  would be six units to intonate and align on a first build.

The bridge's string spacing is the **input** to the hex-pickup bracket, not a
constraint on it: install the bridge, measure the spacing, then model the
bracket to match.

**Revisit only if** crosstalk testing shows adjacent hex pickups picking up too
much of their neighbours. Individual single-string bridges could then spread the
strings to reduce magnetic bleed.

## Controls

**Full wiring, values and rationale: [`guitar_wiring.md`](guitar_wiring.md).**
Summary only here.

Two knobs, one 3-way toggle, two jacks. Revised 2026-09-18 to the parts in hand
(two A500K pots, a Les Paul-style toggle, a 2-conductor Porter).

| Control | Part                                  | Acts on                                                                         |
| ------- | ------------------------------------- | ------------------------------------------------------------------------------- |
| Volume  | A500K (audio taper)                   | Porter only — **not** the hex pickups                                           |
| Tone    | A500K + 0.033 µF (33 nF)              | Porter only                                                                     |
| Mode    | Les Paul 3-way, two independent pairs | **Guitar / Mix / MIDI.** Pair A switches the Porter; pair B → GK 10 → Teensy 21 |

The mode switch replaces the planned CC pot and two momentaries. Its lever
position is the MIDI on/off indicator the guitar otherwise couldn't have.

**The six per-string toggle switches are dropped.** Per-string enable is a
firmware variable on a box that already has a Teensy, a display and an encoder.
In hardware it cost six holes and six control runs sharing a cavity with the six
unbuffered hi-Z hex lines — making the project's top-ranked risk (crosstalk)
worse to buy a feature that is free in software. Worse electrically: opening a
hex hot leaves a floating input on a 46× non-inverting stage, which is _noisier_
switched off than on.

**Nothing is wired into the hex path.** No pot, no switch, no jack contact. Onset
detection uses absolute RMS thresholds, so any attenuator there means a bumped
knob silently stops the MIDI.

Rolling the volume to zero silences the guitar while MIDI keeps playing at full
level — correct, and useful for silent practice.

## Routing

- **Rear routed** control cavity with back plate cover — **NOT pre-routed; omitted from the order (no upcharge), cut yourself after drawing the outline** so it fits the final control layout
- 1x Filtertron-sized route at neck — analog pickup — **pre-routed in blank**
  (ordered as a TV Jones route; the Porter is the same size and drops in)
- Neck pocket — **pre-routed in blank**
- Bridge mounting holes — **pre-drilled in blank** (fixes bridge position → fixes the string path)
- 1x bridge route for the 6 hex pickups (3D-printed bracket) — **NOT pre-routed; cut after measuring string spacing** off the installed bridge
- String spacing at bridge determines pickup positioning — measure before routing
- **Rear cavity depth = deepest component below the top face + 3–5 mm** for
  wire and solder clearance, keeping a **≥5 mm floor** under the cavity. The
  deepest part is now the **Les Paul toggle**, whose long frame hangs well below
  a pot body, so measure it rather than using the old ~22–25 mm estimate (that
  was sized for mini-toggles, since dropped). Mic the blank too; korina at
  ~44 mm leaves plenty of margin.

## Output

**Two jacks.** Decided 2026-09-02.

- **13-pin DIN (Roland GK standard)** → stomp box. Hex on pins 1–6, magnetic
  pickup on pin 7, the mode switch on S1 (pin 10), ground on the shell.
  **Pin 1 is high E.**
- **1/4" jack on the guitar** — a **closed-circuit (switched)** mono jack. Its
  normally-closed contact feeds pin 7, so inserting a plug disconnects pin 7 and
  the magnetic pickup drives the short cable instead of the multicore.

The two magnetic paths are mutually exclusive by construction, which is the
point: wiring them in parallel would halve the load impedance, lose treble, and
create a ground loop the moment they landed in different gear.

| Plugged in       | Magnetic goes to           | MIDI |
| ---------------- | -------------------------- | ---- |
| 13-pin only      | Stomp box 1/4" out         | ✓    |
| Both             | Guitar 1/4" (pin 7 opens)  | ✓    |
| Guitar 1/4" only | Guitar 1/4" — plain guitar | —    |

- Guitar has **no active electronics and no supply rail** — pickups, pots,
  switches, passive wiring. Pins 12/13 (±7 V in the GK standard) stay unconnected;
  the control pins work as closures to ground with all pull-ups in the stomp box.
- Full pin table and rationale: `plan.md` → "13-Pin Interface";
  cavity wiring: [`guitar_wiring.md`](guitar_wiring.md)

## Parts Needed

| Part                                                    | Notes                                                                                                                                                                                                                                                                                     | Acquired |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| Body blank — korina (limba), pre-routed, standard scale | **Arrived 2026-08-08.** Open grain — see Finishing. Limba dust is a skin/respiratory sensitizer — respirator when sanding                                                                                                                                                                 | [x]      |
| Neck blank (tiltback, pau ferro fretboard, 13" radius)  | **Arrived 2026-08-08.** SRV profile, 24 frets, 6105 narrow-tall nickel-silver, paddle headstock                                                                                                                                                                                           | [x]      |
| 13-pin DIN jack (panel mount), GK standard              | **×2** — one on the guitar, one on the stomp box. **In hand**                                                                                                                                                                                                                             | [x]      |
| 13-pin GK cable                                         | Guitar to stomp box. Buy, don't build — that's the whole reason for conforming to the standard. **In hand**                                                                                                                                                                               | [x]      |
| Hammond 1590DD enclosure                                | Stomp box. ~188 × 120 mm — clears the 82 × 156 mm board. 1590BB / 1590XX are too small                                                                                                                                                                                                    | [ ]      |
| Hipshot Hardtail bridge                                 | **In hand.** **String-through.** Individual saddles. **Measure string spacing before routing the hex-pickup bracket** — it sets hex-pickup alignment                                                                                                                                      | [x]      |
| Tuners                                                  | **In hand.** 6 inline or 3+3, match headstock                                                                                                                                                                                                                                             | [x]      |
| 1/4" jack — **closed-circuit (switched)** mono          | **In hand, 3 lugs confirmed — meter test pending** (a stereo TRS jack also has 3 lugs). Guitar-mounted. Its NC contact must break pin 7 on insertion. Must have **3 lugs** (tip, sleeve, NC switch); 2 lugs = open-circuit, wrong part. Meter tip↔NC: ~0 Ω unplugged, open with a plug in | [x]      |
| Pots — 500k audio × 2                                   | Porter volume and tone. **In hand: A500K ×2**                                                                                                                                                                                                                                             | [x]      |
| Tone cap — 0.033 µF (33 nF)                             | **In hand**, marked `.033`, non-polarized. A touch darker than the 22 nF standard when rolled back                                                                                                                                                                                        | [x]      |
| 3-way toggle, Les Paul style                            | Mode switch. Inner lugs **not** jumpered — verified independent. **In hand**                                                                                                                                                                                                              | [x]      |
| Knobs × 2                                               | Match pot shaft type. **In hand**                                                                                                                                                                                                                                                         | [x]      |
| Cavity shielding — copper tape                          | **In hand.** Bond to the star ground at **one point only**. Twice makes the shield a loop                                                                                                                                                                                                 | [x]      |
| Nut (1-11/16")                                          | Match neck width                                                                                                                                                                                                                                                                          | [ ]      |
| Fret wire — 6105 (narrow-tall), nickel-silver           | Match 13" board radius. Nickel-silver = DIY-friendly to fret/level                                                                                                                                                                                                                        | [ ]      |
| String ferrules (string-through)                        | **In hand.** Drill the 6 through-holes from the bridge plate, square to the top (drill press or guide block) — exit holes wander                                                                                                                                                          | [x]      |

### Finishing supplies

Plan: **Osmo hardwax oil on every part, body left open-pore.** Osmo must be the **last** layer on any part it touches — nothing sticks reliably over a hardwax oil — so pick the system per part before the first coat. Test the whole sequence on scrap or inside the neck pocket first.

| Part                                                   | Notes                                                                                                                                                                          | Acquired |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
| Osmo Wood Wax Finish 1101, clear                       | **In hand** (garage). Fretboard, back of neck, body topcoat. Stir to the bottom — skinned or gummy means dead. Thin coats, wipe off all excess or it stays tacky for days      | [x]      |
| Mixol tinting paste — color TBD                        | Body tint. Pigment, so **never straight on the wood** (blotches in korina's pores) — a few drops per cup into the Osmo, build color in thin coats                              | [ ]      |
| Sandpaper 220 / 320 / 400, sanding block               | **In hand.** Stop at **220** on the body before tinting                                                                                                                        | [x]      |
| Lint-free rags                                         | ⚠️ **Oily rags self-ignite.** Dry them flat outdoors or keep them in a sealed can of water                                                                                     | [ ]      |
| Blue painter's tape                                    | Mask the neck pocket and any part getting a different finish                                                                                                                   | [ ]      |
| Respirator, P100 filters                               | **In hand.** Limba dust is a skin/respiratory sensitizer                                                                                                                       | [x]      |
| _Optional:_ water-based clear w/ UV inhibitors, satin  | **Only if the neck back skips Osmo** — see Open Questions. General Finishes Enduro-Var (first pick); Minwax Polycrylic as fallback                                             | [ ]      |
| _Optional:_ Zinsser SealCoat + dark (ebony) Timbermate | **Only for a filled-grain body.** Dark filler stripes the korina pores. Needs SealCoat first or the filler stains the surface. Plus plastic/bondo spreaders + burlap, 2 passes | [ ]      |

## Open Questions

- **Body outline** — Jazzmaster × Iceman hybrid, cut from the rectangular blank
  around the fixed routes. See [`body_shape.md`](body_shape.md).
- **Neck-back finish** — Osmo (fast oiled feel, slight ambering) vs. water-based
  clear with UV inhibitors (keeps purpleheart purple longer). Purpleheart browns
  under UV regardless; the finish only changes how fast. Fretboard gets Osmo
  either way.
- **Body tint color** — not chosen. Test on scrap: korina takes color darker
  than expected.
- **Body grain** — open-pore (default) vs. filled with dark Timbermate (optional
  row in "Finishing supplies").

Settled choices and their reasons are in Specs above; wood reasoning is in
[`wood_comparison.md`](wood_comparison.md).
