# Guitar Build

Physical guitar build notes and decisions.

## Specs

- **Scale length:** 25.5" (standard)
- **Body:** Korina (limba), pre-routed blank, offset shape
- **Bridge:** Hipshot Hardtail
- **Neck:** Pre-routed blank, modern tiltback headstock construction, SRV profile, 24 frets, 6105 (narrow-tall) nickel-silver frets, paddle headstock (custom cut)
- **Neck wood:** Purpleheart
- **Fretboard:** Pau ferro, 13" radius (straight) — Les Paul-ish feel, nudged flatter for bends; see "Fretboard radius" note below
- **Pickups:** 6x Ubertar 77HC single-string pickups (bridge), Porter Pickups Filtertron-sized (neck)
- **Tuning:** E standard

### Fretboard radius

**Decided: straight 13" radius** (Les Paul-ish feel, nudged one inch flatter
for bends). Chosen on hands-on preference, starting from the Les Paul's 12".
Earlier considered 10–16" compound, tighter/rounder, and flatter still.

Why straight 13" works well here:

- **Started from the Les Paul feel (12").** The player likes how an LP plays in
  hand; 13" keeps that character — only 1" flatter, still firmly LP-ish.
- **Nudged flatter for bends.** A bit flatter than 12" lowers achievable action
  and adds bend headroom. Picked 13" over 12.5" because a half-inch step is
  barely perceptible — if moving for bends, make it count. (16"+ would be a
  notably more modern/shred feel, further from the LP target.)
- **Flat enough that fret-out isn't a concern** — that worry applies to _tight_
  radii (7.25"/9.5"), not 12–13".
- **Simpler to build:** a straight radius is easier/cheaper to cut, fret, and
  level than a compound.
- Radius is **pure feel** — zero effect on the hex pickups or MIDI path (string
  heights are set per-string by the 3D bracket regardless of board radius).

Tradeoff vs. the old 10–16" compound: gives up the compound's slightly rounder
chord zone (10") and slightly flatter solo zone (16") at the extremes — a small
price for consistency and the preferred feel.

Reference radii: vintage Fender 7.25" (very round) · modern Fender 9.5" ·
Les Paul / Gibson 12" · **13" ← chosen** · flat/modern 16" · compound options
9.5–14" or 10–16".

## Bridge

**Choice:** Hipshot Hardtail (fixed, individual saddles, string-through or top-load).

**Why a hardtail (not a tremolo):**

- **Tuning stability for pitch-to-MIDI** — the main driver. A tremolo
  constantly bends pitch, which wrecks YIN pitch detection, MIDI note
  tracking, and the per-string pitch-bend channels. A fixed bridge keeps
  every string at a rock-solid frequency — exactly what the Teensy needs.
- **Individual saddles** — precise per-string intonation _and_ a defined
  string spacing at the bridge. That spacing drives where the six hex pickups
  sit (EMG Strat route + 3D-printed bracket), so adjustable saddles matter.
- **String-through or top-load** — Hipshot supports both, giving flexibility
  against the routing / ferrule choices.
- **Simplicity & body integrity** — no trem cavity means more solid wood and
  one less source of mechanical/tuning instability; suits the rear-routed
  control-cavity design.

**Hardtail variations (all fixed-bridge, the axes that matter here):**

| Type                             | Intonation                    | String spacing                  | Notes                                                               |
| -------------------------------- | ----------------------------- | ------------------------------- | ------------------------------------------------------------------- |
| **Hipshot Hardtail** ← chosen    | Individual saddles            | Fixed by plate                  | Compact footprint, string-through _or_ top-load                     |
| Vintage Strat hardtail           | Individual bent-steel saddles | Fixed by plate                  | Cheap, classic; top-load or through                                 |
| Tune-o-matic + stopbar           | Individual saddles            | Fixed                           | Gibson-style, two-piece, top-load only, taller                      |
| Wraparound                       | Limited (unless compensated)  | Fixed                           | Simplest, fewest parts; coarser intonation                          |
| Individual single-string bridges | Per-string, total control     | **Fully adjustable per string** | Each string its own unit — max spacing control, more parts to align |

Spacing note: the **individual single-string bridge** route is worth a thought
since string spacing directly determines hex-pickup alignment — it would let
spacing be dialed in exactly. The tradeoff is more pieces to mount and
intonate precisely. The Hipshot Hardtail's fixed-plate spacing is simpler;
just **measure its string spacing before routing** the hex-pickup bracket.

**Decision: keep the Hipshot Hardtail.** The string-spacing concern mostly
dissolves because the **3D-printed bracket is the made-to-fit part** — pick the
bridge, measure its spacing, then model the bracket to match. A fixed bridge
spacing is the _input_ you design around, not a constraint, so an adjustable
bridge isn't needed for alignment. The Hipshot wins on what matters here:

- **Simplicity / setup risk** — one plate sets radius, height, and spacing.
  Six individual bridges = six units to intonate, height-set, and align to a
  consistent radius (lots of ways to get uneven action on a first build).
- **Stability** — fewer parts, string-through option, solid coupling; good for
  feel and for the tuning stability MIDI tracking depends on.
- **Compact footprint** — tidy right where the hex array sits.

**Revisit only if:** crosstalk testing later shows adjacent hex pickups bleed
too much from neighboring strings. Adjustable per-string spacing (individual
single-string bridges) would then be a real tool to spread the strings and
reduce magnetic bleed. Short of that, it's complexity without payoff.

## Controls

- 6 toggle switches — individual pickup on/off
- 3 knobs — volume + TBD (tone, MIDI CC, etc.)
- **13-pin DIN jack (Roland GK standard)** — signal out to stomp box.
  Carries the six hex signals _and_ the magnetic pickup on one cable.

## Routing

- **Rear routed** control cavity with back plate cover — **NOT pre-routed; omitted from the order (no upcharge), cut yourself after drawing the outline** so it fits the final control layout
- 1x Filtertron-sized route at neck — analog pickup — **pre-routed in blank**
  (ordered as a TV Jones route; the Porter is the same size and drops in)
- Neck pocket — **pre-routed in blank**
- Bridge mounting holes — **pre-drilled in blank** (fixes bridge position → fixes the string path)
- 1x bridge route for the 6 hex pickups (3D-printed bracket) — **NOT pre-routed; cut after measuring string spacing** off the installed bridge
- String spacing at bridge determines pickup positioning — measure before routing
- Cavity sized generously for future control additions
- **Rear cavity depth — target ~22–25 mm (≈1").** Real driver is the deepest
  top-mounted component body (mini-toggle or pot) below the top face + ~3–5 mm
  wire/solder clearance. Keep a **≥5 mm floor** under the cavity for strength.
  **Measure on arrival:** mic the blank thickness and the deepest component, then
  set depth = (component protrusion + clearance), confirm floor ≥5 mm before
  routing. Korina ~44 mm thick leaves plenty of margin.

## Output

- **One cable out: 13-pin DIN (Roland GK standard)** → stomp box (Teensy +
  op-amps). Hex signals on pins 1–6, ground on 7, **magnetic pickup on pin 8**
  — the GK standard has a dedicated pin for exactly that, so the Porter rides
  the same cable instead of needing its own.
- **Analog:** Porter (neck) → pin 8 → 1/4" jack **on the stomp box** →
  amp/pedalboard
- Guitar itself has no active electronics — just pickups, switches, and passive
  wiring. Pins 9/10 (±7V in the GK standard) are left unconnected.
- Both outputs work simultaneously and independently
- Full pin table and rationale: `plan.md` → "13-Pin Interface"

## Parts Needed

| Part                                                    | Notes                                                                                                                                           | Acquired |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| Body blank — korina (limba), pre-routed, standard scale | **Ordered.** Open grain — plan grain filler for finish. Limba dust is a skin/respiratory sensitizer — respirator when sanding                   | [~]      |
| Neck blank (tiltback, pau ferro fretboard, 13" radius)  | **Ordered.** SRV profile, 24 frets, 6105 narrow-tall nickel-silver, paddle headstock                                                            | [~]      |
| 13-pin DIN jack (panel mount), GK standard              | **×2** — one on the guitar, one on the stomp box. ~$10–15 each                                                                                  | [ ]      |
| 13-pin GK cable                                         | Guitar to stomp box. Buy, don't build — that's the whole reason for conforming to the standard. Roland ~$30–60, third-party ~$20–30             | [ ]      |
| Hammond 1590DD enclosure                                | Stomp box. ~188 × 120 mm — clears the 82 × 156 mm board. 1590BB / 1590XX are too small                                                          | [ ]      |
| Hipshot Hardtail bridge                                 | Individual saddles, string-through or top-load. **Measure string spacing before routing the hex-pickup bracket** — it sets hex-pickup alignment | [ ]      |
| Tuners                                                  | 6 inline or 3+3, match headstock                                                                                                                | [ ]      |
| Nut (1-11/16")                                          | Match neck width                                                                                                                                | [ ]      |
| Fret wire — 6105 (narrow-tall), nickel-silver           | Match 13" board radius. Nickel-silver = DIY-friendly to fret/level                                                                              | [ ]      |
| String ferrules or mounting hardware                    | Match bridge choice                                                                                                                             | [ ]      |

## Open Questions

- Body style — offset; **Jazzmaster × Iceman hybrid** (Jazzmaster comfort + Iceman swept lower horn). Outline cut from a rectangular pre-routed blank, drawn around the fixed routes. See `body_shape.md`.
- ~~Bridge~~ — Hipshot Hardtail
- ~~Headstock shape~~ — paddle head, custom cut
- ~~Number of frets~~ — 24
- ~~Fret size & material~~ — 6105 (narrow-tall) nickel-silver. Tall crown = easy bends/vibrato (pairs with the 13" radius), narrow width = precise fretting; nickel-silver chosen for DIY-friendly fretwork over stainless.
- ~~Neck profile~~ — SRV
- ~~Nut width~~ — 1-11/16" (42.86mm), standard Fender. Balanced all-around feel, pairs well with the fat-D SRV profile.
- ~~Body wood~~ — korina (limba). Warm-clear voice that pairs well with the neck P90, adds a bit of weight to balance the dense purpleheart neck, and looks striking under a transparent finish. See `wood_comparison.md`.
- ~~Neck wood~~ — purpleheart
- ~~Finish~~ — semi-transparent, DIY
