#pragma once

#include <Arduino.h>
#include "config.h"

class MidiOutput {
public:
    MidiOutput(int channel = MPE_CHANNEL);

    void sendNoteOn(int noteNumber, int velocity);
    void sendNoteOff();
    void sendPitchBend(float semitoneOffset);

    int getCurrentNote() const { return currentNote; }
    bool isNoteActive() const { return currentNote >= 0; }

    // Map amplitude to MIDI velocity
    static int amplitudeToVelocity(float amplitude);

    // Convert frequency to MIDI note number and fractional remainder
    static void frequencyToMidi(float frequency, int& noteNumber, float& remainder);

    // Call in loop() to service USB MIDI
    void update();

private:
    int channel;
    int currentNote;
    float lastPitchBend;
};
