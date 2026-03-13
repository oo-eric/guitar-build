=== ADC Test ===
Reading A0 every 500ms: avg | min | max | spread
Stage 1 (nothing): floating random values
Stage 2 (bias only): stable ~2048, spread < 50
Stage 3 (full circuit): ~2048 idle, spread grows on pluck
---
avg: 867 | min: 867 | max: 867 | spread: 0
avg: 1936 | min: 1368 | max: 2505 | spread: 1137  << SIGNAL
avg: 2901 | min: 2628 | max: 3175 | spread: 547  << SIGNAL
avg: 2632 | min: 2628 | max: 2637 | spread: 9
avg: 2238 | min: 1972 | max: 2504 | spread: 532  << SIGNAL
avg: 2901 | min: 2628 | max: 3174 | spread: 546  << SIGNAL
avg: 2632 | min: 2628 | max: 2636 | spread: 8
avg: 2240 | min: 1976 | max: 2504 | spread: 528  << SIGNAL
avg: 2901 | min: 2628 | max: 3174 | spread: 546  << SIGNAL
avg: 2632 | min: 2628 | max: 2636 | spread: 8
avg: 2241 | min: 1979 | max: 2504 | spread: 525  << SIGNAL
avg: 2901 | min: 2628 | max: 3174 | spread: 546  << SIGNAL