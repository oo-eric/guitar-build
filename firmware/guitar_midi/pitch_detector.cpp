#include "pitch_detector.h"
#include <math.h>

PitchDetector::PitchDetector() {
    for (int i = 0; i < YIN_BUFFER_SIZE / 2; i++) {
        yinBuffer[i] = 0.0f;
    }
}

PitchResult PitchDetector::detect(const int16_t* samples, int count) {
    PitchResult result = { -1.0f, 0.0f };

    if (count < YIN_BUFFER_SIZE) return result;

    // Step 1: Difference function
    differenceFunction(samples, count);

    // Step 2: Cumulative mean normalized difference
    cumulativeMeanNormalizedDifference();

    // Step 3: Absolute threshold — find the best tau
    int tau = absoluteThreshold();
    if (tau < 0) return result; // No pitch found

    // Step 4: Parabolic interpolation for sub-sample accuracy
    float tauRefined = parabolicInterpolation(tau);

    // Step 5: Convert to frequency
    result.frequency = ADC_SAMPLE_RATE / tauRefined;
    result.probability = 1.0f - yinBuffer[tau];

    // Sanity check
    if (result.frequency < MIN_FREQUENCY || result.frequency > MAX_FREQUENCY) {
        result.frequency = -1.0f;
        result.probability = 0.0f;
    }

    return result;
}

void PitchDetector::differenceFunction(const int16_t* samples, int count) {
    int halfWindow = YIN_BUFFER_SIZE / 2;

    yinBuffer[0] = 0.0f;

    for (int tau = 1; tau < halfWindow; tau++) {
        float sum = 0.0f;
        for (int j = 0; j < halfWindow; j++) {
            float diff = (float)(samples[j] - samples[j + tau]);
            sum += diff * diff;
        }
        yinBuffer[tau] = sum;
    }
}

void PitchDetector::cumulativeMeanNormalizedDifference() {
    int halfWindow = YIN_BUFFER_SIZE / 2;

    yinBuffer[0] = 1.0f; // Defined as 1
    float runningSum = 0.0f;

    for (int tau = 1; tau < halfWindow; tau++) {
        runningSum += yinBuffer[tau];
        yinBuffer[tau] = yinBuffer[tau] * tau / runningSum;
    }
}

int PitchDetector::absoluteThreshold() {
    int halfWindow = YIN_BUFFER_SIZE / 2;
    int bestTau = -1;
    float bestVal = YIN_THRESHOLD;

    // Search within the valid tau range for our frequency bounds
    int tauMin = (YIN_TAU_MIN > 1) ? YIN_TAU_MIN : 1;
    int tauMax = (YIN_TAU_MAX < halfWindow) ? YIN_TAU_MAX : halfWindow - 1;

    for (int tau = tauMin; tau < tauMax; tau++) {
        if (yinBuffer[tau] < YIN_THRESHOLD) {
            // Find the local minimum in this dip
            while (tau + 1 < tauMax && yinBuffer[tau + 1] < yinBuffer[tau]) {
                tau++;
            }
            return tau;
        }
    }

    // No value below threshold — no pitch detected
    return -1;
}

float PitchDetector::parabolicInterpolation(int tauEstimate) {
    int halfWindow = YIN_BUFFER_SIZE / 2;

    if (tauEstimate <= 0 || tauEstimate >= halfWindow - 1) {
        return (float)tauEstimate;
    }

    float s0 = yinBuffer[tauEstimate - 1];
    float s1 = yinBuffer[tauEstimate];
    float s2 = yinBuffer[tauEstimate + 1];

    float denominator = 2.0f * (2.0f * s1 - s0 - s2);
    if (fabsf(denominator) < 1e-10f) {
        return (float)tauEstimate;
    }

    float adjustment = (s0 - s2) / denominator;
    return (float)tauEstimate + adjustment;
}
