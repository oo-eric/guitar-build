// ADC + Pitch + MIDI — single string pitch-to-MIDI
// Arduino IDE USB Type must be set to "Serial + MIDI"
//
// Detects pitch via autocorrelation, sends MIDI note on/off over USB.
// Your DAW will see the Teensy as a MIDI input device.

#include <usb_midi.h>

const int PICKUP_PIN = A0;
const int LED_PIN = 13;
const int MIDI_CHANNEL = 1;

// Sampling
const int BUFFER_SIZE = 1024;
const int SAMPLE_INTERVAL_US = 50;

int16_t buffer[BUFFER_SIZE];
float actualSampleRate;

// Signal detection
const int SIGNAL_THRESHOLD = 25;        // min spread to detect a note
const int NOTE_OFF_THRESHOLD = 20;       // spread below this = note off
const int VELOCITY = 100;                // fixed velocity for now

// Note tracking
int currentNote = -1;                    // -1 = no note playing
unsigned long noteOnTime = 0;
const unsigned long MIN_NOTE_MS = 50;    // minimum note duration to avoid flicker

// Note names for serial debug
const char* NOTE_NAMES[] = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  pinMode(PICKUP_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);

  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }

  delay(1000);
  Serial.println("=== Pitch-to-MIDI ===");
  Serial.println("USB Type must be 'Serial + MIDI'");
  Serial.println("Pluck a string — MIDI notes will be sent over USB.");
  Serial.println("---");
}

void loop() {
  // Fill buffer and measure actual elapsed time
  unsigned long t0 = micros();
  for (int i = 0; i < BUFFER_SIZE; i++) {
    buffer[i] = analogRead(PICKUP_PIN) - 2048;
    delayMicroseconds(SAMPLE_INTERVAL_US);
  }
  unsigned long elapsed = micros() - t0;
  actualSampleRate = (float)BUFFER_SIZE / elapsed * 1000000.0;

  // Check signal level
  int16_t minVal = 32767;
  int16_t maxVal = -32768;
  for (int i = 0; i < BUFFER_SIZE; i++) {
    if (buffer[i] < minVal) minVal = buffer[i];
    if (buffer[i] > maxVal) maxVal = buffer[i];
  }
  int spread = maxVal - minVal;

  // Note off: signal died
  if (spread < NOTE_OFF_THRESHOLD) {
    if (currentNote >= 0 && (millis() - noteOnTime) > MIN_NOTE_MS) {
      usbMIDI.sendNoteOff(currentNote, 0, MIDI_CHANNEL);
      Serial.print("NOTE OFF: ");
      Serial.println(currentNote);
      digitalWrite(LED_PIN, LOW);
      currentNote = -1;
    }
    Serial.println(spread);
    usbMIDI.read(); // must read to keep USB alive
    return;
  }

  // Signal present — detect pitch
  if (spread >= SIGNAL_THRESHOLD) {
    float freq = detectPitch();

    if (freq > 0) {
      int midiNote = frequencyToMidi(freq);

      // Clamp to valid MIDI range
      if (midiNote < 0) midiNote = 0;
      if (midiNote > 127) midiNote = 127;

      if (midiNote != currentNote) {
        // New note — turn off old one first
        if (currentNote >= 0) {
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
      }
    }
  }

  usbMIDI.read(); // must read to keep USB alive
}

float detectPitch() {
  int minPeriod = actualSampleRate / 1000;
  int maxPeriod = actualSampleRate / 60;

  if (maxPeriod > BUFFER_SIZE / 2) {
    maxPeriod = BUFFER_SIZE / 2;
  }

  long bestCorrelation = 0;
  int bestPeriod = 0;

  long sumSq = 0;
  for (int i = 0; i < BUFFER_SIZE; i++) {
    sumSq += (long)buffer[i] * buffer[i];
  }
  long rmsThreshold = sumSq / 2;

  for (int period = minPeriod; period <= maxPeriod; period++) {
    long correlation = 0;
    int count = BUFFER_SIZE - period;
    for (int i = 0; i < count; i++) {
      correlation += (long)buffer[i] * buffer[i + period];
    }

    if (correlation > bestCorrelation) {
      bestCorrelation = correlation;
      bestPeriod = period;
    }
  }

  if (bestCorrelation < rmsThreshold / 4) {
    return -1;
  }

  if (bestPeriod == 0) {
    return -1;
  }

  // Parabolic interpolation
  if (bestPeriod > minPeriod && bestPeriod < maxPeriod) {
    long corrPrev = 0, corrNext = 0;
    int count = BUFFER_SIZE - bestPeriod;
    for (int i = 0; i < count - 1; i++) {
      corrPrev += (long)buffer[i] * buffer[i + bestPeriod - 1];
      corrNext += (long)buffer[i] * buffer[i + bestPeriod + 1];
    }
    float shift = 0.5 * (corrPrev - corrNext) /
                  (corrPrev - 2.0 * bestCorrelation + corrNext);
    return actualSampleRate / (bestPeriod + shift);
  }

  return actualSampleRate / bestPeriod;
}

int frequencyToMidi(float freq) {
  return round(69 + 12 * log2(freq / 440.0));
}
