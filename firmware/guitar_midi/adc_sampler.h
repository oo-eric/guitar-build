#pragma once

#include <ADC.h>
#include <IntervalTimer.h>
#include "config.h"

class AdcSampler {
public:
    void begin();
    void stop();

    // Returns number of new samples copied into dest (for onset detector)
    int getNewSamples(int16_t* dest, int maxCount);

    // Copies the most recent 'count' samples into dest, oldest first (for pitch detector)
    void getRecentSamples(int16_t* dest, int count);

    volatile uint32_t sampleCount; // Total samples taken (for debug)

private:
    static void timerCallback();
    static AdcSampler* instance;

    ADC adc;
    IntervalTimer sampleTimer;
    volatile int16_t ringBuffer[RING_BUFFER_SIZE];
    volatile uint32_t writeIndex;
    uint32_t readIndex;
};
