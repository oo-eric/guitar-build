#pragma once

#include <ADC.h>
#include <IntervalTimer.h>
#include "config.h"

class AdcSampler {
public:
    void begin();
    void stop();

    // Returns number of new samples copied into dest for a given string
    int getNewSamples(int string, int16_t* dest, int maxCount);

    // Copies the most recent 'count' samples into dest, oldest first
    void getRecentSamples(int string, int16_t* dest, int count);

    volatile uint32_t sampleCount; // Total timer ticks (for debug)

private:
    static void timerCallback();
    static AdcSampler* instance;

    ADC adc;
    IntervalTimer sampleTimer;

    // Per-string ring buffers
    volatile int16_t ringBuffer[NUM_STRINGS][RING_BUFFER_SIZE];
    volatile uint32_t writeIndex[NUM_STRINGS];
    uint32_t readIndex[NUM_STRINGS];
};
