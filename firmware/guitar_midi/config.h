#pragma once

#include <Arduino.h>

// --- ADC ---
constexpr int      ADC_PIN            = A0;
constexpr int      ADC_RESOLUTION     = 12;       // 12-bit (0-4095)
constexpr float    ADC_SAMPLE_RATE    = 20000.0f; // 20 kHz
constexpr uint32_t ADC_TIMER_PERIOD   = 50;       // microseconds (1,000,000 / 20000)
constexpr int      ADC_AVERAGING      = 4;        // Hardware averaging for noise reduction
constexpr int      ADC_MID            = 2048;     // DC bias midpoint for 12-bit

// --- Ring buffer ---
constexpr int      RING_BUFFER_SIZE   = 1024;     // Power of 2, ~51ms at 20kHz
constexpr int      RING_BUFFER_MASK   = RING_BUFFER_SIZE - 1;

// --- Pitch detection (YIN) ---
constexpr int      YIN_BUFFER_SIZE    = 512;      // Analysis window (~25.6ms at 20kHz)
constexpr float    YIN_THRESHOLD      = 0.15f;    // Aperiodicity threshold (lower = stricter)
constexpr float    MIN_FREQUENCY      = 75.0f;    // Below low E (82Hz) with margin
constexpr float    MAX_FREQUENCY      = 1400.0f;  // Above high E 24th fret (~1319Hz)
constexpr int      YIN_TAU_MIN        = (int)(ADC_SAMPLE_RATE / MAX_FREQUENCY); // ~14
constexpr int      YIN_TAU_MAX        = (int)(ADC_SAMPLE_RATE / MIN_FREQUENCY); // ~267

// --- Onset / offset detection ---
constexpr float    ONSET_THRESHOLD    = 0.25f;    // RMS threshold for note-on (tune with real signal)
constexpr float    OFFSET_THRESHOLD   = 0.01f;    // RMS threshold for note-off
constexpr int      ONSET_WINDOW       = 64;       // Samples per RMS calculation
constexpr uint32_t OFFSET_HOLD_MS     = 80;       // Min note duration before allowing note-off
constexpr uint32_t RETRIGGER_BLOCK_MS = 30;       // Min time between note-on events
constexpr uint32_t PITCH_TIMEOUT_MS   = 50;       // Max wait for valid pitch after onset

// --- MIDI ---
constexpr int      MPE_CHANNEL        = 2;        // String 1 = channel 2 (MPE master = ch 1)
constexpr int      MIDI_VELOCITY_MIN  = 20;
constexpr int      MIDI_VELOCITY_MAX  = 127;
constexpr int      PITCH_BEND_RANGE   = 2;        // Semitones (must match DAW MPE config)
constexpr int      PITCH_BEND_CENTER  = 8192;     // 14-bit center value
constexpr float    PITCH_BEND_UPDATE_THRESHOLD = 0.02f; // Min semitone change to send update

// --- Timing ---
constexpr uint32_t PITCH_UPDATE_US    = 5000;     // Run pitch detection every 5ms

// --- Debug ---
constexpr bool     DEBUG_SERIAL       = true;     // Enable serial debug output
constexpr uint32_t DEBUG_PRINT_MS     = 100;      // Throttle debug prints
