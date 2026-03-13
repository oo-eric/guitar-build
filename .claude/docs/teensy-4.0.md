# Teensy 4.0 Reference

Source: https://www.pjrc.com/store/teensy40.html

## Processor

- ARM Cortex-M7 at 600 MHz
- Dual-issue superscalar (up to 2 instructions per cycle)
- 32-bit and 64-bit hardware FPU
- DSP extension instructions

## Memory

- **Flash:** 2 MB
- **RAM:** 1024 KB total (512 KB ITCM + 512 KB for DMA)
- **EEPROM:** 1,080 bytes (emulated)

## Pins

- **Total I/O:** 40 (24 breadboard-accessible)
- **Analog inputs:** 14 pins
- **PWM:** 31 pins (19 frequency groups)
- **Digital:** all 40 pins, 3.3V only (NOT 5V tolerant)
- Recommended max 4mA per pin

## ADC

- 14 analog input pins
- 10-bit default, up to 12-bit hardware resolution
- Fixed 0-3.3V range
- Built-in analog comparators

## Communication

| Protocol | Count | Notes |
|----------|-------|-------|
| Serial/UART | 7 | Independent ports with FIFOs |
| SPI | 3 | First has FIFO |
| I2C | 3 | 100/400/1000 kbit/sec |
| CAN | 3 | 1 with CAN FD |
| I2S/TDM | 2 | Up to 8ch I2S or 16ch TDM |
| S/PDIF | 1 | Independent from I2S |

## USB

- 480 Mbit/sec device mode
- Supports: Serial, MIDI, Audio, HID (keyboard/mouse/joystick)
- USB Host via 2 SMT pads on bottom
- Arduino IDE USB Type must be set to "Serial + MIDI" for usbMIDI

## Audio

- 2x I2S/TDM ports (for future PCM1808 ADC upgrade)
- S/PDIF output
- MQS pulsed digital output (small speakers)

## Power

- Input via USB (VUSB) or external 5V (VIN pin)
- 3.3V regulator output: max 250mA for external circuits
- ~100mA draw at 600 MHz
- VBAT pin for CR2032 coin cell (RTC backup)
- On/Off pin with soft power control
- **Do NOT power via VIN and USB simultaneously without cutting the VIN-VUSB trace**

## Timing

- 4 dedicated interval timers
- 32 PWM timers
- 32-bit cycle counter at 600 MHz
- 3 watchdog timers

## Other Notable Hardware

- 32-channel DMA controller
- Hardware true random number generator
- Cryptographic acceleration
- Internal temperature sensor
- FlexIO (configurable peripheral for custom protocols)
- SD card via built-in SDIO socket (4-bit native)

## Physical

- 24 breadboard-friendly through-hole pins per side
- Additional pins accessible via bottom SMT pads (pins 24-33, USB host, SD)
- 3.3V logic levels throughout

## Project-Relevant Notes

- 14 analog pins is enough for 6 strings (one per string) with headroom
- 3x I2C buses available for MPU-6050 accelerometer
- 2x I2S ports support up to 3x PCM1808 stereo ADC modules if 12-bit onboard ADC proves insufficient
- No native Ethernet (unlike Teensy 4.1) — Phase 4 stage connectivity needs alternative approach
