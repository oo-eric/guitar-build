# TL072 Buffer Circuit — Phase 1

Single-channel buffer/amplifier between the pickup and Teensy A0.

## Schematic

```
                          +9V Rail
                            |
                            |
                     [0.1uF ceramic]  (power decoupling, close to TL072)
                            |
                           GND

                          +9V Rail
                            |
                          pin 8
                     +------+------+
                     |             |
   Pickup        pin 2           pin 1
   Hot ----[10uF]----> -IN        OUT ---+---[10uF]---> Teensy A0
                     |             |     |
                pin 3|             |     |
                  +IN|   TL072A    |     |
                     |             |     |
                     +------+------+     |
                            |            |
                          pin 4         [100K]  (feedback)
                            |            |
                           GND           |
                            |     pin 2 -IN <---+
                            |

                     Bias Network
                     (connects to TL072A pin 3, +IN)

                          3.3V (from Teensy)
                            |
                          [10K]
                            |
                            +--------> TL072A pin 3 (+IN)
                            |
                          [10K]
                            |
                           GND
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

```
+9V Rail  =========================================
GND Rail  =========================================

  [9V snap] red  --> +9V rail
  [9V snap] black --> GND rail

  Teensy GND pin --> GND rail
  Teensy 3.3V pin --> 3.3V rail (or direct to divider)

  Row 1:  TL072 straddling center channel (pin 1 top-left)
  Row 2:  0.1uF ceramic cap from pin 8 row to pin 4 row (decoupling)
  Row 3:  10K + 10K voltage divider from 3.3V to GND, midpoint to pin 3
  Row 4:  100K feedback from pin 1 row to pin 2 row
  Row 5:  10uF input cap from pickup jack to pin 2 row
  Row 6:  10uF output cap from pin 1 row toward A0
  Row 7:  10K + 10K output bias divider, midpoint to A0

  Pickup hot --> input cap --> pin 2
  Pickup ground --> GND rail
```

## Parts Used (Phase 1)

| Part                        | Quantity | Purpose                                          |
|-----------------------------|----------|--------------------------------------------------|
| TL072 (DIP-8)               | 1        | Buffer/amplifier (using channel A only)          |
| 10K resistors               | 4        | Two voltage dividers (input bias + output bias)  |
| 100K resistor               | 1        | Feedback resistor                                |
| 10uF electrolytic caps      | 3        | Input DC block, output DC block, power filtering |
| 0.1uF ceramic cap           | 1        | Power decoupling                                 |
| 9V battery + snap connector | 1        | Op-amp power supply                              |

## Troubleshooting

- **ADC reads ~0 or ~4095 constantly:** DC bias is wrong. Check voltage dividers — measure the voltage at A0 with a multimeter, should be ~1.65V with no signal.
- **ADC reads ~2048 but no signal variation:** Check pickup wiring, input cap polarity, feedback resistor connection.
- **Signal is clipped (flat tops/bottoms):** Gain is too high or op-amp is hitting the rails. The TL072 on 9V can only swing roughly 1.5V to 7.5V — but we only need it to swing around 1.65V within a 3.3V window, so this shouldn't be an issue at unity gain.
- **Noisy signal:** Check decoupling cap placement (should be right next to TL072). Make sure 9V and USB grounds are connected. Keep pickup wires short and away from the Teensy.
