# TL072 Buffer Circuit — Phase 1

Single-channel buffer/amplifier between the pickup and Teensy A0.

## Full Schematic

```
                              +9V (battery)
                                |
                  +-------------+-------------+
                  |                           |
               [10uF]  bulk              [0.1uF]  decoupling
               filtering                 (close to chip)
                  |                           |
                 GND                         GND


                              +9V
                               |
                             pin 8 (V+)
                        +------+------+
                        |             |
   77HC Pickup      pin 2           pin 1
   Hot ---[10uF]----> -IN    TL072A   OUT ---[10uF]---+---> Teensy A0
   (no stripe)  +     |             |    +            |
                        |             |                |
                   pin 3|             |               [10K]
                    +IN |             |                |
                        |             |          3.3V (Teensy)
                        +------+------+
                               |
                             pin 4 (V-)
                               |
                              GND


   Feedback (pin 1 to pin 2):

   pin 1 (OUT) ----[100K]---- pin 2 (-IN)


   Input Bias Divider (to pin 3, +IN):

          3.3V (Teensy)
               |
             [10K]
               |
               +--------> pin 3 (+IN)
               |
             [10K]
               |
              GND

         Midpoint = 1.65V


   Output Bias Divider (to Teensy A0):

          3.3V (Teensy)
               |
             [10K]
               |
   [10uF]---->-+--------> Teensy A0
   (from         |
   pin 1 OUT)  [10K]
               |
              GND

         Midpoint = 1.65V


   Grounds (all connected):
   - 9V battery negative
   - TL072 pin 4
   - Teensy GND
   - Pickup ground (white stripe wire)
   - Both voltage divider bottoms
```

### Signal Flow Summary

```
77HC Pickup ──> [10uF cap] ──> TL072 pin 2 (-IN)
                                      |
                               [100K feedback] from pin 1
                                      |
                               TL072 pin 1 (OUT) ──> [10uF cap] ──> voltage divider ──> Teensy A0
```

## How It Works

### 1. DC Bias (Voltage Divider)

The Teensy ADC reads 0–3.3V. The guitar pickup outputs an AC signal centered around 0V. We need to shift it to center around 1.65V (half of 3.3V) so the ADC can read both the positive and negative halves of the waveform.

Two 10K resistors form a voltage divider from the Teensy's 3.3V pin:

```
3.3V --- [10K] ---+--- [10K] --- GND
                   |
                 1.65V bias point
```

This 1.65V reference connects to the op-amp's non-inverting input (+IN, pin 3).

A 0.1uF cap from the bias point to GND can be added to filter noise on the reference voltage.

### 2. Input Stage (DC Blocking)

The 10uF electrolytic capacitor between the pickup and the op-amp's inverting input (pin 2) blocks any DC offset from the pickup, passing only the AC audio signal.

**Polarity:** The positive leg of the electrolytic cap goes toward the side with higher DC voltage (the op-amp side at 1.65V bias). The pickup side sits near 0V DC.

### 3. Gain Stage

The 100K feedback resistor from the output (pin 1) back to the inverting input (pin 2) sets the gain. In this non-inverting configuration with the signal coupled to the inverting input:

- With just the 100K feedback and no input resistor to ground on pin 2, the circuit acts as a voltage follower with unity gain for the AC signal, biased at 1.65V.
- If the pickup signal is too weak, add a resistor from pin 2 to the bias point to set gain: **Gain = 1 + (100K / R_in)**. For example, a 10K resistor gives gain of 11x.

Start with unity gain (100K feedback only, no resistor to bias). If the signal is too small on the ADC, add the gain resistor.

**What we found:** Unity gain and even 11x was not enough for the 77HC single-string pickup. Multiple 10K resistors in parallel were needed to bring the gain high enough for reliable pitch detection. The feedback was also doubled to 200K (two 100K in series) for additional gain. High strings need significantly more gain than low strings.

### 4. Output Stage (DC Blocking)

The 10uF electrolytic capacitor between the op-amp output and Teensy A0 blocks the 1.65V DC bias, passing only the AC signal. But wait — the Teensy also needs a DC bias at its input.

**Add a second voltage divider at the Teensy input:**

```
                              3.3V
                               |
                             [10K]
                               |
TL072 OUT ----[10uF]---+-------+-------> Teensy A0
                       |       |
                       |     [10K]
                       |       |
                      GND     GND
```

This re-biases the signal to 1.65V at the ADC input, centering it in the Teensy's 0–3.3V range.

### 5. Power Decoupling

Place a 0.1uF ceramic capacitor between pin 8 (+V) and pin 4 (GND) of the TL072, as close to the chip as possible. This filters high-frequency noise from the power supply.

A 10uF electrolytic across the 9V battery leads (at the breadboard power rail) provides additional bulk filtering.

## Pin Reference — TL072 (DIP-8)

```
        +---v---+
 OUT A  | 1   8 |  V+  (+9V)
 -IN A  | 2   7 |  OUT B  (unused)
 +IN A  | 3   6 |  -IN B  (unused)
 V-     | 4   5 |  +IN B  (unused)
        +-------+
           GND
```

We only use channel A (pins 1-3) for Phase 1. Channel B (pins 5-7) is available for a second string in Phase 2.

## Breadboard Layout

830-point breadboard. All signal components on the **bottom side** of the center channel.

```
+9V Rail (top)  ====================================================
GND Rail (top)  ====================================================

  Teensy: starts at col 3, straddling center channel
  TL072:  starts at col 55, straddling center channel

  TL072 pin mapping (as placed):
      Top side:    8(col55)  7(col56)  6(col57)  5(col58)
      Bottom side: 1(col55)  2(col56)  3(col57)  4(col58)
```

### Wiring (all on bottom side unless noted)

| Connection                   | From               | To                 | Notes                               |
| ---------------------------- | ------------------ | ------------------ | ----------------------------------- |
| 9V battery red               | far left           | + rail (top)       |                                     |
| 9V battery black             | far left           | - rail (top)       |                                     |
| TL072 V+                     | col 55 top side    | + rail             | jumper wire                         |
| TL072 GND                    | col 58 bottom      | - rail             | jumper wire                         |
| Power decoupling             | + rail             | - rail             | 0.1uF ceramic cap, near TL072 wires |
| Teensy GND                   | Teensy GND pin     | - rail             | jumper wire                         |
| Input bias: 3.3V to midpoint | Teensy 3.3V        | col 35             | 10K resistor                        |
| Input bias: midpoint to GND  | col 35             | - rail             | 10K resistor (or jumper + resistor) |
| Bias to op-amp               | col 35             | col 57 (pin 3 +IN) | jumper wire                         |
| Feedback                     | col 55 (pin 1)     | col 56 (pin 2)     | 100K resistor                       |
| Input cap                    | col 45             | col 56 (pin 2 -IN) | 10uF electrolytic, + leg at col 56  |
| Output cap                   | col 55 (pin 1)     | col 41             | 10uF electrolytic, + leg at col 55  |
| Output bias: 3.3V to mid     | col 37 (from 3.3V) | col 41             | 10K resistor                        |
| Output bias: mid to GND      | col 41             | - rail             | 10K resistor (or jumper + resistor) |
| ADC input                    | col 41             | Teensy A0          | jumper wire                         |
| Pickup hot (no stripe)       | pickup             | col 45             | direct into breadboard              |
| Pickup ground (white stripe) | pickup             | - rail             | direct into breadboard              |

## Parts Used (Phase 1)

| Part                        | Quantity | Purpose                                          |
| --------------------------- | -------- | ------------------------------------------------ |
| TL072 (DIP-8)               | 1        | Buffer/amplifier (using channel A only)          |
| 10K resistors               | 4        | Two voltage dividers (input bias + output bias)  |
| 100K resistor               | 1        | Feedback resistor                                |
| 10uF electrolytic caps      | 3        | Input DC block, output DC block, power filtering |
| 0.1uF ceramic cap           | 1        | Power decoupling                                 |
| 9V battery + snap connector | 1        | Op-amp power supply                              |

## 6-String Layout (Phase 2 — MCP6002 @ 3.3V)

All 3 MCP6002s sit on **one breadboard**, in a row, with identical per-chip wiring lanes. The second breadboard is reserved for the Teensy and scratch space (and helps isolate digital from analog).

This layout is a clean rebuild — board 1's existing Phase-1 wiring stays alive as a fallback while you bring up the new board.

### Chip placement (single breadboard)

| Chip | Col | Strings        | ADC pins |
| ---- | --- | -------------- | -------- |
| A    | 13  | E2 (1), A2 (2) | A0, A1   |
| B    | 29  | D3 (3), G3 (4) | A2, A3   |
| C    | 45  | B3 (5), E4 (6) | A4, A5   |

Spacing: 16 cols between chips. Each chip + its lane (pickup at N−12, output bias at N−8, feedback at N−2, chip at N..N+3) fits in a 16-col slot. Cols 49–63 stay free.

### Rail conventions

| Rail       | Net        | Source                                             |
| ---------- | ---------- | -------------------------------------------------- |
| Top + rail | 3.3V       | jumper from Teensy 3.3V                            |
| Top − rail | GND        | jumper from Teensy GND                             |
| Bot + rail | 1.65V bias | sourced from one 10K-10K divider at the left edge  |
| Bot − rail | GND        | jumper from top − rail (left edge)                 |

Bot + rail carries the bias along the entire length of the board, so every gain resistor and `+IN` jumper goes to the same rail. No spaghetti — the bias jumpers all run vertically and parallel.

### Per-board setup (do once)

| #   | Action      | From               | To                 | Component |
| --- | ----------- | ------------------ | ------------------ | --------- |
| 1   | Power       | Teensy 3.3V        | top + rail         | jumper    |
| 2   | Power       | Teensy GND         | top − rail         | jumper    |
| 3   | GND bridge  | top − rail (col 1) | bot − rail (col 1) | jumper    |
| 4   | Bias divide | top + rail (col 2) | bot + rail (col 2) | 10K       |
| 5   | Bias divide | bot + rail (col 3) | top − rail (col 3) | 10K       |

After step 5, bot + rail sits at 1.65V (the divider midpoint).

### Per-chip setup (do once per chip — A, B, C)

Notch faces **left**. Pins 1–4 on bottom side of center channel, pins 5–8 on top.

| #   | Action   | From                | To         | Component             |
| --- | -------- | ------------------- | ---------- | --------------------- |
| 6   | VDD      | col N top (pin 8)   | top + rail | jumper                |
| 7   | VSS      | col N+3 bot (pin 4) | bot − rail | jumper                |
| 8   | Decouple | top + rail          | top − rail | 0.1uF, close to col N |

(N = 13 for chip A, 29 for chip B, 45 for chip C.)

### Per-channel template (do 6 times — once per string)

Channel A = bottom side of center channel. Channel B = top side. Same column offsets relative to the chip in both cases.

| #   | Component        | From                | To                       | Notes                                |
| --- | ---------------- | ------------------- | ------------------------ | ------------------------------------ |
| a   | jumper           | +IN pin             | bot + rail (1.65V)       | spans across center channel for ch B |
| b   | pickup hot       | cable               | col N−12 (same side)     | enters breadboard                    |
| c   | 10uF input cap   | col N−12            | −IN pin                  | + leg toward chip                    |
| d   | 100K             | OUT pin             | col N−2 (same side)      | feedback ½                           |
| e   | 100K             | col N−2 (same side) | −IN pin                  | feedback ½ (200K total)              |
| f   | 3 × 10K parallel | −IN pin             | bot + rail               | gain (spans center channel for ch B) |
| g   | 10uF output cap  | OUT pin             | col N−8 (same side)      | + leg toward chip                    |
| h   | 10K              | top + rail          | col N−8 (same side)      | output bias upper                    |
| i   | 10K              | col N−8 (same side) | top − rail or bot − rail | output bias lower                    |
| j   | jumper           | col N−8 (same side) | Teensy A_n               | ADC out                              |
| k   | pickup ground    | cable               | top − rail or bot − rail | (any GND point)                      |

Pin reference per chip (notch left):

- Channel A: OUT = col N bot (pin 1), −IN = col N+1 bot (pin 2), +IN = col N+2 bot (pin 3)
- Channel B: OUT = col N+1 top (pin 7), −IN = col N+2 top (pin 6), +IN = col N+3 top (pin 5)

### Resolved column map for all 6 strings

| String | Chip       | Side   | Pickup col | Output col | ADC pin |
| ------ | ---------- | ------ | ---------- | ---------- | ------- |
| 1 (E2) | A (col 13) | bottom | col 1 bot  | col 5 bot  | A0      |
| 2 (A2) | A (col 13) | top    | col 1 top  | col 5 top  | A1      |
| 3 (D3) | B (col 29) | bottom | col 17 bot | col 21 bot | A2      |
| 4 (G3) | B (col 29) | top    | col 17 top | col 21 top | A3      |
| 5 (B3) | C (col 45) | bottom | col 33 bot | col 37 bot | A4      |
| 6 (E4) | C (col 45) | top    | col 33 top | col 37 top | A5      |

### Parts count for all 6 strings

| Part              | Quantity | Where                                                       |
| ----------------- | -------- | ----------------------------------------------------------- |
| MCP6002 (DIP-8)   | 3        | One row, cols 13/29/45                                      |
| 10K resistor      | 32       | 2 (board bias divider) + 6 × 2 (output bias) + 6 × 3 (gain) |
| 100K resistor     | 12       | 6 × 2 (feedback as series pair)                             |
| 10uF electrolytic | 12       | 6 × input cap + 6 × output cap                              |
| 0.1uF ceramic     | 3        | One per chip, decoupling                                    |
| Jumper wires      | ~30      | Power, bias, +IN to bias, ADC outs, pickup wires            |

## Troubleshooting

- **ADC reads ~0 or ~4095 constantly:** DC bias is wrong. Check voltage dividers — measure the voltage at A0 with a multimeter, should be ~1.65V with no signal.
- **ADC reads ~2048 but no signal variation:** Check pickup wiring, input cap polarity, feedback resistor connection.
- **Signal is clipped (flat tops/bottoms):** Gain is too high or op-amp is hitting the rails. The TL072 on 9V can only swing roughly 1.5V to 7.5V — but we only need it to swing around 1.65V within a 3.3V window, so this shouldn't be an issue at unity gain.
- **Noisy signal:** Check decoupling cap placement (should be right next to TL072). Make sure 9V and USB grounds are connected. Keep pickup wires short and away from the Teensy.
