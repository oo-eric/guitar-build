#!/usr/bin/env python3
"""Live terminal dashboard for the Teensy guitar MIDI firmware.

Parses serial output (RMS, ONSET, NOTE ON/OFF/CHANGE, pitch lines) and
renders a colored, animated dashboard with:

  - Color-graded volume bar (cyan/green/yellow/red)
  - 60-sample sparkline of recent RMS history
  - Current note name in pitch-class color
  - Velocity meter and frequency
  - Rolling event log with type-coded colors

Usage:
    scripts/guitar_monitor.py         # auto-discover device
    scripts/guitar_monitor.py <path>  # explicit /dev path
    Ctrl+C to quit.
"""
import glob
import os
import re
import sys
import time
from collections import deque
from dataclasses import dataclass, field

import serial
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTE_COLORS = [
    "red", "bright_red", "yellow", "bright_yellow",
    "green", "bright_green", "cyan", "bright_cyan",
    "blue", "bright_blue", "magenta", "bright_magenta",
]
STATE_NAMES = {0: "IDLE", 1: "ATTACK", 2: "SUSTAIN"}
STATE_STYLES = {0: "dim", 1: "bold yellow", 2: "bold green"}

SPARKLINE_CHARS = " ▁▂▃▄▅▆▇█"
SPARKLINE_LEN = 60

PATTERNS = {
    "rms":      re.compile(r"\[(\w+)\] state=(\d+) rms=([\d.]+)"),
    "onset":    re.compile(r"\[(\w+)\] ONSET amp=([\d.]+)"),
    "pitch":    re.compile(r"\[(\w+)\] pitch: freq=([\d.]+) prob=([\d.]+)"),
    "note_on":  re.compile(r"\[(\w+)\] NOTE ON: \S+ \(MIDI (\d+)\) vel=(\d+) freq=([\d.]+)Hz"),
    "note_off": re.compile(r"\[(\w+)\] NOTE OFF: MIDI (-?\d+)"),
    "note_chg": re.compile(r"\[(\w+)\] NOTE CHANGE: MIDI (-?\d+)"),
}


def midi_to_note(n: int) -> str:
    if n < 0:
        return "—"
    return f"{NOTE_NAMES[n % 12]}{(n // 12) - 1}"


def note_color(n: int) -> str:
    return "white" if n < 0 else NOTE_COLORS[n % 12]


@dataclass
class StringState:
    name: str
    state: int = 0
    rms: float = 0.0
    rms_peak: float = 0.0
    rms_history: deque = field(default_factory=lambda: deque([0.0] * SPARKLINE_LEN, maxlen=SPARKLINE_LEN))
    midi_note: int = -1
    velocity: int = 0
    freq: float = 0.0
    prob: float = 0.0
    note_on_at: float = 0.0


@dataclass
class App:
    dev: str = ""
    connected: bool = False
    strings: dict = field(default_factory=dict)
    events: deque = field(default_factory=lambda: deque(maxlen=10))

    def get(self, name: str) -> StringState:
        if name not in self.strings:
            self.strings[name] = StringState(name=name)
        return self.strings[name]


def parse_line(app: App, text: str):
    text = text.strip()
    if not text:
        return None

    m = PATTERNS["rms"].search(text)
    if m:
        s = app.get(m.group(1))
        s.state = int(m.group(2))
        s.rms = float(m.group(3))
        if s.rms > s.rms_peak:
            s.rms_peak = s.rms
        s.rms_history.append(s.rms)
        return None

    m = PATTERNS["note_on"].search(text)
    if m:
        s = app.get(m.group(1))
        s.midi_note = int(m.group(2))
        s.velocity = int(m.group(3))
        s.freq = float(m.group(4))
        s.note_on_at = time.time()
        return ("note_on", s.name, s.midi_note, s.velocity, s.freq)

    m = PATTERNS["note_off"].search(text)
    if m:
        s = app.get(m.group(1))
        old = s.midi_note
        s.midi_note = -1
        s.velocity = 0
        return ("note_off", s.name, old)

    m = PATTERNS["note_chg"].search(text)
    if m:
        s = app.get(m.group(1))
        s.midi_note = int(m.group(2))
        s.note_on_at = time.time()
        return ("note_chg", s.name, s.midi_note)

    m = PATTERNS["onset"].search(text)
    if m:
        return ("onset", m.group(1), float(m.group(2)))

    m = PATTERNS["pitch"].search(text)
    if m:
        s = app.get(m.group(1))
        s.freq = float(m.group(2))
        s.prob = float(m.group(3))
        return None

    return None


def find_dev(override: str | None) -> str | None:
    if override:
        return override if os.path.exists(override) else None
    devs = glob.glob("/dev/cu.usbmodem*")
    return devs[0] if devs else None


def colored_bar(value: float, full_scale: float, width: int = 40) -> Text:
    pct = max(0.0, min(1.0, value / full_scale))
    filled = int(pct * width)
    bar = Text()
    for i in range(width):
        if i < filled:
            ratio = i / max(1, width - 1)
            if ratio < 0.4:
                color = "cyan"
            elif ratio < 0.7:
                color = "green"
            elif ratio < 0.85:
                color = "yellow"
            else:
                color = "red"
            bar.append("█", style=color)
        else:
            bar.append("░", style="dim")
    return bar


def sparkline(values: deque, full_scale: float) -> Text:
    levels = len(SPARKLINE_CHARS) - 1
    out = Text()
    for v in values:
        idx = max(0, min(levels, int(v / full_scale * levels)))
        ch = SPARKLINE_CHARS[idx]
        ratio = idx / levels
        if ratio < 0.3:
            color = "cyan"
        elif ratio < 0.6:
            color = "green"
        elif ratio < 0.85:
            color = "yellow"
        else:
            color = "red"
        out.append(ch, style=color if idx > 0 else "dim")
    return out


def velocity_bar(vel: int, width: int = 16) -> Text:
    pct = max(0.0, min(1.0, vel / 127.0))
    filled = int(pct * width)
    bar = Text()
    bar.append("█" * filled, style="bright_magenta")
    bar.append("░" * (width - filled), style="dim")
    return bar


def render_event(evt, ts: str) -> Text:
    t = Text(f"{ts}  ", style="dim")
    kind = evt[0]
    if kind == "note_on":
        _, name, midi, vel, freq = evt
        t.append("NOTE ON ", style="bold green")
        t.append(f" [{name}] ", style="cyan")
        t.append(midi_to_note(midi), style=f"bold {note_color(midi)}")
        t.append(f"  vel={vel}  {freq:.1f}Hz", style="dim")
    elif kind == "note_off":
        _, name, midi = evt
        t.append("NOTE OFF", style="bold red")
        t.append(f" [{name}] ", style="cyan")
        t.append(midi_to_note(midi), style=note_color(midi))
    elif kind == "note_chg":
        _, name, midi = evt
        t.append("NOTE CHG", style="bold yellow")
        t.append(f" [{name}] -> ", style="cyan")
        t.append(midi_to_note(midi), style=f"bold {note_color(midi)}")
    elif kind == "onset":
        _, name, amp = evt
        t.append("ONSET   ", style="bold blue")
        t.append(f" [{name}] amp={amp:.4f}", style="dim")
    return t


def render_string_block(s: StringState) -> Text:
    block = Text()

    block.append(f"{s.name}", style="bold cyan")
    block.append("  ")
    block.append(STATE_NAMES.get(s.state, "?"), style=STATE_STYLES.get(s.state, "white"))
    block.append("\n\n")

    block.append("  vol  ")
    block.append_text(colored_bar(s.rms, 0.5, width=44))
    block.append(f"  {s.rms:.4f}", style="bold")
    block.append(f"   peak {s.rms_peak:.4f}\n", style="dim")

    block.append("  hist ")
    block.append_text(sparkline(s.rms_history, 0.5))
    block.append(f"   ({SPARKLINE_LEN} samples)\n", style="dim")

    note_text = midi_to_note(s.midi_note)
    fresh = (time.time() - s.note_on_at) < 0.4 and s.midi_note >= 0
    note_style = f"bold {note_color(s.midi_note)}"
    if fresh:
        note_style = f"bold reverse {note_color(s.midi_note)}"

    block.append("\n  note ")
    block.append(f" {note_text:>4s} ", style=note_style)
    block.append(f"  midi={s.midi_note:>3d}", style="dim" if s.midi_note < 0 else "")
    block.append(f"   freq={s.freq:>7.1f} Hz", style="dim")
    block.append(f"   prob={s.prob:.2f}\n", style="dim")

    block.append("  vel  ")
    block.append_text(velocity_bar(s.velocity))
    block.append(f"  {s.velocity:>3d}/127\n", style="dim")
    return block


def render_dashboard(app: App):
    if not app.strings:
        body = Text("Waiting for serial data — pluck a string.", style="dim italic")
    else:
        body = Group(*[render_string_block(s) for s in app.strings.values()])
    state_panel = Panel(body, title="[bold]Strings[/bold]", border_style="cyan", padding=(0, 1))

    if app.events:
        evt_renderable = Group(*[render_event(evt, ts) for (ts, evt) in app.events])
    else:
        evt_renderable = Text("(no events yet)", style="dim italic")
    events_panel = Panel(evt_renderable, title="[bold]Recent events[/bold]", border_style="magenta", padding=(0, 1))

    status = Text()
    status.append(app.dev or "scanning for /dev/cu.usbmodem*", style="cyan")
    status.append("   ")
    status.append("● CONNECTED" if app.connected else "○ disconnected",
                  style="bold green" if app.connected else "bold red")
    status.append("     ", style="dim")
    status.append("(Ctrl+C to quit)", style="dim italic")

    return Group(status, state_panel, events_panel)


def main():
    override = sys.argv[1] if len(sys.argv) > 1 else None
    app = App()
    s: serial.Serial | None = None
    buf = b""

    try:
        with Live(render_dashboard(app), refresh_per_second=20, screen=True) as live:
            while True:
                if s is None:
                    dev = find_dev(override)
                    if dev:
                        try:
                            s = serial.Serial(dev, 115200, timeout=0.0)
                            s.dtr = True
                            app.dev = dev
                            app.connected = True
                            buf = b""
                        except (serial.SerialException, OSError):
                            s = None
                            app.connected = False

                if s is not None:
                    try:
                        chunk = s.read(4096)
                    except (serial.SerialException, OSError):
                        chunk = b""
                        if not os.path.exists(app.dev):
                            try: s.close()
                            except Exception: pass
                            s = None
                            app.connected = False
                            buf = b""
                    if chunk:
                        buf += chunk
                        while b"\n" in buf:
                            raw, buf = buf.split(b"\n", 1)
                            text = raw.decode("utf-8", "replace")
                            evt = parse_line(app, text)
                            if evt:
                                app.events.append((time.strftime("%H:%M:%S"), evt))

                live.update(render_dashboard(app))
                time.sleep(0.05)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
