#pragma once

// Per-string diagnostics over USB MIDI SysEx, for the HexScope app (app/HexScope).
//
// Why SysEx and not Serial: iOS gives apps no access to a USB CDC serial port,
// but it does expose class-compliant USB MIDI through CoreMIDI. Running the
// diagnostics over the MIDI interface means one firmware build talks to the
// iPhone, iPad and Mac identically, and the Serial debug output is untouched.
//
// Every message is  F0 7D 47 <version> <type> <payload...> F7
//   7D = non-commercial manufacturer ID, 47 = 'G'.
// All multi-byte values are 7-bit groups, most significant first.
// The app's decoder lives in app/HexScope/Shared/Telemetry.swift — change both
// together and bump TELEMETRY_VERSION.

#include <Arduino.h>
#include "config.h"
#include "adc_sampler.h"
#include "onset_detector.h"
#include "pitch_detector.h"

constexpr uint8_t TELEMETRY_VERSION = 1;

enum TelemetryType : uint8_t
{
    TELEM_STATUS = 0x01, // every TELEMETRY_PERIOD_MS: per-string levels, bias, pitch
    TELEM_SCOPE = 0x02,  // one string's recent waveform, round-robin
    TELEM_CONFIG = 0x03, // thresholds and rates, every TELEMETRY_CONFIG_MS
};

class Telemetry
{
public:
    // Call after every pitch detection so the status frame carries the latest result.
    void notePitch(int string, const PitchResult &result);

    // Sends whatever is due. Cheap when nothing is.
    void update(AdcSampler &sampler, const OnsetDetector *onset, const int *activeNote);

private:
    void sendStatus(AdcSampler &sampler, const OnsetDetector *onset, const int *activeNote);
    void sendScope(AdcSampler &sampler, int string);
    void sendConfig();

    float lastFreq[NUM_STRINGS] = {};
    float lastProb[NUM_STRINGS] = {};
    int scopeString = 0;
    elapsedMillis statusTimer;
    elapsedMillis configTimer = TELEMETRY_CONFIG_MS; // send config immediately
};
