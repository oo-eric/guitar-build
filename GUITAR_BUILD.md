# Guitar Build

Physical guitar build notes and decisions.

## Specs

- **Scale length:** 25.5" (standard)
- **Body:** Roasted swamp ash, pre-routed blank, offset shape
- **Bridge:** Hipshot Hardtail
- **Neck:** Pre-routed blank, modern tiltback headstock construction, SRV profile, 24 frets, 6105 (narrow tall) frets, paddle headstock (custom cut)
- **Neck wood:** Purpleheart
- **Fretboard:** Pau ferro, 10-16" compound radius
- **Pickups:** 6x Ubertar 77HC single-string pickups (bridge), P90 (neck)
- **Tuning:** E standard

## Controls

- 6 toggle switches — individual pickup on/off
- 3 knobs — volume + TBD (tone, MIDI CC, etc.)
- 7-pin DIN jack — signal out to stomp box

## Routing

- **Rear routed** control cavity with back plate cover
- 1x EMG Strat route at bridge — holds all 6 77HC pickups via 3D printed bracket
- 1x P90 route at neck — traditional analog pickup
- String spacing at bridge determines pickup positioning — measure before routing
- Cavity sized generously for future control additions

## Output

- **MIDI:** 7-pin DIN jack → 6 pickup signals + ground → stomp box (Teensy + op-amps)
- **Analog:** P90 → 1/4" jack → amp/pedalboard
- Guitar itself has no active electronics — just pickups, switches, and passive wiring
- Both outputs work simultaneously and independently

## Parts Needed

| Part                                       | Notes                                          | Acquired |
| ------------------------------------------ | ---------------------------------------------- | -------- |
| Body blank (pre-routed, standard scale)    | TBD source                                     | [ ]      |
| Neck blank (tiltback, pau ferro fretboard) | TBD source                                     | [ ]      |
| 7-pin DIN jack (panel mount)               | Guitar side                                    | [ ]      |
| 7-pin DIN plug                             | Cable side                                     | [ ]      |
| 7-conductor shielded cable                 | Guitar to stomp box                            | [ ]      |
| Hipshot Hardtail bridge                    | Individual saddles, string-through or top-load | [ ]      |
| Tuners                                     | 6 inline or 3+3, match headstock               | [ ]      |
| Nut (1-11/16")                             | Match neck width                               | [ ]      |
| Fret wire                                  | Match pau ferro board radius                   | [ ]      |
| String ferrules or mounting hardware       | Match bridge choice                            | [ ]      |

## Open Questions

- ~~Body style~~ — offset (Jazzmaster/Mustang inspired, custom weird)
- ~~Bridge~~ — Hipshot Hardtail
- ~~Headstock shape~~ — paddle head, custom cut
- ~~Number of frets~~ — 24
- ~~Neck profile~~ — SRV
- ~~Body wood~~ — roasted swamp ash
- ~~Neck wood~~ — purpleheart
- ~~Finish~~ — semi-transparent, DIY
