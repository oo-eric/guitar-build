1. 10K resistor #1: One leg from the Teensy 3.3V row (col 3) to col 17
2. 10K resistor #2: One leg in col 17, other leg to the GND rail
4. Jumper wire: From col 17 to the Teensy A0 row (col 13)
5. Jumper wire: From Teensy GND (col 2) to GND rail

---

1. Place TL072 straddling center channel, left side at col 55
2. 0.1uF ceramic cap between + rail and GND rail, near the TL072 (col 51)
3. 9V battery red → + rail
4. 9V battery black → – rail
5. Jumper from TL072 pin 8 (col 55 top side) → + rail
6. Jumper from TL072 pin 4 (col 58 bottom side) → GND rail

---

1. 10K resistor from Teensy 3.3V row → col 19
2. 10K resistor from col 19 → GND rail
3. Jumper from col 19 → TL072 pin 3 (+IN, col 57 bottom side)
4. 100K resistor from col 55 (pin 1 OUT) → col 56 (pin 2 –IN)
5. 10uF electrolytic cap — positive leg at col 55 (pin 1 OUT), negative leg at col 41, jumper col 41 to col 30, jumper col 30 to col 17 (existing A0 junction)

---

1. 10uF electrolytic cap — positive leg at col 56 (pin 2 –IN, bottom side), negative leg at col 45
2. Pickup hot wire (no stripe) → col 45
3. Pickup ground wire (white stripe) → GND rail
4. 10K resistor from col 56 (pin 2 –IN) to col 48, jumper from col 48 to col 30