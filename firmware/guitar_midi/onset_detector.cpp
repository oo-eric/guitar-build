#include "onset_detector.h"

OnsetDetector::OnsetDetector()
    : state(NoteState::IDLE), currentRMS(0.0f), peakAmplitude(0.0f), noteOnTime(0), lastOnsetTime(0), releaseStartTime(0)
{
}

float OnsetDetector::computeRMS(const int16_t *samples, int count)
{
    float sum = 0.0f;
    for (int i = 0; i < count; i++)
    {
        float s = samples[i] / 2048.0f; // Normalize to roughly -1.0..+1.0
        sum += s * s;
    }
    return sqrtf(sum / count);
}

OnsetEvent OnsetDetector::processSamples(const int16_t *samples, int count)
{
    OnsetEvent event = {false, 0.0f};
    currentRMS = computeRMS(samples, count);

    if (state == NoteState::ATTACK)
    {
        for (int i = 0; i < count; i++)
        {
            float absVal = fabsf(samples[i] / 2048.0f);
            if (absVal > peakAmplitude)
            {
                peakAmplitude = absVal;
            }
        }
    }

    switch (state)
    {
    case NoteState::IDLE:
        if (currentRMS > ONSET_THRESHOLD)
        {
            uint32_t now = millis();
            if (now - lastOnsetTime >= RETRIGGER_BLOCK_MS)
            {
                state = NoteState::ATTACK;
                noteOnTime = now;
                lastOnsetTime = now;
                peakAmplitude = currentRMS;
                event.triggered = true;
                event.attackAmplitude = currentRMS;
            }
        }
        break;

    case NoteState::SUSTAIN:
        if (currentRMS < OFFSET_THRESHOLD)
        {
            state = NoteState::RELEASING;
            releaseStartTime = millis();
        }
        break;

    case NoteState::RELEASING:
        if (currentRMS > ONSET_THRESHOLD)
        {
            state = NoteState::SUSTAIN;
        }
        break;

    default:
        break;
    }

    return event;
}

void OnsetDetector::confirmPitch()
{
    if (state == NoteState::ATTACK)
    {
        state = NoteState::SUSTAIN;
    }
}

OffsetEvent OnsetDetector::checkOffset()
{
    OffsetEvent event = {false};

    if (state == NoteState::RELEASING)
    {
        uint32_t elapsed = millis() - releaseStartTime;
        if (elapsed >= OFFSET_HOLD_MS && currentRMS < OFFSET_THRESHOLD)
        {
            event.triggered = true;
        }
    }

    if (state == NoteState::ATTACK)
    {
        uint32_t elapsed = millis() - noteOnTime;
        if (elapsed >= PITCH_TIMEOUT_MS)
        {
            state = NoteState::IDLE;
        }
    }

    return event;
}

void OnsetDetector::reset()
{
    state = NoteState::IDLE;
    currentRMS = 0.0f;
    peakAmplitude = 0.0f;
}
