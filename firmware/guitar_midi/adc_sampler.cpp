#include "adc_sampler.h"

AdcSampler* AdcSampler::instance = nullptr;

void AdcSampler::begin() {
    instance = this;
    writeIndex = 0;
    readIndex = 0;
    sampleCount = 0;

    // Clear buffer
    for (int i = 0; i < RING_BUFFER_SIZE; i++) {
        ringBuffer[i] = 0;
    }

    // Configure ADC
    adc.adc0->setAveraging(ADC_AVERAGING);
    adc.adc0->setResolution(ADC_RESOLUTION);
    adc.adc0->setConversionSpeed(ADC_CONVERSION_SPEED::HIGH_SPEED);
    adc.adc0->setSamplingSpeed(ADC_SAMPLING_SPEED::HIGH_SPEED);

    pinMode(ADC_PIN, INPUT);

    // Start timer-driven sampling
    sampleTimer.begin(timerCallback, ADC_TIMER_PERIOD);
}

void AdcSampler::stop() {
    sampleTimer.end();
}

void AdcSampler::timerCallback() {
    if (instance) {
        int raw = instance->adc.adc0->analogRead(ADC_PIN);
        int16_t sample = (int16_t)(raw - ADC_MID); // Center around zero

        uint32_t idx = instance->writeIndex & RING_BUFFER_MASK;
        instance->ringBuffer[idx] = sample;
        instance->writeIndex++;
        instance->sampleCount++;
    }
}

int AdcSampler::getNewSamples(int16_t* dest, int maxCount) {
    uint32_t currentWrite = writeIndex;
    int available = (int)(currentWrite - readIndex);

    if (available <= 0) return 0;
    if (available > RING_BUFFER_SIZE) {
        // We fell behind — skip to recent data
        readIndex = currentWrite - RING_BUFFER_SIZE;
        available = RING_BUFFER_SIZE;
    }

    int count = (available < maxCount) ? available : maxCount;
    for (int i = 0; i < count; i++) {
        dest[i] = ringBuffer[(readIndex + i) & RING_BUFFER_MASK];
    }
    readIndex += count;
    return count;
}

void AdcSampler::getRecentSamples(int16_t* dest, int count) {
    uint32_t currentWrite = writeIndex;
    uint32_t start = currentWrite - count;

    for (int i = 0; i < count; i++) {
        dest[i] = ringBuffer[(start + i) & RING_BUFFER_MASK];
    }
}
