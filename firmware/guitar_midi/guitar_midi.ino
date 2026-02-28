#include "config.h"
#include "adc_sampler.h"
#include "onset_detector.h"
#include "pitch_detector.h"
#include "midi_output.h"

AdcSampler    sampler;
OnsetDetector onset;
PitchDetector pitch;
MidiOutput    midi;

elapsedMicros pitchTimer;
elapsedMillis debugTimer;

int16_t pitchBuffer[YIN_BUFFER_SIZE];
int16_t onsetBuffer[ONSET_WINDOW];

int   activeNote     = -1;
float activeRemainder = 0.0f;

void setup() {
    if (DEBUG_SERIAL) {
        Serial.begin(115200);
        while (!Serial && millis() < 3000) {} // Wait up to 3s for serial monitor
        Serial.println("Guitar MIDI - Phase 1");
        Serial.println("=====================");
    }

    sampler.begin();

    if (DEBUG_SERIAL) {
        Serial.println("ADC sampling started at 20kHz");
    }
}

void loop() {
    // --- 1. Feed new samples to onset detector ---
    int count = sampler.getNewSamples(onsetBuffer, ONSET_WINDOW);
    if (count > 0) {
        OnsetEvent onEvent = onset.processSamples(onsetBuffer, count);

        if (onEvent.triggered && DEBUG_SERIAL) {
            Serial.print("ONSET detected, amplitude: ");
            Serial.println(onEvent.attackAmplitude, 4);
        }
    }

    // --- 2. Run pitch detection periodically ---
    if (pitchTimer >= PITCH_UPDATE_US) {
        pitchTimer = 0;
        NoteState state = onset.getState();

        if (state == NoteState::ATTACK || state == NoteState::SUSTAIN) {
            sampler.getRecentSamples(pitchBuffer, YIN_BUFFER_SIZE);
            PitchResult result = pitch.detect(pitchBuffer, YIN_BUFFER_SIZE);

            if (result.frequency > 0 && result.probability > 0.80f) {
                int noteNum;
                float remainder;
                MidiOutput::frequencyToMidi(result.frequency, noteNum, remainder);

                if (state == NoteState::ATTACK) {
                    // First valid pitch after onset — send note on
                    int velocity = MidiOutput::amplitudeToVelocity(onset.getAttackAmplitude());
                    midi.sendPitchBend(remainder);
                    midi.sendNoteOn(noteNum, velocity);
                    onset.confirmPitch();
                    activeNote = noteNum;
                    activeRemainder = remainder;

                    if (DEBUG_SERIAL) {
                        Serial.print("NOTE ON: ");
                        Serial.print(noteNum);
                        Serial.print(" vel=");
                        Serial.print(velocity);
                        Serial.print(" freq=");
                        Serial.print(result.frequency, 1);
                        Serial.print("Hz prob=");
                        Serial.println(result.probability, 2);
                    }
                } else {
                    // Sustain — update pitch bend for string bends
                    // Calculate bend relative to the original note
                    float currentMidiNote = 12.0f * log2f(result.frequency / 440.0f) + 69.0f;
                    float bendFromOriginal = currentMidiNote - (float)activeNote;
                    midi.sendPitchBend(bendFromOriginal);
                }
            }
        }
    }

    // --- 3. Check for note-off ---
    OffsetEvent offEvent = onset.checkOffset();
    if (offEvent.triggered) {
        if (DEBUG_SERIAL) {
            Serial.print("NOTE OFF: ");
            Serial.println(activeNote);
        }
        midi.sendNoteOff();
        onset.reset();
        activeNote = -1;
    }

    // --- 4. Service USB MIDI ---
    midi.update();

    // --- 5. Debug output ---
    if (DEBUG_SERIAL && debugTimer >= DEBUG_PRINT_MS) {
        debugTimer = 0;
        // Uncomment for continuous monitoring:
        // Serial.print("RMS: ");
        // Serial.print(currentRMS, 4);
        // Serial.print(" state: ");
        // Serial.println((int)onset.getState());
    }
}
