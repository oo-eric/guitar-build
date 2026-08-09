# Breadboard wiring — HISTORICAL

> ## ⚠️ Do not build from this page.
>
> This documents the **superseded Phase-1 circuit**: TL072 running on a 9V
> battery. That circuit was replaced by the MCP6002 running on 3.3V from the
> Teensy — no battery — and the two are not interchangeable. The TL072 needs 7V+
> and a weak battery produced distorted output; the MCP6002 also roughly halves
> the output swing, so the onset/offset thresholds differ too.
>
> **The circuit of record is [`buffer_circuit.md`](buffer_circuit.md).** For the
> built version, `hardware/` holds the generated KiCad schematic and PCB, and
> `scripts/check_kicad_netlist.py` asserts that the netlist matches the doc.
>
> **It also contains a known error.** Step 4 of the last section routes the gain
> resistors correctly to the input bias point (col 21), but an earlier revision
> of this page sent them to the output chain (col 30), which shorts the output to
> the inverting input. Related: the Phase-1 breadboard fed the pickup into −IN,
> making the circuit inverting — gain then stops matching `1 + Rf/Rg` and starts
> tracking pickup impedance. See the reconciliation section of
> `buffer_circuit.md`.
>
> Kept as a record of how the prototype was actually wired, not as instructions.

---

1. 10K resistor #1: One leg from the Teensy 3.3V row (col 3) to col 20
2. 10K resistor #2: One leg in col 20, other leg to the GND rail
3. Jumper wire: From col 20 to the Teensy A0 row (col 13)
4. Jumper wire: From Teensy GND (col 2) to GND rail

---

1. Place TL072 straddling center channel, left side at col 55
2. 0.1uF ceramic cap between + rail and GND rail, near the TL072 (col 51)
3. 9V battery red → + rail
4. 9V battery black → – rail
5. Jumper from TL072 pin 8 (col 55 top side) → + rail
6. Jumper from TL072 pin 4 (col 58 bottom side) → GND rail

---

1. 10K resistor from Teensy 3.3V row → col 21
2. 10K resistor from col 21 → GND rail
3. Jumper from col 21 → TL072 pin 3 (+IN, col 57 bottom side)
4. 200K feedback: 100K resistor from col 55 (pin 1 OUT) → col 53, 100K resistor from col 53 → col 56 (pin 2 –IN)
5. 10uF electrolytic cap — positive leg at col 55 (pin 1 OUT), negative leg at col 41, jumper col 41 to col 30, jumper col 30 to col 20. (existing A0 junction)

---

1. 10uF electrolytic cap — positive leg at col 56 (pin 2 –IN, bottom side), negative leg at col 45
2. Pickup hot wire (no stripe) → col 45
3. Pickup ground wire (white stripe) → GND rail
4. Gain resistors: multiple 10K resistors in parallel from col 56 (pin 2 –IN) to col 48, jumper from col 48 to col 21 (input bias point)
