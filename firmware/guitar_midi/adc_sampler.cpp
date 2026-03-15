#include "adc_sampler.h"

AdcSampler* AdcSampler::instance = nullptr;

void AdcSampler::begin() {
    instance = this;
    sampleCount = 0;

    for (int s = 0; s < NUM_STRINGS; s++) {
        writeIndex[s] = 0;
        readIndex[s] = 0;
        for (int i = 0; i < RING_BUFFER_SIZE; i++) {
            ringBuffer[s][i] = 0;
        }
        pinMode(STRING_PINS[s], INPUT);
    }

    // Configure ADC0 (ADC1 on Teensy 4.0)
    adc.adc0->setAveraging(ADC_AVERAGING);
    adc.adc0->setResolution(ADC_RESOLUTION);
    adc.adc0->setConversionSpeed(ADC_CONVERSION_SPEED::HIGH_SPEED);
    adc.adc0->setSamplingSpeed(ADC_SAMPLING_SPEED::HIGH_SPEED);

    // Start timer-driven sampling
    sampleTimer.begin(timerCallback, ADC_TIMER_PERIOD);
}

void AdcSampler::stop() {
    sampleTimer.end();
}

void AdcSampler::timerCallback() {
    if (!instance) return;

    // Read all 6 strings sequentially (~2.5µs each, ~15µs total)
    for (int s = 0; s < NUM_STRINGS; s++) {
        int raw = instance->adc.adc0->analogRead(STRING_PINS[s]);
        int16_t sample = (int16_t)(raw - ADC_MID);

        uint32_t idx = instance->writeIndex[s] & RING_BUFFER_MASK;
        instance->ringBuffer[s][idx] = sample;
        instance->writeIndex[s]++;
    }
    instance->sampleCount++;
}

int AdcSampler::getNewSamples(int string, int16_t* dest, int maxCount) {
    uint32_t currentWrite = writeIndex[string];
    int available = (int)(currentWrite - readIndex[string]);

    if (available <= 0) return 0;
    if (available > RING_BUFFER_SIZE) {
        // We fell behind — skip to recent data
        readIndex[string] = currentWrite - RING_BUFFER_SIZE;
        available = RING_BUFFER_SIZE;
    }

    int count = (available < maxCount) ? available : maxCount;
    for (int i = 0; i < count; i++) {
        dest[i] = ringBuffer[string][(readIndex[string] + i) & RING_BUFFER_MASK];
    }
    readIndex[string] += count;
    return count;
}

void AdcSampler::getRecentSamples(int string, int16_t* dest, int count) {
    uint32_t currentWrite = writeIndex[string];
    uint32_t start = currentWrite - count;

    for (int i = 0; i < count; i++) {
        dest[i] = ringBuffer[string][(start + i) & RING_BUFFER_MASK];
    }
}
