#pragma once

#include <Arduino.h>
#include "config.h"

class MidiOutput {
public:
    MidiOutput(int channel = MPE_CHANNELS[0]);

    void sendNoteOn(int noteNumber, int velocity);
    void sendNoteOff();
    void sendPitchBend(float semitoneOffset);

    int getCurrentNote() const { return currentNote; }
    bool isNoteActive() const { return currentNote >= 0; }

    static int amplitudeToVelocity(float amplitude);
    static void frequencyToMidi(float frequency, int& noteNumber, float& remainder);

private:
    int channel;
    int currentNote;
    float lastPitchBend;
};
