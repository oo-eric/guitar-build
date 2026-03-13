// ADC Test — staged validation for buffer circuit + pickup
// Upload this sketch for each stage below.
//
// STAGE 1: Nothing connected to A0
//   - Readings will float randomly (0-4095) — this is normal
//   - Confirms: Teensy works, serial works, ADC works
//
// STAGE 2: Wire voltage divider only to A0
//   - 3.3V --[10K]--+--[10K]-- GND, junction to A0
//   - Readings should sit stable around 2048 (+/- ~20)
//   - Confirms: bias circuit is correct
//
// STAGE 3: Full buffer circuit + pickup connected
//   - Idle readings ~2048, plucking should swing above/below
//   - min/max will spread apart when you pluck

const int PICKUP_PIN = A0;
const int LED_PIN = 13;

// Track signal range over a window
int minVal = 4095;
int maxVal = 0;
unsigned long lastReport = 0;
const unsigned long REPORT_INTERVAL_MS = 500;

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  pinMode(PICKUP_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);

  // Blink LED to confirm sketch is running
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }

  delay(1000); // wait for serial monitor to connect
  Serial.println("=== ADC Test ===");
  Serial.println("Reading A0 every 500ms: avg | min | max | spread");
  Serial.println("Stage 1 (nothing): floating random values");
  Serial.println("Stage 2 (bias only): stable ~2048, spread < 50");
  Serial.println("Stage 3 (full circuit): ~2048 idle, spread grows on pluck");
  Serial.println("---");
}

void loop() {
  // Sample fast, report slow
  int val = analogRead(PICKUP_PIN);

  if (val < minVal) minVal = val;
  if (val > maxVal) maxVal = val;

  unsigned long now = millis();
  if (now - lastReport >= REPORT_INTERVAL_MS) {
    int spread = maxVal - minVal;
    int mid = (maxVal + minVal) / 2;

    Serial.print("avg: ");
    Serial.print(mid);
    Serial.print(" | min: ");
    Serial.print(minVal);
    Serial.print(" | max: ");
    Serial.print(maxVal);
    Serial.print(" | spread: ");
    Serial.print(spread);

    // Visual indicator
    if (spread > 200) {
      Serial.print("  << SIGNAL");
      digitalWrite(LED_PIN, HIGH);
    } else {
      digitalWrite(LED_PIN, LOW);
    }

    Serial.println();

    // Reset for next window
    minVal = 4095;
    maxVal = 0;
    lastReport = now;
  }
}
