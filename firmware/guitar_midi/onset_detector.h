#pragma once

#include <Arduino.h>
#include "config.h"

enum class NoteState
{
    IDLE,
    ATTACK,
    SUSTAIN,
    RELEASING
};

struct OnsetEvent
{
    bool triggered;
    float attackAmplitude;
};

struct OffsetEvent
{
    bool triggered;
};

class OnsetDetector
{
public:
    OnsetDetector();

    OnsetEvent processSamples(const int16_t *samples, int count);
    OffsetEvent checkOffset();

    NoteState getState() const { return state; }
    float getAttackAmplitude() const { return peakAmplitude; }
    float getCurrentRMS() const { return currentRMS; }
    uint32_t getNoteOnTime() const { return noteOnTime; }

    void confirmPitch();
    void reset();

private:
    float computeRMS(const int16_t *samples, int count);

    NoteState state;
    float currentRMS;
    float peakAmplitude;
    uint32_t noteOnTime;
    uint32_t lastOnsetTime;
    uint32_t releaseStartTime;
};
