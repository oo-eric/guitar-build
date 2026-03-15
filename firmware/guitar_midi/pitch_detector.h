#pragma once

#include <Arduino.h>
#include "config.h"

struct PitchResult {
    float frequency;    // Hz, or -1.0 if no pitch detected
    float probability;  // 0.0-1.0 confidence
};

class PitchDetector {
public:
    PitchDetector();

    PitchResult detect(const int16_t* samples, int count);

    // Hysteresis: returns true if the new note should replace the current one
    bool shouldSwitchNote(float newFreq, int currentNote);

private:
    float yinBuffer[YIN_BUFFER_SIZE / 2];

    void differenceFunction(const int16_t* samples, int count);
    void cumulativeMeanNormalizedDifference();
    int absoluteThreshold();
    float parabolicInterpolation(int tauEstimate);
};
