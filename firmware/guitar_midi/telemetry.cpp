#include "telemetry.h"
#include <usb_midi.h>

namespace
{
    // Analysis window for the bias/level stats. The whole ring buffer (~51ms)
    // covers several cycles of low E, so the mean is a real DC estimate.
    constexpr int STATS_WINDOW = RING_BUFFER_SIZE;
    int16_t statsBuffer[STATS_WINDOW];

    constexpr int MAX_MSG = 8 + NUM_STRINGS * 16 + TELEMETRY_SCOPE_POINTS * 2;
    uint8_t msg[MAX_MSG];
    int msgLen = 0;

    void begin(TelemetryType type)
    {
        msgLen = 0;
        msg[msgLen++] = 0x7D;
        msg[msgLen++] = 0x47;
        msg[msgLen++] = TELEMETRY_VERSION;
        msg[msgLen++] = type;
    }

    void put7(int v)
    {
        msg[msgLen++] = (uint8_t)(constrain(v, 0, 0x7F));
    }

    void put14(int v)
    {
        v = constrain(v, 0, 0x3FFF);
        msg[msgLen++] = (uint8_t)((v >> 7) & 0x7F);
        msg[msgLen++] = (uint8_t)(v & 0x7F);
    }

    void put28(uint32_t v)
    {
        msg[msgLen++] = (uint8_t)((v >> 21) & 0x7F);
        msg[msgLen++] = (uint8_t)((v >> 14) & 0x7F);
        msg[msgLen++] = (uint8_t)((v >> 7) & 0x7F);
        msg[msgLen++] = (uint8_t)(v & 0x7F);
    }

    // 0..1 fraction of full scale (same normalisation as OnsetDetector: /2048).
    void putLevel(float level)
    {
        put14((int)(level * 16383.0f + 0.5f));
    }

    void send()
    {
        usbMIDI.sendSysEx(msgLen, msg, false); // false: Teensy adds F0/F7
    }
}

void Telemetry::notePitch(int string, const PitchResult &result)
{
    lastFreq[string] = result.frequency > 0 ? result.frequency : 0.0f;
    lastProb[string] = result.probability;
}

void Telemetry::update(AdcSampler &sampler, const OnsetDetector *onset, const int *activeNote)
{
    if (!TELEMETRY_ENABLED)
        return;

    if (configTimer >= TELEMETRY_CONFIG_MS)
    {
        configTimer = 0;
        sendConfig();
    }

    if (statusTimer >= TELEMETRY_PERIOD_MS)
    {
        statusTimer = 0;
        sendStatus(sampler, onset, activeNote);
        for (int i = 0; i < TELEMETRY_SCOPES_PER_TICK; i++)
        {
            sendScope(sampler, scopeString);
            scopeString = (scopeString + 1) % NUM_STRINGS;
        }
        usbMIDI.send_now();
    }
}

// STATUS payload:
//   time_ms(28) nStrings(7)
//   per string: state(7) onsetRms(14) acRms(14) dcMean(14, 8192-centred raw counts)
//               min(14) max(14) raw 0..4095   freq_x10(14, 0 = none) prob_x100(7) note(7, 0 = none)
void Telemetry::sendStatus(AdcSampler &sampler, const OnsetDetector *onset, const int *activeNote)
{
    begin(TELEM_STATUS);
    put28(millis());
    put7(NUM_STRINGS);

    for (int s = 0; s < NUM_STRINGS; s++)
    {
        sampler.getRecentSamples(s, statsBuffer, STATS_WINDOW);

        int32_t sum = 0;
        int16_t lo = 32767, hi = -32768;
        for (int i = 0; i < STATS_WINDOW; i++)
        {
            int16_t v = statsBuffer[i];
            sum += v;
            if (v < lo)
                lo = v;
            if (v > hi)
                hi = v;
        }
        float mean = (float)sum / STATS_WINDOW;

        float acc = 0.0f;
        for (int i = 0; i < STATS_WINDOW; i++)
        {
            float d = (statsBuffer[i] - mean) / 2048.0f;
            acc += d * d;
        }
        float acRms = sqrtf(acc / STATS_WINDOW);

        put7((int)onset[s].getState());
        putLevel(onset[s].getCurrentRMS());
        putLevel(acRms);
        put14((int)roundf(mean) + 8192);
        put14(lo + ADC_MID);
        put14(hi + ADC_MID);
        put14((int)(lastFreq[s] * 10.0f + 0.5f));
        put7((int)(lastProb[s] * 100.0f + 0.5f));
        put7(activeNote[s] > 0 ? activeNote[s] : 0);
    }
    send();
}

// SCOPE payload: string(7) sampleRate/10(14) nPoints(14) then nPoints x raw(14, 0..4095)
// The most recent samples, decimated by TELEMETRY_SCOPE_DECIMATE.
void Telemetry::sendScope(AdcSampler &sampler, int string)
{
    constexpr int span = TELEMETRY_SCOPE_POINTS * TELEMETRY_SCOPE_DECIMATE;
    static_assert(span <= RING_BUFFER_SIZE, "scope span exceeds ring buffer");

    sampler.getRecentSamples(string, statsBuffer, span);

    begin(TELEM_SCOPE);
    put7(string);
    put14((int)(ADC_SAMPLE_RATE / TELEMETRY_SCOPE_DECIMATE / 10.0f));
    put14(TELEMETRY_SCOPE_POINTS);
    for (int i = 0; i < TELEMETRY_SCOPE_POINTS; i++)
    {
        put14(statsBuffer[i * TELEMETRY_SCOPE_DECIMATE] + ADC_MID);
    }
    send();
}

// CONFIG payload: nStrings(7) sampleRate/10(14) onsetThr(14) offsetThr(14) yinThr_x100(7)
//                 then per string: midiChannel(7)
void Telemetry::sendConfig()
{
    begin(TELEM_CONFIG);
    put7(NUM_STRINGS);
    put14((int)(ADC_SAMPLE_RATE / 10.0f));
    putLevel(ONSET_THRESHOLD);
    putLevel(OFFSET_THRESHOLD);
    put7((int)(YIN_THRESHOLD * 100.0f + 0.5f));
    for (int s = 0; s < NUM_STRINGS; s++)
        put7(MPE_CHANNELS[s]);
    send();
}
