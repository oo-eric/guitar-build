// ADC + Pitch + MIDI + USB Audio — single string pitch-to-MIDI
// Arduino IDE USB Type must be set to "Serial + MIDI + Audio"
//
// Detects pitch via YIN algorithm, sends MIDI note on/off over USB.
// Also streams raw pickup audio over USB Audio (visible as an audio input
// device on your computer — open it in a DAW, Audacity, etc.).

#include <Audio.h>
#include <usb_midi.h>

#include <Adafruit_GFX.h>     // include Adafruit graphics library
#include <Adafruit_ILI9341.h> // include Adafruit ILI9341 TFT library

// Audio library objects
AudioInputAnalog adcInput(A0); // ADC input from pickup
AudioOutputUSB usbAudioOut;    // USB audio output (stereo)
AudioRecordQueue queue;        // tap audio stream for pitch detection

// Connections: ADC → USB audio (both channels) and ADC → queue
AudioConnection patchCord1(adcInput, 0, usbAudioOut, 0); // left channel
AudioConnection patchCord2(adcInput, 0, usbAudioOut, 1); // right channel
AudioConnection patchCord3(adcInput, 0, queue, 0);       // pitch detection tap

const int LED_PIN = 13;
const int MIDI_CHANNEL = 1;

// ILI9341 TFT display pins
#define TFT_DC 9
#define TFT_CS 10

// initialize ILI9341 TFT library
Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC); // , TFT_RST

// Sampling — Audio library runs at 44100 Hz, 128 samples per block
const float SAMPLE_RATE = 44100.0;
const int BLOCK_SIZE = 128;                      // Audio library block size
const int NUM_BLOCKS = 12;                       // blocks to accumulate before pitch detection
const int BUFFER_SIZE = BLOCK_SIZE * NUM_BLOCKS; // 1536 samples

int16_t buffer[BUFFER_SIZE];
int bufferIndex = 0;

// Signal detection
const int SIGNAL_THRESHOLD = 300;   // min spread to detect a note (idle ~55, playing ~1400+)
const int NOTE_OFF_THRESHOLD = 150; // spread below this = note off
const int VELOCITY = 100;           // fixed velocity for now

// Note tracking
int currentNote = -1; // -1 = no note playing
unsigned long noteOnTime = 0;
const unsigned long MIN_NOTE_MS = 50; // minimum note duration to avoid flicker

// Note names for serial debug
const char *NOTE_NAMES[] = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};

// Waveform display
const int WAVE_X = 0;
const int WAVE_Y = 40;     // top of waveform area
const int WAVE_W = 240;    // screen width
const int WAVE_H = 200;    // waveform area height
int16_t prevWaveY[240];    // previous y positions for erasing
bool waveDrawn = false;    // has a waveform been drawn yet?

void setup()
{

  Serial.begin(9600);
  if (CrashReport)
    Serial.print(CrashReport);

  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  // Audio library needs memory for its block system
  AudioMemory(12);

  // Start recording queue for pitch detection
  queue.begin();

  // Initialize TFT display
  tft.begin();
  tft.fillScreen(ILI9341_BLACK);

  for (int i = 0; i < 3; i++)
  {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }

  delay(1000);
  Serial.println("=== Pitch-to-MIDI + USB Audio ===");
  Serial.println("USB Type must be 'Serial + MIDI + Audio'");
  Serial.println("Pluck a string — MIDI notes sent over USB, audio streamed over USB Audio.");
  Serial.println("---");
}

void loop()
{
  // Accumulate audio blocks into our pitch detection buffer
  while (queue.available())
  {
    int16_t *block = queue.readBuffer();
    int samplesToCopy = min(BLOCK_SIZE, BUFFER_SIZE - bufferIndex);
    memcpy(buffer + bufferIndex, block, samplesToCopy * sizeof(int16_t));
    bufferIndex += samplesToCopy;
    queue.freeBuffer();
  }

  // Wait until we have a full buffer before doing pitch detection
  if (bufferIndex < BUFFER_SIZE)
  {
    usbMIDI.read();
    return;
  }

  bufferIndex = 0;

  // Draw waveform and measure how long it takes
  unsigned long drawStart = micros();
  drawWaveform();
  unsigned long drawTime = micros() - drawStart;
  Serial.print("TFT draw: ");
  Serial.print(drawTime / 1000.0, 1);
  Serial.println(" ms");

  // Check signal level
  int16_t minVal = 32767;
  int16_t maxVal = -32768;
  for (int i = 0; i < BUFFER_SIZE; i++)
  {
    if (buffer[i] < minVal)
      minVal = buffer[i];
    if (buffer[i] > maxVal)
      maxVal = buffer[i];
  }
  int spread = maxVal - minVal;

  // Note off: signal died
  if (spread < NOTE_OFF_THRESHOLD)
  {
    if (currentNote >= 0 && (millis() - noteOnTime) > MIN_NOTE_MS)
    {
      usbMIDI.sendNoteOff(currentNote, 0, MIDI_CHANNEL);
      Serial.print("NOTE OFF: ");
      Serial.println(currentNote);
      digitalWrite(LED_PIN, LOW);
      clearNoteInfo();
      currentNote = -1;
    }
    usbMIDI.read();
    return;
  }

  // Signal present — detect pitch
  if (spread >= SIGNAL_THRESHOLD)
  {
    float freq = detectPitch();

    if (freq > 0)
    {
      int midiNote = frequencyToMidi(freq);

      // Clamp to valid MIDI range
      if (midiNote < 0)
        midiNote = 0;
      if (midiNote > 127)
        midiNote = 127;

      if (midiNote != currentNote)
      {
        // New note — turn off old one first
        if (currentNote >= 0)
        {
          usbMIDI.sendNoteOff(currentNote, 0, MIDI_CHANNEL);
        }
        // Send new note
        usbMIDI.sendNoteOn(midiNote, VELOCITY, MIDI_CHANNEL);
        currentNote = midiNote;
        noteOnTime = millis();
        digitalWrite(LED_PIN, HIGH);

        int noteIndex = midiNote % 12;
        int octave = (midiNote / 12) - 1;
        Serial.print("NOTE ON: ");
        Serial.print(NOTE_NAMES[noteIndex]);
        Serial.print(octave);
        Serial.print(" (MIDI ");
        Serial.print(midiNote);
        Serial.print(") | freq: ");
        Serial.print(freq, 1);
        Serial.print(" Hz | spread: ");
        Serial.println(spread);

        drawNoteInfo(midiNote, freq);
      }
    }
  }

  usbMIDI.read();
}

float detectPitch()
{
  // Guitar range: ~60 Hz (drop D low) to ~700 Hz (high E, ~12th fret)
  // minPeriod must be large enough for CMND to stabilize (~63+ samples)
  int minPeriod = SAMPLE_RATE / 700; // ~63 samples
  int maxPeriod = SAMPLE_RATE / 60;  // ~735 samples

  if (maxPeriod > BUFFER_SIZE / 2)
  {
    maxPeriod = BUFFER_SIZE / 2;
  }

  // YIN algorithm — cumulative mean normalized difference
  // Step 1: compute difference function d(tau)
  // Step 2: cumulative mean normalization d'(tau) — suppresses harmonics
  // Step 3: pick FIRST dip below threshold — guarantees fundamental, not harmonics

  // Allocate on stack — maxPeriod is at most BUFFER_SIZE/2 (768)
  float cmnd[BUFFER_SIZE / 2 + 1]; // cumulative mean normalized difference
  cmnd[0] = 1.0f;

  float runningSum = 0;
  int bestPeriod = 0;
  float bestDiff = 1.0f;

  for (int tau = 1; tau <= maxPeriod; tau++)
  {
    float diff = 0; // float to avoid int32 overflow with 16-bit samples
    int count = BUFFER_SIZE - tau;
    for (int i = 0; i < count; i++)
    {
      float d = (float)buffer[i] - buffer[i + tau];
      diff += d * d;
    }

    runningSum += diff;
    // Cumulative mean normalized difference: d'(tau) = d(tau) / ((1/tau) * sum(d(1..tau)))
    cmnd[tau] = (runningSum > 0) ? (diff * tau / runningSum) : 1.0f;

    // Only consider periods in guitar range
    if (tau >= minPeriod)
    {
      // Look for first dip below threshold (YIN absolute threshold)
      if (cmnd[tau] < 0.20f)
      {
        // Find the local minimum of this dip
        bestPeriod = tau;
        bestDiff = cmnd[tau];
        // Continue to find the bottom of this dip
        while (tau + 1 <= maxPeriod)
        {
          float diff2 = 0;
          int count2 = BUFFER_SIZE - (tau + 1);
          for (int i = 0; i < count2; i++)
          {
            float d2 = (float)buffer[i] - buffer[i + tau + 1];
            diff2 += d2 * d2;
          }
          runningSum += diff2;
          cmnd[tau + 1] = (runningSum > 0) ? (diff2 * (tau + 1) / runningSum) : 1.0f;
          tau++;
          if (cmnd[tau] < bestDiff)
          {
            bestDiff = cmnd[tau];
            bestPeriod = tau;
          }
          else
          {
            break; // passed the minimum, stop
          }
        }
        break; // use the first dip — this is the fundamental
      }
    }
  }

  if (bestPeriod == 0)
  {
    return -1;
  }

  // Parabolic interpolation using the cmnd array
  if (bestPeriod > minPeriod && bestPeriod < maxPeriod)
  {
    float nPrev = cmnd[bestPeriod - 1];
    float nNext = cmnd[bestPeriod + 1];
    float denom = nPrev - 2.0f * bestDiff + nNext;
    if (fabsf(denom) > 1e-6f)
    {
      float shift = 0.5f * (nPrev - nNext) / denom;
      return SAMPLE_RATE / (bestPeriod + shift);
    }
  }

  return SAMPLE_RATE / bestPeriod;
}

int frequencyToMidi(float freq)
{
  return round(69 + 12 * log2(freq / 440.0));
}

void drawWaveform()
{
  // Downsample buffer (1536 samples) to screen width (240 pixels)
  // For each pixel column, find the min/max in that chunk and draw a vertical line
  int samplesPerPixel = BUFFER_SIZE / WAVE_W; // ~6 samples per pixel

  for (int x = 0; x < WAVE_W; x++)
  {
    // Erase previous column
    if (waveDrawn)
    {
      tft.drawFastVLine(x, WAVE_Y, WAVE_H, ILI9341_BLACK);
    }

    // Find min/max in this chunk
    int start = x * samplesPerPixel;
    int16_t lo = buffer[start];
    int16_t hi = buffer[start];
    for (int j = 1; j < samplesPerPixel && (start + j) < BUFFER_SIZE; j++)
    {
      int16_t s = buffer[start + j];
      if (s < lo) lo = s;
      if (s > hi) hi = s;
    }

    // Map sample range (-32768..32767) to waveform area
    int yLo = map(hi, -32768, 32767, WAVE_Y + WAVE_H - 1, WAVE_Y); // hi sample = top of screen
    int yHi = map(lo, -32768, 32767, WAVE_Y + WAVE_H - 1, WAVE_Y);

    // Draw vertical line from yLo to yHi (min 1px)
    if (yHi == yLo) yHi = yLo + 1;
    tft.drawFastVLine(x, yLo, yHi - yLo, ILI9341_GREEN);
  }
  waveDrawn = true;
}

void drawNoteInfo(int midiNote, float freq)
{
  // Clear the top area
  tft.fillRect(0, 0, 240, WAVE_Y, ILI9341_BLACK);

  tft.setCursor(4, 4);
  tft.setTextColor(ILI9341_WHITE);
  tft.setTextSize(3);

  int noteIndex = midiNote % 12;
  int octave = (midiNote / 12) - 1;
  tft.print(NOTE_NAMES[noteIndex]);
  tft.print(octave);

  tft.setTextSize(1);
  tft.setCursor(4, 28);
  tft.print(freq, 1);
  tft.print(" Hz  MIDI ");
  tft.print(midiNote);
}

void clearNoteInfo()
{
  tft.fillRect(0, 0, 240, WAVE_Y, ILI9341_BLACK);
}
