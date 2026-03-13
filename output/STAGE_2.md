=== ADC Test ===
Reading A0 every 500ms: avg | min | max | spread
Stage 1 (nothing): floating random values
Stage 2 (bias only): stable ~2048, spread < 50
Stage 3 (full circuit): ~2048 idle, spread grows on pluck
---
avg: 2050 | min: 2050 | max: 2050 | spread: 0
avg: 2048 | min: 2042 | max: 2054 | spread: 12
avg: 2048 | min: 2042 | max: 2055 | spread: 13
avg: 2047 | min: 2041 | max: 2054 | spread: 13
avg: 2047 | min: 2041 | max: 2054 | spread: 13