#pragma once

#include <Arduino.h>

// --- Strings ---
// Index 0 = string 1 = high E (GK pin 1 -> J1 -> A0). See docs/plan.md "13-Pin Interface".
constexpr int NUM_STRINGS = 6;
constexpr int STRING_PINS[NUM_STRINGS] = {A0, A1, A2, A3, A4, A5};
constexpr int MPE_CHANNELS[NUM_STRINGS] = {2, 3, 4, 5, 6, 7};

// --- ADC ---
constexpr int ADC_RESOLUTION = 12;          // 12-bit (0-4095)
constexpr float ADC_SAMPLE_RATE = 20000.0f; // 20 kHz per string
constexpr uint32_t ADC_TIMER_PERIOD = 50;   // microseconds (1,000,000 / 20000)
constexpr int ADC_AVERAGING = 4;            // Hardware averaging for noise reduction
constexpr int ADC_MID = 2048;               // DC bias midpoint for 12-bit

// --- Ring buffer (per string) ---
constexpr int RING_BUFFER_SIZE = 1024; // Power of 2, ~51ms at 20kHz
constexpr int RING_BUFFER_MASK = RING_BUFFER_SIZE - 1;

// --- Pitch detection (YIN) ---
constexpr int YIN_BUFFER_SIZE = 512;                                // Analysis window (~25.6ms at 20kHz)
constexpr float YIN_THRESHOLD = 0.25f;                              // Aperiodicity threshold (lower = stricter)
constexpr float MIN_FREQUENCY = 75.0f;                              // Below low E (82Hz) with margin
constexpr float MAX_FREQUENCY = 1400.0f;                            // Above high E 24th fret (~1319Hz)
constexpr int YIN_TAU_MIN = (int)(ADC_SAMPLE_RATE / MAX_FREQUENCY); // ~14
constexpr int YIN_TAU_MAX = (int)(ADC_SAMPLE_RATE / MIN_FREQUENCY); // ~267

// --- Onset / offset detection ---
constexpr float ONSET_THRESHOLD = 0.03f;    // RMS threshold for note-on (MCP6002 @ 3.3V: idle ~0.014, plucks ~0.05)
constexpr float OFFSET_THRESHOLD = 0.018f;  // RMS threshold for note-off (just above idle floor)
constexpr int ONSET_WINDOW = 256;           // Samples per RMS calculation (~12.8ms, covers full waveform cycle)
constexpr uint32_t OFFSET_HOLD_MS = 80;     // Min note duration before allowing note-off
constexpr uint32_t RETRIGGER_BLOCK_MS = 200; // Min time between note-on events (prevents false re-trigger after decay)
constexpr uint32_t PITCH_TIMEOUT_MS = 200;  // Max wait for valid pitch after onset
constexpr uint32_t PITCH_DELAY_MS = 20;     // Wait before first pitch detection after onset

// --- MIDI ---
constexpr int MIDI_VELOCITY_MIN = 20;
constexpr int MIDI_VELOCITY_MAX = 127;
constexpr int PITCH_BEND_RANGE = 2;                  // Semitones (must match DAW MPE config)
constexpr int PITCH_BEND_CENTER = 8192;              // 14-bit center value
constexpr float PITCH_BEND_UPDATE_THRESHOLD = 0.02f; // Min semitone change to send update

// --- Pitch hysteresis ---
constexpr float HYSTERESIS_MIN_SEMITONES = 0.6f; // Ignore wobbles smaller than this
constexpr float HYSTERESIS_MAX_SEMITONES = 7.0f; // Reject jumps larger than this

// --- Timing ---
constexpr uint32_t PITCH_STAGGER_US = 5000; // Run pitch detection every 5ms (one string at a time)

// --- Telemetry (USB MIDI SysEx -> HexScope app, see telemetry.h) ---
constexpr bool TELEMETRY_ENABLED = true;
constexpr uint32_t TELEMETRY_PERIOD_MS = 50;  // status frame rate (20 Hz)
constexpr uint32_t TELEMETRY_CONFIG_MS = 1000; // thresholds re-sent so a late-connecting app picks them up
constexpr int TELEMETRY_SCOPE_POINTS = 128;
constexpr int TELEMETRY_SCOPE_DECIMATE = 2;    // 128 points x 2 = 256 samples = 12.8ms, ~1 cycle of low E
constexpr int TELEMETRY_SCOPES_PER_TICK = 2;   // each string's scope refreshes every 150ms

// --- Debug ---
constexpr bool DEBUG_SERIAL = true;
constexpr uint32_t DEBUG_PRINT_MS = 100;
