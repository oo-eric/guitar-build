#!/usr/bin/env python3
"""Read Teensy USB CDC serial output for a fixed window.

Auto-discovers /dev/cu.usbmodem*, asserts DTR, and stays attached across
intermittent empty reads. Only treats it as a real disconnect when the
/dev node actually disappears (or after many consecutive empty reads).

Usage:
    scripts/teensy_serial.py [seconds]    # default 60s
"""
import glob
import os
import sys
import time

import serial


def find_dev() -> str | None:
    devs = glob.glob("/dev/cu.usbmodem*")
    return devs[0] if devs else None


def main(duration: float = 60.0, baud: int = 115200) -> int:
    end = time.time() + duration
    last_open_dev: str | None = None
    while time.time() < end:
        dev = find_dev()
        if not dev:
            time.sleep(0.2)
            continue
        try:
            s = serial.Serial(dev, baud, timeout=0.3)
            s.dtr = True
            if dev != last_open_dev:
                sys.stdout.write(f"[opened {dev}]\n")
                sys.stdout.flush()
                last_open_dev = dev
            consecutive_empty_errors = 0
            while time.time() < end:
                try:
                    line = s.readline()
                except (serial.SerialException, OSError) as e:
                    if not os.path.exists(dev):
                        sys.stdout.write(f"[lost {dev}: {e}]\n")
                        sys.stdout.flush()
                        last_open_dev = None
                        try: s.close()
                        except Exception: pass
                        time.sleep(0.3)
                        break
                    consecutive_empty_errors += 1
                    if consecutive_empty_errors == 1 or consecutive_empty_errors % 50 == 0:
                        sys.stdout.write(f"[empty-read x{consecutive_empty_errors} (device still present)]\n")
                        sys.stdout.flush()
                    time.sleep(0.05)
                    continue
                if line:
                    sys.stdout.write(line.decode("utf-8", "replace"))
                    sys.stdout.flush()
                    consecutive_empty_errors = 0
        except (serial.SerialException, OSError) as e:
            sys.stdout.write(f"[open failed: {e}]\n")
            sys.stdout.flush()
            last_open_dev = None
            time.sleep(0.3)
    return 0


if __name__ == "__main__":
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    sys.exit(main(seconds))
