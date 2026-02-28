#include "midi_output.h"
#include <math.h>

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
    // Map amplitude (0.0-1.0) to velocity range
    int velocity = (int)(amplitude * (MIDI_VELOCITY_MAX - MIDI_VELOCITY_MIN) + MIDI_VELOCITY_MIN);
    if (velocity < MIDI_VELOCITY_MIN) velocity = MIDI_VELOCITY_MIN;
    if (velocity > MIDI_VELOCITY_MAX) velocity = MIDI_VELOCITY_MAX;
    return velocity;
}

void MidiOutput::sendNoteOn(int noteNumber, int velocity) {
    // If a note is already active, send note-off first
    if (currentNote >= 0) {
        usbMIDI.sendNoteOff(currentNote, 0, channel);
    }

    currentNote = noteNumber;
    lastPitchBend = 0.0f;
    usbMIDI.sendNoteOn(noteNumber, velocity, channel);
}

void MidiOutput::sendNoteOff() {
    if (currentNote >= 0) {
        usbMIDI.sendNoteOff(currentNote, 0, channel);
        currentNote = -1;
        lastPitchBend = 0.0f;
        // Reset pitch bend to center
        usbMIDI.sendPitchBend(PITCH_BEND_CENTER, channel);
    }
}

void MidiOutput::sendPitchBend(float semitoneOffset) {
    // Skip if change is too small
    if (fabsf(semitoneOffset - lastPitchBend) < PITCH_BEND_UPDATE_THRESHOLD) {
        return;
    }

    lastPitchBend = semitoneOffset;

    // Convert semitone offset to 14-bit pitch bend value (0-16383, center=8192)
    int bendValue = PITCH_BEND_CENTER + (int)(semitoneOffset * ((float)PITCH_BEND_CENTER / (float)PITCH_BEND_RANGE));
    if (bendValue < 0) bendValue = 0;
    if (bendValue > 16383) bendValue = 16383;

    usbMIDI.sendPitchBend(bendValue, channel);
}

void MidiOutput::update() {
    // Read and discard incoming MIDI to keep USB stack healthy
    while (usbMIDI.read()) {}
}
