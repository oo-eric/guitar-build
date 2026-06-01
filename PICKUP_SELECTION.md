# Standard (Magnetic) Pickup Selection

> **DECIDED: TV Jones (neck position), Universal mount.** Hum-cancelling
> (survives the digital noise environment), bright/chimey Filtertron voice that
> pairs well with the warm-clear korina body, and the body blank is pre-routed
> for it. The rest of this doc is the reasoning that led here.

The build is a hybrid instrument:

- **Six hex single-string pickups** → Teensy 4.0 → pitch-to-MIDI (MPE)
- **One standard magnetic pickup** → 1/4" jack → amp, for the actual guitar tone

This document covers what to weigh when choosing the standard pickup
(humbucker / Strat single / Tele / P90 / TV Jones) given how it interacts
with the rest of the build.

---

## 1. Noise immunity (likely the #1 constraint)

The build has a 600 MHz MCU, SPI, switching activity, and a history of
fighting ADC noise. A magnetic pickup is an antenna — it will pick up
60-cycle hum _and_ digital hash from the Teensy.

Hum-cancelling designs reject that common-mode noise:

- **Humbucker** — best rejection (two coils series-opposing).
- **TV Jones / Filtertron** — also hum-cancelling, voiced brighter.
- **Stacked / noiseless singles** — single-coil tone with hum-cancelling.

Bias toward a hum-cancelling type unless willing to add shielding and keep
the audio ground star-grounded away from the digital ground.

## 2. Physical real estate & placement

**Decided layout:** hex pickups sit near the bridge; the standard pickup goes
in a **middle / neck-ward position**, between the neck and bridge. Position
dictates tone more than type:

- Neck = warm/round, Bridge = bright/cutting, Middle = balanced.
- A middle/neck-ward slot is **away from the bridge**, so the pickup sees more
  string excursion → warmer, fuller, more fundamental and a hotter signal.
  This is a forgiving, musical position for a general-purpose guitar voice.
- It also opens up **physical distance from the hex array** at the bridge,
  which reduces both mounting conflicts and magnetic interaction (see §3).
- **Footprint:** P90 (soapbar) and humbucker are wide; Strat/Tele singles
  are narrow. With the standard pickup pulled away from the bridge, footprint
  is less likely to foul the hex array.

### TV Jones mounting: "ears" (English) vs. Universal

"Ears" are mounting tabs, not a tonal difference — they only change how the
pickup attaches.

- **With ears = English Mount** — traditional Gretsch Filtertron style. Tabs
  flank the long sides and the screws pass _through the ears_; the pickup
  hangs from them. Use for a real Gretsch route or vintage look.
- **Without ears = Universal Mount** — mounts like a standard PAF-sized
  humbucker: drops into a normal humbucker rout with a standard humbucker
  ring (or direct-mount). Fits the vast majority of guitars and aftermarket
  hardware.
- **T-Armond** — a separate mount for their wide single-coil-style models.

**For this build:** routing a custom body for the middle position →
**Universal mount (no ears)** is the easier choice (standard humbucker rout +
standard rings, most available hardware). Only pick the eared English mount
for the Gretsch aesthetic or an existing Gretsch-style route.

## 3. Magnetic interaction

Strong magnets (ceramic humbuckers, P90 bar magnets) close to the strings
cause "stratitis" — magnetic pull that kills sustain and skews intonation.
Worse here: a strong field near the **hex pickups** could subtly affect their
string sensing. Favor moderate-output **alnico** magnets and keep the standard
pickup a reasonable distance from both the strings and the hex sensors.

## 4. Tone character (quick map)

| Type                      | Character                                                       | Output   | Hum-cancelling?        |
| ------------------------- | --------------------------------------------------------------- | -------- | ---------------------- |
| **Humbucker**             | Fat, warm, rolled-off highs, wide aperture (less string detail) | High     | Yes                    |
| **Strat single**          | Glassy, bright, articulate, quacky                              | Low      | No                     |
| **Tele**                  | Bridge: twangy/bright w/ baseplate mid bump; neck: dark/mellow  | Med-low  | No                     |
| **P90**                   | Single-coil grit + humbucker-ish midrange thickness             | Med-high | No (unless HC version) |
| **TV Jones (Filtertron)** | Chimey, clear, jangly highs                                     | Med      | Yes                    |

## 5. Output level & blending

**The standard pickup goes out its own channel and is blended externally**
(at the mixer / interface), not on the guitar. This relaxes the output-matching
concern considerably — relative level and tone are dialed in downstream, so
there's no need to pick a pickup whose raw output matches the MIDI voices.

What still matters:

- **Headroom into the front end** — a hot pickup can clip whatever it feeds
  first (preamp/DI). Easy to pad externally, but worth a thought.
- **Tone is committed at the source.** External blending sets _level and EQ_,
  not pickup character — choose the type for the voice you want, since you
  can't un-bake a dark humbucker into a bright single coil at the mixer.

## 6. Wiring complexity

4-conductor humbuckers (and TV Jones) allow coil-split / series-parallel
options later. Singles are 2-wire and simple. More leads = more flexibility
but more to route in an already-crowded cavity.

---

## Decision: TV Jones (neck position)

**Chosen: TV Jones / Filtertron**, Universal mount, neck position.

- Hum-cancelling — survives the digital noise environment.
- Bright/chimey Filtertron voice complements the warm-clear korina body.
- Body blank is **pre-routed for the TV Jones** at the neck.
- (The runner-up was a moderate-output alnico humbucker — also hum-cancelling,
  warmer/darker. Kept here for reference if ever swapping.)

If classic single-coil sparkle had been the goal instead, the move would have
been **noiseless / stacked** rather than a true vintage single.

### Price ranges (per pickup, street price, USD — approximate)

**TV Jones** — boutique-only, no budget line:

- Classic / Classic Plus, Power'Tron, Magna'Tron, etc.: **~$150–200 each**
- Budget route into the _Filtertron sound_: Gretsch-branded or import
  Filtertron-style (TV Jones-licensed or clone): **~$50–110**

**Alnico humbuckers** — wide spread:

- Budget / import (Epiphone, GFS, Tonerider): **~$30–70**
- Mainstream (Seymour Duncan, DiMarzio, Gibson): **~$80–140**
- Boutique (Lollar, Bare Knuckle, Wolfetone, Fralin): **~$150–300+**

**Bottom line:** a TV Jones sits in good-name-brand-to-boutique territory
(~$150–200). A mainstream alnico humbucker is roughly half to two-thirds the
cost; the TV Jones premium buys the Filtertron voice specifically. Since this
build needs only **one** pickup, the absolute difference is modest (~$60–100) —
let tone preference drive the choice, not price.

### Open questions that would sharpen the choice

1. ~~**Where can it physically go**~~ — Resolved: hex pickups at the bridge,
   standard pickup in a middle / neck-ward position. Warmer, fuller voice and
   good separation from the hex array.
2. ~~**What's the role / blending**~~ — Resolved: separate channel, blended
   externally. Choose for tone character, not output matching.

Both open questions are now resolved. The decision reduces to **tone character**
under three fixed constraints: hum-cancelling (noise), alnico / moderate output
(magnetic interaction), and a footprint that fits the middle position.
