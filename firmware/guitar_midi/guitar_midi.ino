// 6-String MIDI Guitar — MPE pitch-to-MIDI
// Arduino IDE USB Type: "Serial + MIDI"
//
// Each string has its own ADC input, onset detector, pitch detector,
// and MIDI channel (MPE channels 2-7). Pitch detection is staggered
// across strings to balance CPU load.

#include "config.h"
#include "adc_sampler.h"
#include "onset_detector.h"
#include "pitch_detector.h"
#include "midi_output.h"

AdcSampler sampler;
OnsetDetector onset[NUM_STRINGS];
PitchDetector pitch[NUM_STRINGS];
MidiOutput midi[NUM_STRINGS] = {
    MidiOutput(MPE_CHANNELS[0]),
    // MidiOutput(MPE_CHANNELS[1]),
    // MidiOutput(MPE_CHANNELS[2]),
    // MidiOutput(MPE_CHANNELS[3]),
    // MidiOutput(MPE_CHANNELS[4]),
    // MidiOutput(MPE_CHANNELS[5])
};

// Shared buffers — only one string processed at a time
int16_t pitchBuffer[YIN_BUFFER_SIZE];
int16_t onsetBuffer[ONSET_WINDOW];

// Per-string state
int activeNote[NUM_STRINGS];

// Staggered pitch detection
int pitchStringIndex = 0;
elapsedMicros pitchTimer;

// Debug
elapsedMillis debugTimer;

const char *NOTE_NAMES[] = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};
const char *STRING_NAMES[] = {"E2", "A2", "D3", "G3", "B3", "E4"};

void setup()
{
    if (DEBUG_SERIAL)
    {
        Serial.begin(115200);
        while (!Serial && millis() < 3000)
        {
        }
        Serial.println("Guitar MIDI — Phase 2 (6 strings)");
        Serial.println("==================================");
    }

    for (int s = 0; s < NUM_STRINGS; s++)
    {
        activeNote[s] = -1;
    }

    sampler.begin();

    if (DEBUG_SERIAL)
    {
        Serial.print("ADC sampling ");
        Serial.print(NUM_STRINGS);
        Serial.print(" strings at ");
        Serial.print((int)ADC_SAMPLE_RATE);
        Serial.println(" Hz each");
    }
}

void loop()
{
    // --- 1. Onset detection — all strings, every loop ---
    for (int s = 0; s < NUM_STRINGS; s++)
    {
        int count = sampler.getNewSamples(s, onsetBuffer, ONSET_WINDOW);
        if (count > 0)
        {
            OnsetEvent onEvent = onset[s].processSamples(onsetBuffer, count);

            if (onEvent.triggered && DEBUG_SERIAL)
            {
                Serial.print("[");
                Serial.print(STRING_NAMES[s]);
                Serial.print("] ONSET amp=");
                Serial.println(onEvent.attackAmplitude, 4);
            }
        }
    }

    // --- 2. Pitch detection — one string per tick (staggered) ---
    if (pitchTimer >= PITCH_STAGGER_US)
    {
        pitchTimer = 0;

        int s = pitchStringIndex;
        NoteState state = onset[s].getState();

        if (state == NoteState::ATTACK || state == NoteState::SUSTAIN)
        {
            sampler.getRecentSamples(s, pitchBuffer, YIN_BUFFER_SIZE);
            PitchResult result = pitch[s].detect(pitchBuffer, YIN_BUFFER_SIZE);

            if (result.frequency > 0 && result.probability > 0.80f)
            {
                int noteNum;
                float remainder;
                MidiOutput::frequencyToMidi(result.frequency, noteNum, remainder);

                if (state == NoteState::ATTACK)
                {
                    // First valid pitch after onset — send note on
                    int velocity = MidiOutput::amplitudeToVelocity(onset[s].getAttackAmplitude());
                    midi[s].sendPitchBend(remainder);
                    midi[s].sendNoteOn(noteNum, velocity);
                    onset[s].confirmPitch();
                    activeNote[s] = noteNum;

                    if (DEBUG_SERIAL)
                    {
                        int noteIndex = noteNum % 12;
                        int octave = (noteNum / 12) - 1;
                        Serial.print("[");
                        Serial.print(STRING_NAMES[s]);
                        Serial.print("] NOTE ON: ");
                        Serial.print(NOTE_NAMES[noteIndex]);
                        Serial.print(octave);
                        Serial.print(" (MIDI ");
                        Serial.print(noteNum);
                        Serial.print(") vel=");
                        Serial.print(velocity);
                        Serial.print(" freq=");
                        Serial.print(result.frequency, 1);
                        Serial.print("Hz ch=");
                        Serial.println(MPE_CHANNELS[s]);
                    }
                }
                else if (state == NoteState::SUSTAIN && activeNote[s] >= 0)
                {
                    // Sustain — check for note change or pitch bend
                    if (pitch[s].shouldSwitchNote(result.frequency, activeNote[s]))
                    {
                        // Frequency moved to a clearly different note
                        int velocity = MidiOutput::amplitudeToVelocity(onset[s].getAttackAmplitude());
                        midi[s].sendNoteOff();
                        midi[s].sendPitchBend(remainder);
                        midi[s].sendNoteOn(noteNum, velocity);
                        activeNote[s] = noteNum;

                        if (DEBUG_SERIAL)
                        {
                            Serial.print("[");
                            Serial.print(STRING_NAMES[s]);
                            Serial.print("] NOTE CHANGE: MIDI ");
                            Serial.println(noteNum);
                        }
                    }
                    else
                    {
                        // Small pitch variation — send as pitch bend
                        float currentMidiNote = 12.0f * log2f(result.frequency / 440.0f) + 69.0f;
                        float bendFromOriginal = currentMidiNote - (float)activeNote[s];
                        midi[s].sendPitchBend(bendFromOriginal);
                    }
                }
            }
        }

        pitchStringIndex = (pitchStringIndex + 1) % NUM_STRINGS;
    }

    // --- 3. Note-off — all strings, every loop ---
    for (int s = 0; s < NUM_STRINGS; s++)
    {
        OffsetEvent offEvent = onset[s].checkOffset();
        if (offEvent.triggered)
        {
            if (DEBUG_SERIAL)
            {
                Serial.print("[");
                Serial.print(STRING_NAMES[s]);
                Serial.print("] NOTE OFF: MIDI ");
                Serial.println(activeNote[s]);
            }
            midi[s].sendNoteOff();
            onset[s].reset();
            activeNote[s] = -1;
        }
    }

    // --- 4. Debug: print RMS for string 0 ---
    if (DEBUG_SERIAL && debugTimer >= DEBUG_PRINT_MS)
    {
        debugTimer = 0;
        for (int s = 0; s < NUM_STRINGS; s++)
        {
            if (onset[s].getState() != NoteState::IDLE)
            {
                Serial.print("[");
                Serial.print(STRING_NAMES[s]);
                Serial.print("] state=");
                Serial.print((int)onset[s].getState());
            }
            Serial.print(" rms=");
            Serial.println(onset[s].getCurrentRMS(), 4);
        }
    }

    // --- 5. Service USB MIDI ---
    while (usbMIDI.read())
    {
    }
}
