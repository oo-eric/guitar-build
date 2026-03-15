#include "midi_output.h"
#include <math.h>
#include <usb_midi.h>

MidiOutput::MidiOutput(int channel)
    : channel(channel)
    , currentNote(-1)
    , lastPitchBend(0.0f) {
}

void MidiOutput::frequencyToMidi(float frequency, int& noteNumber, float& remainder) {
    float midiNote = 12.0f * log2f(frequency / 440.0f) + 69.0f;
    noteNumber = (int)roundf(midiNote);
    remainder = midiNote - (float)noteNumber;
}

int MidiOutput::amplitudeToVelocity(float amplitude) {
    // Map from actual signal range (~0.08 to ~0.5) to velocity range
    float normalized = (amplitude - ONSET_THRESHOLD) / (0.5f - ONSET_THRESHOLD);
    if (normalized < 0.0f) normalized = 0.0f;
    if (normalized > 1.0f) normalized = 1.0f;
    int velocity = (int)(normalized * (MIDI_VELOCITY_MAX - MIDI_VELOCITY_MIN) + MIDI_VELOCITY_MIN);
    if (velocity < MIDI_VELOCITY_MIN) velocity = MIDI_VELOCITY_MIN;
    if (velocity > MIDI_VELOCITY_MAX) velocity = MIDI_VELOCITY_MAX;
    return velocity;
}

void MidiOutput::sendNoteOn(int noteNumber, int velocity) {
    if (currentNote >= 0) {
        usbMIDI.sendNoteOff(currentNote, 0, channel);
    }

    currentNote = noteNumber;
    lastPitchBend = 0.0f;
    usbMIDI.sendPitchBend(PITCH_BEND_CENTER, channel); // Reset pitch bend before note on
    usbMIDI.sendNoteOn(noteNumber, velocity, channel);
}

void MidiOutput::sendNoteOff() {
    if (currentNote >= 0) {
        usbMIDI.sendNoteOff(currentNote, 0, channel);
        currentNote = -1;
        lastPitchBend = 0.0f;
        // usbMIDI.sendPitchBend(PITCH_BEND_CENTER, channel);
    }
}

void MidiOutput::sendPitchBend(float semitoneOffset) {
    if (fabsf(semitoneOffset - lastPitchBend) < PITCH_BEND_UPDATE_THRESHOLD) {
        return;
    }

    lastPitchBend = semitoneOffset;

    int bendValue = PITCH_BEND_CENTER + (int)(semitoneOffset * ((float)PITCH_BEND_CENTER / (float)PITCH_BEND_RANGE));
    if (bendValue < 0) bendValue = 0;
    if (bendValue > 16383) bendValue = 16383;

    // usbMIDI.sendPitchBend(bendValue, channel);
}
