#!/usr/bin/env python3
"""
Generate hardware/midi-guitar-preamp.kicad_sch from the canonical circuit in
docs/buffer_circuit.md.

Six non-inverting MCP6002 preamp channels running on 3.3V from the Teensy.
Edit the CONFIG block below and re-run; do not hand-edit the .kicad_sch.

    python3 scripts/gen_kicad_schematic.py

Symbol definitions are embedded in the output file, so it opens in KiCad
without any library setup.
"""

import uuid as _uuid
from pathlib import Path

# --------------------------------------------------------------------------
# CONFIG — circuit values (see docs/buffer_circuit.md)
# --------------------------------------------------------------------------

PROJECT = "midi-guitar-preamp"

R_FEEDBACK = "100k"      # Rf
C_FEEDBACK = "330p"      # Cf  -> ~4.8kHz anti-alias corner with Rf
R_BIAS_IN = "1M"         # Rbias, sets input impedance
C_IN = "100n"            # Cin, film/C0G (NOT electrolytic)
R_DIVIDER = "10k"        # bias divider halves
C_BIAS_BULK = "100u"     # VBIAS bulk bypass
C_RAIL_BULK = "10u"      # +3V3 bulk bypass (datasheet wants >=1uF on the rail)
C_BYPASS = "100n"        # decoupling

# THT throughout: matches the DIP-8 MCP6002 and axial passives already on hand,
# and stays hand-solderable. SMD would shrink the board a lot if ever wanted.
FP_R = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
FP_C_FILM = "Capacitor_THT:C_Rect_L7.0mm_W2.5mm_P5.00mm"
FP_C_DISC = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
FP_C_ELEC = "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"
FP_DIP8 = "Package_DIP:DIP-8_W7.62mm"
FP_HDR2 = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
FP_HDR8 = "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"

# string -> (label, gain resistor Rg, ADC net). Gain = 1 + Rf/Rg.
CHANNELS = [
    ("E2", "2k2", "A0"),
    ("A2", "2k2", "A1"),
    ("D3", "2k2", "A2"),
    ("G3", "2k2", "A3"),
    ("B3", "2k2", "A4"),
    ("E4", "2k2", "A5"),
]

# --------------------------------------------------------------------------
# Deterministic UUIDs — same input always yields the same file, so the
# schematic diffs cleanly in git instead of churning every regeneration.
# --------------------------------------------------------------------------

NS = _uuid.UUID("6f1d5e2a-9c3b-4d7e-8a1f-2b4c6d8e0a12")
_uid_counter = {}


def uid(tag: str) -> str:
    n = _uid_counter.get(tag, 0)
    _uid_counter[tag] = n + 1
    return str(_uuid.uuid5(NS, f"{tag}:{n}"))


ROOT_UUID = uid("root")

# --------------------------------------------------------------------------
# Symbol library (embedded)
#
# Symbol-internal geometry uses a Y-up convention; the schematic sheet is
# Y-down. KiCad flips Y when it instantiates a symbol. pin_xy() below applies
# the same transform, so wire endpoints are computed from the identical math
# that places the pins -- connectivity is correct by construction.
# --------------------------------------------------------------------------

FONT = "(effects (font (size 1.27 1.27)))"
FONT_HIDE = "(effects (font (size 1.27 1.27)) hide)"


def _pin(kind, x, y, angle, length, name, number):
    return (
        f'(pin {kind} line (at {x} {y} {angle}) (length {length})\n'
        f'  (name "{name}" {FONT})\n'
        f'  (number "{number}" {FONT})\n'
        f')'
    )


# pin geometry per lib_id, in symbol coordinates: number -> (x, y)
PIN_XY = {
    "Device:R": {"1": (0, 3.81), "2": (0, -3.81)},
    "Device:C": {"1": (0, 3.81), "2": (0, -3.81)},
    "Device:C_Polarized": {"1": (0, 3.81), "2": (0, -3.81)},
    "Connector:Conn_01x02_Pin": {"1": (5.08, 2.54), "2": (5.08, -2.54)},
    "Connector:Conn_01x08_Pin": {
        str(i + 1): (5.08, 8.89 - i * 2.54) for i in range(8)
    },
    "power:GND": {"1": (0, 0)},
    "power:PWR_FLAG": {"1": (0, 0)},
    "power:+3V3": {"1": (0, 0)},
    # multi-unit: unit -> pins
    "Amplifier_Operational:MCP6002": {
        1: {"1": (7.62, 0), "2": (-7.62, -2.54), "3": (-7.62, 2.54)},
        2: {"7": (7.62, 0), "6": (-7.62, -2.54), "5": (-7.62, 2.54)},
        3: {"8": (0, 7.62), "4": (0, -7.62)},
    },
}

LIB_SYMBOLS = f"""
  (symbol "Device:R" (pin_numbers hide) (pin_names (offset 0) hide)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (property "Reference" "R" (at 2.032 0 90) {FONT})
    (property "Value" "R" (at 0 0 90) {FONT})
    (property "Footprint" "" (at -1.778 0 90) {FONT_HIDE})
    (property "Datasheet" "~" (at 0 0 0) {FONT_HIDE})
    (symbol "R_0_1"
      (rectangle (start -1.016 -2.54) (end 1.016 2.54)
        (stroke (width 0.254) (type default)) (fill (type none)))
    )
    (symbol "R_1_1"
      {_pin("passive", 0, 3.81, 270, 1.27, "~", "1")}
      {_pin("passive", 0, -3.81, 90, 1.27, "~", "2")}
    )
  )
  (symbol "Device:C" (pin_numbers hide) (pin_names (offset 0.254) hide)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (property "Reference" "C" (at 0.635 2.54 0) {FONT})
    (property "Value" "C" (at 0.635 -2.54 0) {FONT})
    (property "Footprint" "" (at 0.9652 -3.81 0) {FONT_HIDE})
    (property "Datasheet" "~" (at 0 0 0) {FONT_HIDE})
    (symbol "C_0_1"
      (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762))
        (stroke (width 0.508) (type default)) (fill (type none)))
      (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762))
        (stroke (width 0.508) (type default)) (fill (type none)))
    )
    (symbol "C_1_1"
      {_pin("passive", 0, 3.81, 270, 2.794, "~", "1")}
      {_pin("passive", 0, -3.81, 90, 2.794, "~", "2")}
    )
  )
  (symbol "Device:C_Polarized" (pin_numbers hide) (pin_names (offset 0.254) hide)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (property "Reference" "C" (at 0.635 2.54 0) {FONT})
    (property "Value" "C_Polarized" (at 0.635 -2.54 0) {FONT})
    (property "Footprint" "" (at 0.9652 -3.81 0) {FONT_HIDE})
    (property "Datasheet" "~" (at 0 0 0) {FONT_HIDE})
    (symbol "C_Polarized_0_1"
      (rectangle (start -2.286 0.508) (end 2.286 1.016)
        (stroke (width 0) (type default)) (fill (type outline)))
      (polyline (pts (xy -2.032 -1.016) (xy 2.032 -1.016))
        (stroke (width 0.508) (type default)) (fill (type none)))
      (polyline (pts (xy -1.778 2.286) (xy -1.778 3.302))
        (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy -2.286 2.794) (xy -1.27 2.794))
        (stroke (width 0.254) (type default)) (fill (type none)))
    )
    (symbol "C_Polarized_1_1"
      {_pin("passive", 0, 3.81, 270, 2.794, "~", "1")}
      {_pin("passive", 0, -3.81, 90, 2.794, "~", "2")}
    )
  )
  (symbol "Connector:Conn_01x02_Pin" (pin_names (offset 1.016) hide)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (property "Reference" "J" (at 0 5.08 0) {FONT})
    (property "Value" "Conn_01x02" (at 0 -5.08 0) {FONT})
    (property "Footprint" "" (at 0 0 0) {FONT_HIDE})
    (property "Datasheet" "~" (at 0 0 0) {FONT_HIDE})
    (symbol "Conn_01x02_Pin_1_1"
      (rectangle (start -1.27 3.81) (end 1.27 -3.81)
        (stroke (width 0.254) (type default)) (fill (type none)))
      {_pin("passive", 5.08, 2.54, 180, 2.54, "Pin_1", "1")}
      {_pin("passive", 5.08, -2.54, 180, 2.54, "Pin_2", "2")}
    )
  )
  (symbol "Connector:Conn_01x08_Pin" (pin_names (offset 1.016) hide)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (property "Reference" "J" (at 0 12.7 0) {FONT})
    (property "Value" "Conn_01x08" (at 0 -12.7 0) {FONT})
    (property "Footprint" "" (at 0 0 0) {FONT_HIDE})
    (property "Datasheet" "~" (at 0 0 0) {FONT_HIDE})
    (symbol "Conn_01x08_Pin_1_1"
      (rectangle (start -1.27 10.16) (end 1.27 -10.16)
        (stroke (width 0.254) (type default)) (fill (type none)))
      {chr(10).join(
          "      " + _pin("passive", 5.08, 8.89 - i * 2.54, 180, 2.54,
                          f"Pin_{i + 1}", str(i + 1))
          for i in range(8)
      )}
    )
  )
  (symbol "power:GND" (power) (pin_numbers hide) (pin_names (offset 0) hide)
    (exclude_from_sim yes) (in_bom no) (on_board yes)
    (property "Reference" "#PWR" (at 0 -6.35 0) {FONT_HIDE})
    (property "Value" "GND" (at 0 -3.81 0) {FONT})
    (property "Footprint" "" (at 0 0 0) {FONT_HIDE})
    (property "Datasheet" "" (at 0 0 0) {FONT_HIDE})
    (symbol "GND_0_1"
      (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54)
                     (xy -1.27 -1.27) (xy 0 -1.27))
        (stroke (width 0) (type default)) (fill (type none)))
    )
    (symbol "GND_1_1"
      {_pin("power_in", 0, 0, 270, 0, "GND", "1")}
    )
  )
  (symbol "power:+3V3" (power) (pin_numbers hide) (pin_names (offset 0) hide)
    (exclude_from_sim yes) (in_bom no) (on_board yes)
    (property "Reference" "#PWR" (at 0 -3.81 0) {FONT_HIDE})
    (property "Value" "+3V3" (at 0 3.556 0) {FONT})
    (property "Footprint" "" (at 0 0 0) {FONT_HIDE})
    (property "Datasheet" "" (at 0 0 0) {FONT_HIDE})
    (symbol "+3V3_0_1"
      (polyline (pts (xy -0.762 1.27) (xy 0 2.54) (xy 0.762 1.27))
        (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy 0 0) (xy 0 2.54))
        (stroke (width 0) (type default)) (fill (type none)))
    )
    (symbol "+3V3_1_1"
      {_pin("power_in", 0, 0, 90, 0, "+3V3", "1")}
    )
  )
  (symbol "power:PWR_FLAG" (power) (pin_numbers hide) (pin_names (offset 0) hide)
    (exclude_from_sim yes) (in_bom no) (on_board yes)
    (property "Reference" "#FLG" (at 0 1.905 0) {FONT_HIDE})
    (property "Value" "PWR_FLAG" (at 0 3.81 0) {FONT})
    (property "Footprint" "" (at 0 0 0) {FONT_HIDE})
    (property "Datasheet" "" (at 0 0 0) {FONT_HIDE})
    (symbol "PWR_FLAG_1_1"
      {_pin("power_out", 0, 0, 90, 0, "pwr", "1")}
      (polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54)
                     (xy 1.016 1.905) (xy 0 1.27))
        (stroke (width 0) (type default)) (fill (type none)))
    )
  )
  (symbol "Amplifier_Operational:MCP6002" (pin_names (offset 0.127) hide)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (property "Reference" "U" (at 0 5.08 0) {FONT})
    (property "Value" "MCP6002" (at 0 -5.08 0) {FONT})
    (property "Footprint" "" (at 0 0 0) {FONT_HIDE})
    (property "Datasheet" "http://ww1.microchip.com/downloads/en/DeviceDoc/21733j.pdf" (at 0 0 0) {FONT_HIDE})
    (symbol "MCP6002_1_1"
      (polyline (pts (xy -5.08 5.08) (xy 5.08 0) (xy -5.08 -5.08) (xy -5.08 5.08))
        (stroke (width 0.254) (type default)) (fill (type background)))
      {_pin("output", 7.62, 0, 180, 2.54, "~", "1")}
      {_pin("input", -7.62, -2.54, 0, 2.54, "-", "2")}
      {_pin("input", -7.62, 2.54, 0, 2.54, "+", "3")}
    )
    (symbol "MCP6002_2_1"
      (polyline (pts (xy -5.08 5.08) (xy 5.08 0) (xy -5.08 -5.08) (xy -5.08 5.08))
        (stroke (width 0.254) (type default)) (fill (type background)))
      {_pin("output", 7.62, 0, 180, 2.54, "~", "7")}
      {_pin("input", -7.62, -2.54, 0, 2.54, "-", "6")}
      {_pin("input", -7.62, 2.54, 0, 2.54, "+", "5")}
    )
    (symbol "MCP6002_3_1"
      (rectangle (start -2.54 5.08) (end 2.54 -5.08)
        (stroke (width 0.254) (type default)) (fill (type background)))
      {_pin("power_in", 0, 7.62, 270, 2.54, "VDD", "8")}
      {_pin("power_in", 0, -7.62, 90, 2.54, "VSS", "4")}
    )
  )
"""

# --------------------------------------------------------------------------
# Placement / geometry
# --------------------------------------------------------------------------

items = []          # schematic body s-expressions
_segments = []      # (p1, p2) for the self-check
_pin_pts = []       # every placed pin, absolute
_term_pts = []      # labels: legitimate net terminators


def norm(p):
    """Snap a point to 0.001mm. Coordinates are built by adding 2.54/3.81
    offsets, which drift in binary floating point; two routes to the same
    physical point must compare equal or KiCad sees an open circuit."""
    return (round(p[0] + 0.0, 3), round(p[1] + 0.0, 3))


def pin_xy(lib_id, at, rot, number, unit=1):
    """Symbol pin -> absolute sheet coordinate.

    KiCad's placement transform, with the symbol-space Y flip folded in:
        sheet_x = X + px*cos(t) + py*sin(t)
        sheet_y = Y + px*sin(t) - py*cos(t)
    """
    table = PIN_XY[lib_id]
    if isinstance(next(iter(table.values())), dict):
        table = table[unit]
    px, py = table[number]
    import math
    t = math.radians(rot)
    c, s = round(math.cos(t)), round(math.sin(t))
    return norm((at[0] + px * c + py * s, at[1] + px * s - py * c))


def place(lib_id, ref, value, at, rot=0, unit=1, hide_value=False,
          ref_off=(2.54, -2.54), val_off=(2.54, 2.54), footprint="",
          hide_ref=False):
    props = [
        ("Reference", ref, ref_off, hide_ref),
        ("Value", value, val_off, hide_value),
        ("Footprint", footprint, (0, 0), True),
        ("Datasheet", "~", (0, 0), True),
    ]
    text_angle = (360 - rot) % 360
    prop_txt = "\n".join(
        f'    (property "{k}" "{v}" '
        f'(at {at[0] + o[0]} {at[1] + o[1]} {text_angle}) '
        f'{FONT_HIDE if h else FONT})'
        for k, v, o, h in props
    )
    table = PIN_XY[lib_id]
    if isinstance(next(iter(table.values())), dict):
        numbers = table[unit].keys()
    else:
        numbers = table.keys()
    pins_txt = "\n".join(f'    (pin "{n}" (uuid "{uid("pin")}"))' for n in numbers)
    for n in numbers:
        _pin_pts.append(pin_xy(lib_id, at, rot, n, unit))
    items.append(
        f'  (symbol (lib_id "{lib_id}") (at {at[0]} {at[1]} {rot}) (unit {unit})\n'
        f'    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)\n'
        f'    (uuid "{uid("sym")}")\n'
        f'{prop_txt}\n'
        f'{pins_txt}\n'
        f'    (instances (project "{PROJECT}"\n'
        f'      (path "/{ROOT_UUID}" (reference "{ref}") (unit {unit}))))\n'
        f'  )'
    )
    return lambda number: pin_xy(lib_id, at, rot, number, unit)


def wire(p1, p2):
    p1, p2 = norm(p1), norm(p2)
    if p1 == p2:
        return
    assert p1[0] == p2[0] or p1[1] == p2[1], f"diagonal wire {p1}->{p2}"
    _segments.append((p1, p2))
    items.append(
        f'  (wire (pts (xy {p1[0]} {p1[1]}) (xy {p2[0]} {p2[1]}))\n'
        f'    (stroke (width 0) (type default)) (uuid "{uid("wire")}"))'
    )


def route(*pts):
    for a, b in zip(pts, pts[1:]):
        wire(a, b)


def junction(p):
    p = norm(p)
    items.append(
        f'  (junction (at {p[0]} {p[1]}) (diameter 0) (color 0 0 0 0) '
        f'(uuid "{uid("j")}"))'
    )


def glabel(name, p, rot=0, shape="bidirectional"):
    p = norm(p)
    _term_pts.append(p)
    refs = "${INTERSHEET_REFS}"   # literal, not an f-string field
    items.append(
        f'  (global_label "{name}" (shape {shape}) (at {p[0]} {p[1]} {rot})\n'
        f'    (effects (font (size 1.27 1.27)) (justify left)) (uuid "{uid("gl")}")\n'
        f'    (property "Intersheetrefs" "{refs}" '
        f'(at {p[0]} {p[1]} 0) {FONT_HIDE}))'
    )


def text(s, p, size=1.27, bold=False):
    b = " bold" if bold else ""
    items.append(
        f'  (text "{s}" (at {p[0]} {p[1]} 0)\n'
        f'    (effects (font (size {size} {size}){b}) (justify left bottom))\n'
        f'    (uuid "{uid("t")}"))'
    )


def gnd(p):
    place("power:GND", f"#PWR{next_pwr()}", "GND", p, hide_ref=True,
          ref_off=(0, 0), val_off=(0, 3.81))


def v33(p):
    place("power:+3V3", f"#PWR{next_pwr()}", "+3V3", p, hide_ref=True,
          ref_off=(0, 0), val_off=(0, -3.81))


def pwr_flag(p):
    place("power:PWR_FLAG", f"#FLG{next_pwr()}", "PWR_FLAG", p, hide_ref=True,
          ref_off=(0, 0), val_off=(2.54, -2.54))


_pwr = [0]


def next_pwr():
    _pwr[0] += 1
    return f"{_pwr[0]:02d}"


# --------------------------------------------------------------------------
# One preamp channel
# --------------------------------------------------------------------------

_refs = {"R": 0, "C": 0, "J": 0}


def ref(prefix):
    _refs[prefix] += 1
    return f"{prefix}{_refs[prefix]}"


def channel(ox, oy, idx):
    string, rg, adc = CHANNELS[idx]
    chip = idx // 2          # 0,1,2 -> U1,U2,U3
    unit = (idx % 2) + 1     # 1 or 2
    u_ref = f"U{chip + 1}"

    OUT, NEG, POS = ("1", "2", "3") if unit == 1 else ("7", "6", "5")

    text(f"String {idx + 1} — {string}  ->  {adc}   (gain = 1 + {R_FEEDBACK}/{rg})",
         (ox, oy + 5.08), size=1.778, bold=True)

    # --- op-amp -----------------------------------------------------------
    op = place("Amplifier_Operational:MCP6002", u_ref, "MCP6002",
               (ox + 63.5, oy + 25.4), unit=unit, footprint=FP_DIP8,
               ref_off=(-2.54, -7.62), val_off=(-2.54, 7.62))
    p_pos, p_neg, p_out = op(POS), op(NEG), op(OUT)

    # --- pickup connector -------------------------------------------------
    j = place("Connector:Conn_01x02_Pin", ref("J"), f"Pickup {string}",
              (ox + 7.62, oy + 25.4), footprint=FP_HDR2,
              ref_off=(-2.54, -8.89), val_off=(-2.54, 8.89))
    hot, cold = j("1"), j("2")

    # --- input coupling cap (horizontal) ----------------------------------
    cin = place("Device:C", ref("C"), C_IN, (ox + 27.94, oy + 22.86), rot=90,
                footprint=FP_C_FILM,
                ref_off=(-2.54, -5.08), val_off=(-2.54, 3.81))
    route(hot, cin("2"))
    route(cin("1"), p_pos)

    # --- input bias resistor to VBIAS -------------------------------------
    rb = place("Device:R", ref("R"), R_BIAS_IN, (ox + 40.64, oy + 33.02),
               footprint=FP_R, ref_off=(2.54, -2.54), val_off=(2.54, 2.54))
    tap_bias = (ox + 40.64, oy + 22.86)
    route(tap_bias, rb("1"))
    junction(tap_bias)
    route(rb("2"), (ox + 40.64, oy + 46.99))
    glabel("VBIAS", (ox + 40.64, oy + 46.99), rot=270)

    # --- pickup ground ----------------------------------------------------
    route(cold, (ox + 12.7, oy + 33.02))
    gnd((ox + 12.7, oy + 33.02))

    # --- feedback network -------------------------------------------------
    NEG_X = ox + 50.8
    OUT_X = ox + 71.12
    Y_RF = oy + 38.1
    Y_CF = oy + 45.72

    route(p_neg, (NEG_X, oy + 27.94))

    rf = place("Device:R", ref("R"), R_FEEDBACK, (ox + 54.61, Y_RF), rot=90,
               footprint=FP_R, ref_off=(-2.54, -5.08), val_off=(10.16, -1.27))
    cf = place("Device:C", ref("C"), C_FEEDBACK, (ox + 54.61, Y_CF), rot=90,
               footprint=FP_C_DISC,
               ref_off=(-2.54, -5.08), val_off=(-10.16, 2.54))

    # -IN column, top to bottom
    route((NEG_X, oy + 27.94), (NEG_X, Y_RF))       # rf pin 2 lands here
    route((NEG_X, Y_RF), (NEG_X, Y_CF))             # cf pin 2 lands here
    junction((NEG_X, Y_RF))
    route(rf("1"), (OUT_X, Y_RF))
    route(cf("1"), (OUT_X, Y_CF))

    # OUT column
    route(p_out, (OUT_X, Y_RF))
    route((OUT_X, Y_RF), (OUT_X, Y_CF))
    junction((OUT_X, Y_RF))
    junction(p_out)

    # --- gain resistor to VBIAS -------------------------------------------
    rgr = place("Device:R", ref("R"), rg, (NEG_X, oy + 57.15), footprint=FP_R,
                ref_off=(3.81, -2.54), val_off=(3.81, 2.54))
    route((NEG_X, Y_CF), rgr("1"))
    junction((NEG_X, Y_CF))
    route(rgr("2"), (NEG_X, oy + 68.58))
    glabel("VBIAS", (NEG_X, oy + 68.58), rot=270)

    # --- ADC output -------------------------------------------------------
    route(p_out, (ox + 88.9, oy + 25.4))
    glabel(adc, (ox + 88.9, oy + 25.4), shape="output")


# --------------------------------------------------------------------------
# Power / bias / Teensy block
# --------------------------------------------------------------------------

def power_block(ox, oy):
    text("Bias rail and supply — one divider shared by all six channels",
         (ox, oy), size=1.778, bold=True)

    # --- bias divider -----------------------------------------------------
    x = ox + 15.24
    rtop = place("Device:R", ref("R"), R_DIVIDER, (x, oy + 20.32),
                 footprint=FP_R, ref_off=(2.54, -2.54), val_off=(2.54, 2.54))
    rbot = place("Device:R", ref("R"), R_DIVIDER, (x, oy + 38.1),
                 footprint=FP_R, ref_off=(2.54, -2.54), val_off=(2.54, 2.54))
    route(rtop("1"), (x, oy + 12.7))
    v33((x, oy + 12.7))
    mid = (x, oy + 29.21)
    route(rtop("2"), mid)
    route(mid, rbot("1"))
    junction(mid)
    route(rbot("2"), (x, oy + 45.72))
    gnd((x, oy + 45.72))

    # VBIAS escapes left as a label; bypass caps hang off a bus to the right.
    route((x - 17.78, oy + 29.21), mid)
    glabel("VBIAS", (x - 17.78, oy + 29.21), rot=180)

    taps = [(x + 20.32, C_BIAS_BULK, "Device:C_Polarized"),
            (x + 40.64, C_BYPASS, "Device:C")]
    route(mid, (taps[-1][0], oy + 29.21))          # one bus, no overlaps
    for cx, val, lib in taps:
        if cx != taps[-1][0]:
            junction((cx, oy + 29.21))             # mid-bus tap
        c = place(lib, ref("C"), val, (cx, oy + 35.56),
                  footprint=FP_C_ELEC if lib.endswith("Polarized") else FP_C_DISC,
                  ref_off=(2.54, -2.54), val_off=(2.54, 2.54))
        route((cx, oy + 29.21), c("1"))
        route(c("2"), (cx, oy + 43.18))
        gnd((cx, oy + 43.18))

    # --- three chip power units + decoupling ------------------------------
    text("Op-amp supply pins and decoupling", (ox, oy + 60.96), size=1.778,
         bold=True)
    for i in range(3):
        cx = ox + 15.24 + i * 33.02
        cy = oy + 81.28
        u = place("Amplifier_Operational:MCP6002", f"U{i + 1}", "MCP6002",
                  (cx, cy), unit=3, footprint=FP_DIP8,
                  ref_off=(-10.16, -2.54), val_off=(-10.16, 2.54))
        route(u("8"), (cx, cy - 12.7))
        v33((cx, cy - 12.7))
        route(u("4"), (cx, cy + 12.7))
        gnd((cx, cy + 12.7))

        # decoupling cap alongside
        dx = cx + 15.24
        route((cx, cy - 12.7), (dx, cy - 12.7))
        junction((cx, cy - 12.7))
        c = place("Device:C", ref("C"), C_BYPASS, (dx, cy - 5.08),
                  footprint=FP_C_DISC,
                  ref_off=(2.54, -2.54), val_off=(2.54, 2.54))
        route((dx, cy - 12.7), c("1"))
        route(c("2"), (dx, cy + 2.54))
        gnd((dx, cy + 2.54))

    # --- +3V3 rail bulk bypass --------------------------------------------
    # The three 100n caps above are per-chip decoupling; they handle the fast
    # transients but not the low-frequency sag. The MCP6002 datasheet also
    # wants bulk capacitance on the rail itself. Its own stub to +3V3/GND
    # rather than a tap off a chip, so it stays independent of chip placement.
    bx, by = ox + 108.0, oy + 81.28
    cb = place("Device:C_Polarized", ref("C"), C_RAIL_BULK, (bx, by - 5.08),
               footprint=FP_C_ELEC,
               ref_off=(2.54, -2.54), val_off=(2.54, 2.54))
    route(cb("1"), (bx, by - 12.7))
    v33((bx, by - 12.7))
    route(cb("2"), (bx, by + 2.54))
    gnd((bx, by + 2.54))

    # --- ERC power-source flags -------------------------------------------
    # Supply arrives from the Teensy, not a regulator, so without these ERC
    # reports both rails as undriven. Kept well apart: routing them off
    # adjacent header pins overlapped and shorted the rails.
    text("Rails are sourced from the Teensy", (ox + 86.36, oy + 8.89),
         size=1.27)
    for dy, sym in ((15.24, v33), (33.02, gnd)):
        fx, fy = ox + 88.9, oy + dy
        route((fx, fy), (fx, fy + 7.62))
        pwr_flag((fx, fy))
        sym((fx, fy + 7.62))

    # --- Teensy header ----------------------------------------------------
    text("To Teensy 4.0", (ox + 116.84, oy + 60.96), size=1.778, bold=True)
    hx, hy = ox + 121.92, oy + 81.28
    j = place("Connector:Conn_01x08_Pin", ref("J"), "Teensy", (hx, hy),
              footprint=FP_HDR8,
              ref_off=(-2.54, -15.24), val_off=(-2.54, 15.24))
    # Pin order matches the physical top-to-bottom order of the op-amp
    # outputs on the PCB, which lets the six ADC runs fan into the header
    # without crossing. The connector is a flying lead, so the order is free.
    nets = ["GND", "+3V3", "A1", "A0", "A3", "A2", "A5", "A4"]
    for i, net in enumerate(nets):
        p = j(str(i + 1))
        end = (hx + 20.32, p[1])
        route(p, end)
        if net == "+3V3":
            v33(end)
        elif net == "GND":
            gnd(end)
        else:
            glabel(net, end, shape="input")


# --------------------------------------------------------------------------
# Build the sheet
# --------------------------------------------------------------------------

def build():
    text("MIDI Guitar — 6-channel MCP6002 preamp", (20.32, 15.24), size=3.0,
         bold=True)
    text("Non-inverting, 3.3V single supply from the Teensy. No battery. "
         "See docs/buffer_circuit.md",
         (20.32, 20.32), size=1.778)

    # six channels, 2 columns x 3 rows
    for i in range(6):
        col, row = i % 2, i // 2
        channel(20.32 + col * 106.68, 27.94 + row * 78.74, i)

    power_block(248.92, 27.94)

    body = "\n".join(items)
    return f"""(kicad_sch
  (version 20231120)
  (generator "gen_kicad_schematic.py")
  (generator_version "8.0")
  (uuid "{ROOT_UUID}")
  (paper "A3")
  (title_block
    (title "MIDI Guitar - 6ch MCP6002 Preamp")
    (rev "2")
    (comment 1 "Generated by scripts/gen_kicad_schematic.py - do not hand-edit")
    (comment 2 "Circuit of record: docs/buffer_circuit.md")
  )
  (lib_symbols
{LIB_SYMBOLS}  )
{body}
  (sheet_instances
    (path "/" (page "1"))
  )
)
"""


def selfcheck(txt):
    """Cheap structural checks. Not a substitute for opening it in KiCad."""
    errs = []
    depth = 0
    in_str = False
    prev = ""
    for ch in txt:
        if ch == '"' and prev != "\\":
            in_str = not in_str
        elif not in_str:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth < 0:
                    errs.append("unbalanced ')'")
                    break
        prev = ch
    if depth != 0:
        errs.append(f"paren depth ends at {depth}, expected 0")

    # Every wire endpoint must land on something real: a component pin, a
    # label, another wire's endpoint, or partway along another wire (a tap).
    def on_segment(p, seg):
        (x1, y1), (x2, y2) = seg
        if x1 == x2 == p[0]:
            return min(y1, y2) < p[1] < max(y1, y2)
        if y1 == y2 == p[1]:
            return min(x1, x2) < p[0] < max(x1, x2)
        return False

    pins = set(_pin_pts)
    terms = set(_term_pts)
    ends = {}
    for a, b in _segments:
        for p in (a, b):
            ends[p] = ends.get(p, 0) + 1

    dangling = []
    for p, n in ends.items():
        if n > 1 or p in pins or p in terms:
            continue
        if any(on_segment(p, s) for s in _segments):
            continue
        dangling.append(p)
    if dangling:
        errs.append(
            f"{len(dangling)} dangling wire endpoint(s), e.g. {dangling[:5]}")

    # A pin with nothing attached is almost always a placement mistake.
    touched = set(ends)
    for seg in _segments:
        touched.update(seg)
    floating = [p for p in pins
                if p not in touched and not any(on_segment(p, s)
                                                for s in _segments)]
    if floating:
        errs.append(f"{len(floating)} unconnected pin(s), e.g. {floating[:5]}")
    return errs


PROJECT_FILE = """{
  "board": {
    "design_settings": {
      "rule_severities": {
        "lib_footprint_mismatch": "ignore"
      }
    }
  },
  "erc": {
    "rule_severities": {
      "lib_symbol_mismatch": "ignore",
      "lib_symbol_issues": "ignore"
    }
  },
  "meta": { "filename": "%s.kicad_pro", "version": 1 },
  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] },
  "sheets": [],
  "text_variables": {}
}
""" % PROJECT


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "hardware"
    out.mkdir(exist_ok=True)
    txt = build()
    problems = selfcheck(txt)
    path = out / f"{PROJECT}.kicad_sch"
    path.write_text(txt)
    pro = out / f"{PROJECT}.kicad_pro"
    pro.write_text(PROJECT_FILE)
    print(f"wrote {path} ({len(txt.splitlines())} lines)")
    print(f"wrote {pro}")
    print(f"  symbols placed: {sum(1 for i in items if i.startswith('  (symbol'))}")
    print(f"  wires: {len(_segments)}")
    if problems:
        print("SELF-CHECK FAILED:")
        for e in problems:
            print(f"  - {e}")
        raise SystemExit(1)
    print("  self-check: ok")
