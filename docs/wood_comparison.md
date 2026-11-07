# Tonewood Comparison — Body, Neck, Fretboard

Reference for body / neck / fretboard wood choices. Current build picks are
marked **← chosen**. See `guitar_build.md` for the committed spec.

## A note on "tone" for this build

This is a hybrid instrument. The **MIDI path doesn't care about tonewood at
all** — the hex pickups feed pitch detection, which only sees string
vibration frequency. Wood choice affects only:

1. The **analog voice** of the Porter Filtertron (out the 1/4" jack) — and even
   there the effect is subtle and debated.
2. **Weight, balance, feel, stability, and looks** — which are real, immediate,
   and matter more than tone arguments for a player.

So weight, workability, and stability are weighted heavily below.

---

## Body Woods

| Wood                  | Weight    | Tonal reputation                                | Workability / finishing                                                | Notes                                                                 |
| --------------------- | --------- | ----------------------------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **Swamp ash**         | Light–med | Bright, airy, scooped mids, strong highs & lows | Open grain (needs grain filler for gloss), takes stain well            | Classic Fender. Light, resonant, gorgeous grain. Runner-up, see below |
| **Roasted swamp ash** | Lighter   | Same but drier/snappier; more stable            | Easier to finish, darker amber tone, very stable                       | Torrefied — moisture baked out, more dimensionally stable & lighter   |
| Alder                 | Medium    | Balanced, full mids, even                       | Tight grain, finishes easily (no filler)                               | Classic Strat body; cheap, neutral, paints well                       |
| Mahogany              | Med–heavy | Warm, thick mids, soft highs                    | Open grain, easy to carve                                              | Les Paul / SG; warm and woody                                         |
| Basswood              | Light     | Soft, neutral, slightly mid-focused             | Soft (dents easily), needs sealing                                     | Cheap, light; common on import guitars                                |
| Hard/soft maple       | Heavy     | Bright, tight, articulate                       | Hard, heavy; great for tops                                            | Often a thin top cap, not full body                                   |
| **Korina (limba)**    | Med       | Warm-but-clear, great sustain, chimey top       | Open grain (filler optional); white = subtle, black = dramatic streaks | Boutique; pricey. Dust is a skin/respiratory sensitizer. **← CHOSEN** |
| Poplar                | Med       | Alder-like, slightly softer                     | Cheap, paints well (greenish, hide it)                                 | Budget alder substitute                                               |

### Body wood decision: korina (chosen) vs. roasted swamp ash

**Decided: korina (limba).** Chosen over roasted swamp ash, the runner-up, for
the bit of extra weight that helps balance the dense purpleheart neck, its looks
under a transparent finish, and a warm-clear voice. Tradeoff accepted: gives up
the torrefied stability and lighter weight of roasted ash, and costs more.

The voice argument was first made for a **neck P90**. The neck pickup is now a
**Porter Filtertron-sized humbucker**, and the pairing still holds, for a
different reason: korina's warmth fills in under the Filtertron's bright, chimey
top, where with a P90 it was matching midrange with midrange.

| Factor                     | Korina                                  | Roasted swamp ash          |
| -------------------------- | --------------------------------------- | -------------------------- |
| Weight                     | Medium (mahogany-ish but lighter)       | Light                      |
| Analog voice (Filtertron)  | Warm + clear, great sustain, chimey top | Bright, scooped, snappy    |
| Looks (transparent finish) | Stunning — esp. black limba streaks     | Beautiful amber grain      |
| Grain fill                 | Open pores — filler optional            | Also open — similar effort |
| Stability                  | Good                                    | Excellent (torrefied)      |
| Cost / availability        | Pricier, boutique                       | Cheaper, common            |

Build-specific notes:

- **Balance:** korina's extra weight could help offset the dense purpleheart
  neck and reduce neck-dive on the offset body — a plus here.
- **Filtertron pairing:** korina's warm-but-clear voice balances the
  Filtertron's brightness. (Affects the analog jack only, not the MIDI path.)
- **Finish:** planned open-pore under tinted Osmo (see `guitar_build.md` →
  "Finishing supplies"). Grain filling is optional, for a dark-striped look.
- **Health:** limba dust is a known skin/respiratory sensitizer — wear a good
  respirator when sanding.
- **What you'd give up vs. roasted ash:** torrefied dimensional stability and
  the lighter weight.

> **Torrefaction** (what makes "roasted" ash): roasting wood in an
> oxygen-starved oven (~350–400°F) bakes out moisture and breaks down the
> hemicellulose that absorbs water. Result: the wood swells/shrinks far less
> with humidity → stays flat and in-spec ("stability"), plus it's lighter and
> darker amber. Korina is not torrefied, so it's stable but lacks this edge.

---

## Neck Woods

| Wood                  | Stability | Feel / reputation                                    | Notes                                                                                      |
| --------------------- | --------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **Purpleheart**       | Excellent | Very stiff, dense, bright/snappy, strong fundamental | Hard & heavy; striking purple color. Very stable, great for a one-piece neck. **← chosen** |
| Hard maple            | Very good | Bright, snappy, the default                          | Cheap, proven, usually needs finish                                                        |
| Roasted maple         | Excellent | Maple but warmer; very stable                        | Torrefied; often left raw/oiled — great feel                                               |
| Mahogany              | Good      | Warm, softer attack                                  | Les Paul necks; less stiff                                                                 |
| Wenge                 | Excellent | Stiff, dry, grippy raw feel                          | Boutique; splintery to work                                                                |
| Maple/walnut laminate | Excellent | Stiff, decorative stripes                            | Multi-piece resists warping                                                                |

**Why purpleheart works here:** extremely stiff and stable (resists warp under
string tension over a 25.5" / 24-fret neck), bright attack, and the color is a
showpiece against the korina body. Downsides: heavy and hard on tools — sharp
bits, slow feed, expect more sanding. Can be left unfinished or lightly oiled.

---

## Fretboard Woods

| Wood              | Feel                             | Look                       | Notes                                                                                    |
| ----------------- | -------------------------------- | -------------------------- | ---------------------------------------------------------------------------------------- |
| **Pau ferro**     | Smooth, between rosewood & ebony | Med-dark brown, fine grain | Hard, tight-grained, low-oil — finishes clean. CITES-friendly rosewood alt. **← chosen** |
| Rosewood (Indian) | Warm, slightly oily              | Dark brown                 | Classic; CITES-restricted (import hassle)                                                |
| Ebony             | Hard, fast, slick                | Near-black                 | Premium; can crack if dry                                                                |
| Maple             | Hard, bright snap                | Light (needs finish/seal)  | One-piece or capped; shows wear                                                          |
| Roasted maple     | As maple, more stable            | Amber                      | Torrefied                                                                                |

**Why pau ferro works here:** hard and dense for a fast, durable surface, low
oil content so it glues/finishes predictably, and it sidesteps the CITES
paperwork that comes with true rosewood. Pairs well with the straight 13"
radius + 6105 frets.

---

## Combined picks for this build

| Component | Choice         | One-line rationale                                                                                    |
| --------- | -------------- | ----------------------------------------------------------------------------------------------------- |
| Body      | Korina (limba) | Warm-clear (balances the bright Filtertron), adds weight against the dense neck, striking under clear |
| Neck      | Purpleheart    | Very stiff/stable, bright, striking color                                                             |
| Fretboard | Pau ferro      | Hard & fast, predictable finishing, no CITES hassle                                                   |

**Weight watch:** purpleheart is dense — keep an eye on neck-heavy balance on
an offset body. Korina's medium weight should help offset neck-dive vs. a
lighter wood; if it still dives, lighter tuners or body-side ballast can fix it.

**Tooling note:** purpleheart and pau ferro are both hard, dense, and abrasive
on cutting edges. Use sharp, carbide tooling, take light passes, and budget
extra sanding/finishing time vs. softer woods.

---

## Construction: 1-piece vs. 2-piece

Wood _choice_ aside, how the blank is **assembled** affects cost, stability,
and looks.

### Body

|               | 1-piece (single slab)                            | 2-piece (glued at center seam)                                      |
| ------------- | ------------------------------------------------ | ------------------------------------------------------------------- |
| **Sourcing**  | Hard — needs wide clear stock                    | Easy, widely available                                              |
| **Cost**      | Higher                                           | Lower                                                               |
| **Stability** | Wide single board more prone to cup/warp         | Often _more_ stable — grain oriented to oppose movement             |
| **Looks**     | No center seam (prized under transparent finish) | Visible glue line; **bookmatch** to make it symmetric & intentional |

**For this build:** the korina blank has already arrived, so this is now
reference only. In general, a clean **bookmatched 2-piece** is the practical
sweet spot: cheaper, more available, and stable. Under a semi-transparent
finish a centered bookmatched seam reads as deliberate. A 1-piece is an
aesthetic flex, not a functional upgrade.

### Neck — tiltback headstock

The spec calls for **modern tiltback headstock construction**, which almost
always means a **scarf joint** (angled headstock glued on as a separate piece).

- **1-piece tiltback** (angle carved from one thick billet) — seamless look,
  but wastes wood, needs thick stock, and leaves **short, weak grain** at the
  headstock transition (a classic break point).
- **Scarf-joint tiltback** (2-piece) — the glue joint runs **with** the grain
  through the transition, making it **stronger** and far more material-
  efficient. Modern standard; likely what the pre-routed blank already is.

Separately, a **one-piece neck** (neck + headstock back) vs. a neck with a
glued-on fretboard is its own axis — and with a **pau ferro board on a
purpleheart neck**, this build is a 2-piece (neck + fretboard) by definition.
