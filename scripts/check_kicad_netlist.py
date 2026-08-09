#!/usr/bin/env python3
"""
Independently verify hardware/midi-guitar-preamp.kicad_sch.

This does NOT import the generator's state. It re-parses the finished file,
reads pin geometry out of the embedded lib_symbols, rebuilds connectivity from
the wires/junctions/labels, and then asserts the circuit that
docs/buffer_circuit.md describes. If the generator's geometry is wrong, the
netlist here comes out wrong and the assertions fail.

    python3 scripts/check_kicad_netlist.py
"""

import math
import re
import sys
from pathlib import Path

SCH = Path(__file__).resolve().parent.parent / "hardware" / "midi-guitar-preamp.kicad_sch"

# --------------------------------------------------------------------------
# Minimal s-expression reader
# --------------------------------------------------------------------------

TOKEN = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')


def parse(text):
    stack, cur = [], []
    for m in TOKEN.finditer(text):
        t = m.group()
        if t == "(":
            new = []
            cur.append(new)
            stack.append(cur)
            cur = new
        elif t == ")":
            cur = stack.pop()
        elif t.startswith('"'):
            cur.append(t[1:-1])
        else:
            cur.append(t)
    return cur[0]


def kids(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def kid(node, name):
    k = kids(node, name)
    return k[0] if k else None


def num(v):
    return round(float(v), 3)


# --------------------------------------------------------------------------
# Read the file
# --------------------------------------------------------------------------

if not SCH.exists():
    sys.exit(f"missing {SCH} — run scripts/gen_kicad_schematic.py first")

root = parse(SCH.read_text())

# lib_symbols: "Lib:Name" -> unit -> {pin_number: (x, y)}
libpins = {}
for sym in kids(kid(root, "lib_symbols"), "symbol"):
    full = sym[1]
    units = {}
    for sub in kids(sym, "symbol"):
        m = re.match(r"^(.*)_(\d+)_(\d+)$", sub[1])
        if not m:
            continue
        unit = int(m.group(2))
        for p in kids(sub, "pin"):
            number = kid(p, "number")[1]
            at = kid(p, "at")
            units.setdefault(unit, {})[number] = (num(at[1]), num(at[2]))
    libpins[full] = units


def pin_abs(lib_id, at, rot, unit, number):
    table = libpins[lib_id]
    # unit 0 holds shared graphics; pins live in the numbered units
    px, py = table[unit][number]
    t = math.radians(rot)
    c, s = round(math.cos(t)), round(math.sin(t))
    return (round(at[0] + px * c + py * s, 3),
            round(at[1] + px * s - py * c, 3))


pins = {}   # (ref, number) -> point
values = {}  # ref -> value
placed = []
for sym in kids(root, "symbol"):
    lib_id = kid(sym, "lib_id")
    if lib_id is None:
        continue
    lib_id = lib_id[1]
    at = kid(sym, "at")
    pos, rot = (num(at[1]), num(at[2])), float(at[3])
    unit = int(kid(sym, "unit")[1])
    props = {p[1]: p[2] for p in kids(sym, "property")}
    ref, val = props.get("Reference"), props.get("Value")
    values[ref] = val
    placed.append((ref, lib_id, unit))
    for p in kids(sym, "pin"):
        pins[(ref, p[1])] = pin_abs(lib_id, pos, rot, unit, p[1])

segments = []
for w in kids(root, "wire"):
    pts = kid(w, "pts")
    (a, b) = [(num(p[1]), num(p[2])) for p in kids(pts, "xy")]
    segments.append((a, b))

labels = []  # (name, point)
for l in kids(root, "global_label"):
    at = kid(l, "at")
    labels.append((l[1], (num(at[1]), num(at[2]))))

# --------------------------------------------------------------------------
# Build nets (union-find over coincident / on-segment points)
# --------------------------------------------------------------------------

parent = {}


def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb


def on_seg(p, seg):
    (x1, y1), (x2, y2) = seg
    if x1 == x2 == p[0]:
        return min(y1, y2) <= p[1] <= max(y1, y2)
    if y1 == y2 == p[1]:
        return min(x1, x2) <= p[0] <= max(x1, x2)
    return False


all_pts = set()
for s in segments:
    all_pts.update(s)
all_pts.update(pins.values())
all_pts.update(p for _, p in labels)

for seg in segments:
    union(seg[0], seg[1])
    for p in all_pts:
        if on_seg(p, seg):
            union(p, seg[0])

# name the nets
net_name = {}
for name, p in labels:
    net_name[find(p)] = name
for (ref, number), p in pins.items():
    if ref.startswith("#PWR"):
        net_name[find(p)] = values[ref]


def net_of(ref, number):
    p = pins[(ref, number)]
    return net_name.get(find(p), f"<unnamed@{find(p)}>")


def same_net(*terminals):
    roots = {find(pins[t]) for t in terminals}
    return len(roots) == 1


# --------------------------------------------------------------------------
# Assertions — the circuit of record
# --------------------------------------------------------------------------

errors = []
notes = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


CHANNELS = [
    # (opamp ref, unit, OUT, -IN, +IN, adc net)
    ("U1", 1, "1", "2", "3", "A0"),
    ("U1", 2, "7", "6", "5", "A1"),
    ("U2", 1, "1", "2", "3", "A2"),
    ("U2", 2, "7", "6", "5", "A3"),
    ("U3", 1, "1", "2", "3", "A4"),
    ("U3", 2, "7", "6", "5", "A5"),
]

# Group passives by which op-amp pin they touch.
for i, (u, unit, OUT, NEG, POS, adc) in enumerate(CHANNELS, start=1):
    out_net, neg_net, pos_net = (find(pins[(u, OUT)]), find(pins[(u, NEG)]),
                                 find(pins[(u, POS)]))
    check(out_net != neg_net,
          f"ch{i}: OUT shorted directly to -IN (no feedback element)")
    check(out_net != pos_net, f"ch{i}: OUT shorted to +IN")
    check(neg_net != pos_net, f"ch{i}: inputs shorted together")

    # ADC label must be on the output net
    check(net_name.get(out_net) == adc,
          f"ch{i}: output net is {net_name.get(out_net)!r}, expected {adc!r}")

    # what hangs off each node
    def touching(root_net, exclude_ref=u):
        out = []
        for (ref, number), p in pins.items():
            if ref == exclude_ref or ref.startswith("#PWR"):
                continue
            if find(p) == root_net:
                out.append((ref, number))
        return out

    fb = {r for r, _ in touching(out_net)}
    inv = {r for r, _ in touching(neg_net)}
    noninv = {r for r, _ in touching(pos_net)}

    # feedback: exactly one R and one C bridging OUT and -IN
    bridging = sorted(fb & inv)
    kinds = sorted(values[r] for r in bridging)
    check(len(bridging) == 2,
          f"ch{i}: expected 2 feedback parts (Rf, Cf), got {bridging} {kinds}")
    check("100k" in kinds and "330p" in kinds,
          f"ch{i}: feedback values {kinds}, expected ['100k', '330p']")

    # -IN also carries the gain resistor down to VBIAS
    rg = [r for r in inv - fb if r.startswith("R")]
    check(len(rg) == 1, f"ch{i}: expected 1 gain resistor on -IN, got {rg}")
    if rg:
        other = [n for (ref, n) in pins if ref == rg[0]]
        rg_nets = {net_of(rg[0], n) for n in other}
        check("VBIAS" in rg_nets,
              f"ch{i}: gain resistor {rg[0]} does not reach VBIAS ({rg_nets})")
        notes.append(f"ch{i} ({adc}): Rf=100k Rg={values[rg[0]]} "
                     f"-> gain = {1 + 100.0 / float(values[rg[0]].replace('k','').replace('2k2','2.2') if values[rg[0]] != '2k2' else '2.2'):.1f}x")

    # +IN: coupling cap from the pickup, and the 1M bias resistor
    cin = [r for r in noninv if r.startswith("C")]
    rbias = [r for r in noninv if r.startswith("R")]
    check(len(cin) == 1, f"ch{i}: expected 1 input cap on +IN, got {cin}")
    check(len(rbias) == 1 and values[rbias[0]] == "1M",
          f"ch{i}: expected 1M bias resistor on +IN, got "
          f"{[(r, values[r]) for r in rbias]}")

    # THE fix being verified: signal enters +IN, never -IN.
    if cin:
        far = [n for (ref, n) in pins if ref == cin[0]]
        conn_side = [n for n in far if find(pins[(cin[0], n)]) != pos_net]
        check(len(conn_side) == 1, f"ch{i}: input cap wiring is odd")
        if conn_side:
            jrefs = {r for r, _ in touching(find(pins[(cin[0], conn_side[0])]),
                                            exclude_ref=cin[0])
                     if r.startswith("J")}
            check(len(jrefs) == 1,
                  f"ch{i}: input cap does not reach a pickup connector "
                  f"(found {jrefs})")

    # power pins (unit 3 of the same chip)
    check(net_of(u, "8") == "+3V3", f"{u}: VDD is {net_of(u, '8')}, want +3V3")
    check(net_of(u, "4") == "GND", f"{u}: VSS is {net_of(u, '4')}, want GND")

# bias rail: divider between +3V3 and GND, with VBIAS at the midpoint
vbias_pins = [(r, n) for (r, n) in pins if net_of(r, n) == "VBIAS"]
# both 10k legs meet at the midpoint, so both touch VBIAS
div = sorted({r for r, _ in vbias_pins if r.startswith("R") and values[r] == "10k"})
check(len(div) == 2,
      f"expected both 10k divider legs at the VBIAS midpoint, got {div}")
# ...and their far ends must be the rails
if len(div) == 2:
    far = set()
    for r in div:
        for (ref, n) in pins:
            if ref == r and net_of(r, n) != "VBIAS":
                far.add(net_of(r, n))
    check(far == {"+3V3", "GND"},
          f"divider legs should reach +3V3 and GND, they reach {far}")
bulk = [r for r, _ in vbias_pins if r.startswith("C")]
check(len(bulk) >= 2,
      f"VBIAS needs bulk + ceramic bypass, found {[(r, values[r]) for r in bulk]}")

# +3V3 rail: three 100n per-chip decoupling caps, plus one bulk electrolytic.
# The bulk cap is the one the MCP6002 datasheet asks for on the rail itself;
# the 100n caps alone do not cover low-frequency sag.
rail_caps = {r for (r, n) in pins
             if r.startswith("C") and net_of(r, n) == "+3V3"}
rail_bulk = sorted(r for r in rail_caps if values[r].endswith("u"))
check(len(rail_bulk) == 1,
      f"expected exactly 1 bulk electrolytic on +3V3, got "
      f"{[(r, values[r]) for r in rail_bulk]}")
# ...and its other leg must land on GND, not somewhere unhelpful
for r in rail_bulk:
    other = {net_of(r, n) for (ref, n) in pins
             if ref == r and net_of(r, n) != "+3V3"}
    check(other == {"GND"},
          f"{r}: bulk cap's return leg should be GND, it reaches {other}")

# every op-amp unit 3 present
for u in ("U1", "U2", "U3"):
    check(any(r == u and unit == 3 for r, _, unit in placed),
          f"{u}: power unit (pins 4/8) not placed")

# Two different net names must never resolve to the same node. Overlapping
# collinear wire segments merge nets silently; this is how a PWR_FLAG stub
# once shorted +3V3 to GND.
by_root = {}
for name, p in labels:
    by_root.setdefault(find(p), set()).add(name)
for (ref, number), p in pins.items():
    if ref.startswith("#PWR"):
        by_root.setdefault(find(p), set()).add(values[ref])
for r, names in by_root.items():
    check(len(names) == 1,
          f"nets {sorted(names)} are shorted together")

# no unnamed multi-pin nets left floating
roots = {}
for (ref, number), p in pins.items():
    roots.setdefault(find(p), []).append((ref, number))
for r, members in roots.items():
    if len(members) == 1 and r not in net_name:
        errors.append(f"pin {members[0]} is not connected to anything")

# --------------------------------------------------------------------------

print(f"parsed {SCH.name}")
print(f"  symbols: {len(placed)}   wires: {len(segments)}   "
      f"labels: {len(labels)}   nets: {len(roots)}")
named = sorted({n for n in net_name.values()})
print(f"  named nets: {', '.join(named)}")
for n in notes:
    print(f"  {n}")

if errors:
    print(f"\nFAILED — {len(errors)} problem(s):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
print("\nnetlist matches docs/buffer_circuit.md")
