#!/usr/bin/env python3
"""
Generate hardware/midi-guitar-preamp.kicad_pcb from the schematic.

Connectivity comes from KiCad's own netlist exporter, not from re-deriving it
here, so the board and schematic cannot disagree about what connects to what.

    python3 scripts/gen_kicad_pcb.py

Layout strategy
---------------
Each MCP6002 is rotated 90 degrees so its three signal pins per channel
(OUT, -IN, +IN) run left to right instead of stacking 2.54mm apart. Channel A
then fans downward and channel B upward, mirrored, which keeps the feedback
parts right against the op-amp and the high-impedance +IN trace short.

Because every part is through-hole, each pad exists on both layers, so pads
double as layer transitions and almost no vias are needed.

  F.Cu  short per-channel analog nets, and the +3V3 spine
  B.Cu  VBIAS bus and the six ADC runs to the Teensy header
  both  GND pour

The two crossing-prone nets (+3V3 spine and the ADC fan) are deliberately on
opposite layers so they pass over each other instead of colliding.
"""

import os
import shutil
import subprocess
import sys
import uuid as _uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kicad_sexp import Str, dump, kid, kids, parse  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCH = ROOT / "hardware" / "midi-guitar-preamp.kicad_sch"
PCB = ROOT / "hardware" / "midi-guitar-preamp.kicad_pcb"
FPLIB = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints")

TRACK = 0.35          # signal track width, mm
POWER_TRACK = 0.6     # power / bias
CLEARANCE = 0.25

NS = _uuid.UUID("2b7c4e19-5a83-4f60-9d21-7e0c3a5b8d44")
_ctr = {}


def uid(tag):
    n = _ctr.get(tag, 0)
    _ctr[tag] = n + 1
    return str(_uuid.uuid5(NS, f"{tag}:{n}"))


# --------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------

CX = 47.0                      # DIP-8 pin-1 x
SPINE = 61.0                   # VBIAS spine x (B.Cu), clear of every pad
CYS = [48.0, 94.0, 140.0]      # DIP-8 pin-1 y, one per chip
# Teensy header lies along the bottom edge, rotated, so every ADC run
# approaches it from above; that makes the fan-in planar with no vias.
HX, HY = 14.0, 155.0           # header pin 1 (lanes clear the
                               # decoupling GND pads at x=34.3)
BOARD = (6.0, 4.0, 88.0, 160.0)  # x1, y1, x2, y2


def dip_pads(cy):
    """Absolute pad centres for a DIP-8 placed at (CX, cy) rotated 90."""
    return {
        "1": (CX, cy), "2": (CX + 2.54, cy),
        "3": (CX + 5.08, cy), "4": (CX + 7.62, cy),
        "8": (CX, cy - 7.62), "7": (CX + 2.54, cy - 7.62),
        "6": (CX + 5.08, cy - 7.62), "5": (CX + 7.62, cy - 7.62),
    }


_PITCH_CACHE = {}


def fp_pad_vec(lib_id):
    """Local vector from pad 1 to pad 2 of a 2-pad footprint."""
    if lib_id in _PITCH_CACHE:
        return _PITCH_CACHE[lib_id]
    lib, name = lib_id.split(":")
    fp = parse((FPLIB / f"{lib}.pretty" / f"{name}.kicad_mod").read_text())
    at = {}
    for pad in kids(fp, "pad"):
        a = kid(pad, "at")
        at[str(pad[1])] = (float(a[1]), float(a[2]))
    v = (at["2"][0] - at["1"][0], at["2"][1] - at["1"][1])
    _PITCH_CACHE[lib_id] = v
    return v


def rot_xy(p, deg):
    """KiCad footprint rotation: (x,y) -> (x cos + y sin, -x sin + y cos)."""
    import math
    t = math.radians(deg)
    c, s = round(math.cos(t)), round(math.sin(t))
    return (p[0] * c + p[1] * s, -p[0] * s + p[1] * c)


# --------------------------------------------------------------------------
# Netlist (from KiCad)
# --------------------------------------------------------------------------

def load_netlist():
    cli = shutil.which("kicad-cli") or \
        "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
    if not Path(cli).exists():
        sys.exit("kicad-cli not found; install KiCad or put it on PATH")
    out = Path(os.environ.get("TMPDIR", "/tmp")) / "mgp_netlist.net"
    subprocess.run([cli, "sch", "export", "netlist", "--format", "kicadsexpr",
                    "-o", str(out), str(SCH)],
                   check=True, capture_output=True)
    tree = parse(out.read_text())

    footprints, values = {}, {}
    for c in kids(kid(tree, "components"), "comp"):
        ref = str(kid(c, "ref")[1])
        values[ref] = str(kid(c, "value")[1])
        fp = kid(c, "footprint")
        if fp:
            footprints[ref] = str(fp[1])

    pin_net, net_names = {}, []
    for n in kids(kid(tree, "nets"), "net"):
        name = str(kid(n, "name")[1])
        net_names.append(name)
        for nd in kids(n, "node"):
            pin_net[(str(kid(nd, "ref")[1]), str(kid(nd, "pin")[1]))] = name
    return footprints, values, pin_net, net_names


# --------------------------------------------------------------------------
# Board assembly
# --------------------------------------------------------------------------

class Board:
    def __init__(self, net_names):
        self.nets = {"": 0}
        for i, n in enumerate(sorted(set(net_names)), start=1):
            self.nets[n] = i
        self.items = []
        self.placed = {}     # ref -> (pos, rot)

    def netcode(self, name):
        return self.nets.get(name, 0)

    # -- placement ---------------------------------------------------------
    def place(self, ref, lib_id, pos, rot, value, pin_net, front=True):
        lib, name = lib_id.split(":")
        path = FPLIB / f"{lib}.pretty" / f"{name}.kicad_mod"
        if not path.exists():
            sys.exit(f"missing footprint {lib_id}")
        fp = parse(path.read_text())
        fp[0] = "footprint"
        fp[1] = Str(lib_id)
        # strip file-level tokens that are illegal inside a board
        fp[:] = [c for c in fp
                 if not (isinstance(c, list) and c and c[0] in
                         ("version", "generator", "generator_version",
                          "at", "uuid"))]
        fp.insert(2, ["at", fmt(pos[0]), fmt(pos[1])] +
                  ([fmt(rot)] if rot else []))
        fp.insert(3, ["uuid", Str(uid("fp"))])

        for prop in kids(fp, "property"):
            if prop[1] == "Reference":
                prop[2] = Str(ref)
                font = kid(kid(prop, "effects") or ["effects"], "font")
                if font:
                    font[:] = ["font", ["size", "0.9", "0.9"],
                               ["thickness", "0.15"]]
            elif prop[1] == "Value":
                prop[2] = Str(value)

        for pad in kids(fp, "pad"):
            net = pin_net.get((ref, str(pad[1])))
            if net:
                pad.append(["net", self.netcode(net), Str(net)])
        self.items.append(fp)
        self.placed[ref] = (pos, rot)

    def place2(self, ref, lib_id, p_near, direction, near_net, value,
               pin_net):
        """Place a 2-pad part so the pad carrying `near_net` sits at p_near
        and the other pad lies `direction` away.

        Which schematic pin is on which net is read from the netlist rather
        than assumed, and the spacing comes from the footprint itself.
        """
        v = fp_pad_vec(lib_id)
        pitch = (v[0] ** 2 + v[1] ** 2) ** 0.5
        far = (p_near[0] + direction[0] * pitch,
               p_near[1] + direction[1] * pitch)
        theta = None
        for t in (0, 90, 180, 270):
            r = rot_xy(v, t)
            if (abs(r[0] - direction[0] * pitch) < 1e-6 and
                    abs(r[1] - direction[1] * pitch) < 1e-6):
                theta = t
                break
        if theta is None:
            sys.exit(f"{ref}: cannot orient {lib_id} along {direction}")

        if pin_net.get((ref, "1")) == near_net:
            pos, rot = p_near, theta
        elif pin_net.get((ref, "2")) == near_net:
            pos, rot = far, (theta + 180) % 360
        else:
            sys.exit(f"{ref}: neither pin is on {near_net}")
        self.place(ref, lib_id, pos, rot, value, pin_net)
        return p_near, far

    # -- copper ------------------------------------------------------------
    def track(self, pts, net, layer="F.Cu", width=TRACK):
        code = self.netcode(net)
        for a, b in zip(pts, pts[1:]):
            if a == b:
                continue
            self.items.append([
                "segment",
                ["start", fmt(a[0]), fmt(a[1])],
                ["end", fmt(b[0]), fmt(b[1])],
                ["width", fmt(width)], ["layer", Str(layer)],
                ["net", code], ["uuid", Str(uid("seg"))]])

    def via(self, p, net):
        self.items.append([
            "via", ["at", fmt(p[0]), fmt(p[1])],
            ["size", "0.8"], ["drill", "0.4"],
            ["layers", Str("F.Cu"), Str("B.Cu")],
            ["net", self.netcode(net)], ["uuid", Str(uid("via"))]])

    def edge(self, a, b):
        self.items.append([
            "gr_line", ["start", fmt(a[0]), fmt(a[1])],
            ["end", fmt(b[0]), fmt(b[1])],
            ["stroke", ["width", "0.1"], ["type", "default"]],
            ["layer", Str("Edge.Cuts")], ["uuid", Str(uid("edge"))]])

    def text(self, s, p, layer="F.SilkS", size=1.5):
        self.items.append([
            "gr_text", Str(s), ["at", fmt(p[0]), fmt(p[1]), "0"],
            ["layer", Str(layer)], ["uuid", Str(uid("txt"))],
            ["effects", ["font", ["size", fmt(size), fmt(size)],
                         ["thickness", "0.25"]],
             ["justify", "left"] + (["mirror"] if layer.startswith("B.")
                                    else [])]])

    def zone(self, layer, poly, net="GND"):
        pts = ["pts"] + [["xy", fmt(x), fmt(y)] for x, y in poly]
        self.items.append([
            "zone", ["net", self.netcode(net)], ["net_name", Str(net)],
            ["layer", Str(layer)], ["uuid", Str(uid("zone"))],
            ["hatch", "edge", "0.5"],
            ["connect_pads", ["clearance", fmt(CLEARANCE)]],
            ["min_thickness", "0.25"], ["filled_areas_thickness", "no"],
            ["fill", "yes", ["thermal_gap", "0.5"],
             ["thermal_bridge_width", "0.5"]],
            ["polygon", pts]])


def fmt(v):
    return f"{round(float(v), 4):g}"


# --------------------------------------------------------------------------
# ADC fan-in: pick vertical lanes that produce no crossings
# --------------------------------------------------------------------------

def segs_cross(a, b):
    """Axis-aligned segment intersection, endpoints included."""
    def span(s, i):
        return (min(s[0][i], s[1][i]), max(s[0][i], s[1][i]))
    ax, ay = span(a, 0), span(a, 1)
    bx, by = span(b, 0), span(b, 1)
    return (ax[0] <= bx[1] and bx[0] <= ax[1] and
            ay[0] <= by[1] and by[0] <= ay[1])


def route_fan(sources, pins, lane_xs):
    """sources/pins: list of (x, y) in matching order. Try lane permutations
    until no two traces touch. Returns list of point-lists, or None."""
    from itertools import permutations
    n = len(sources)
    for perm in permutations(range(n)):
        lanes = [lane_xs[perm[k]] for k in range(n)]
        paths = []
        for k in range(n):
            sx, sy = sources[k]
            px, py = pins[k]
            lx = lanes[k]
            paths.append([(sx, sy), (lx, sy), (lx, py), (px, py)])
        ok = True
        for i in range(n):
            si = list(zip(paths[i], paths[i][1:]))
            for j in range(i + 1, n):
                sj = list(zip(paths[j], paths[j][1:]))
                if any(segs_cross(a, b) for a in si for b in sj):
                    ok = False
                    break
            if not ok:
                break
        if ok:
            return paths
    return None


# --------------------------------------------------------------------------

def build():
    footprints, values, pin_net, net_names = load_netlist()
    b = Board(net_names)

    def net_of(ref, pin):
        return pin_net.get((ref, str(pin)), "")

    # Map schematic refs to physical roles by walking the netlist: for each
    # op-amp channel find which parts sit on its OUT / -IN / +IN nets.
    CH = [("U1", "1", "2", "3"), ("U1", "7", "6", "5"),
          ("U2", "1", "2", "3"), ("U2", "7", "6", "5"),
          ("U3", "1", "2", "3"), ("U3", "7", "6", "5")]

    def parts_on(net, kind):
        out = []
        for (ref, pin), n in pin_net.items():
            if n == net and ref[0] == kind and not ref.startswith("#"):
                out.append(ref)
        return sorted(set(out))

    layout_log = []
    adc_sources, adc_pins, adc_nets = [], [], []

    for chip, cy in enumerate(CYS):
        u = f"U{chip + 1}"
        b.place(u, footprints[u], (CX, cy), 90, values[u], pin_net)

    for idx, (u, OUT, NEG, POS) in enumerate(CH):
        chip = idx // 2
        cy = CYS[chip]
        pads = dip_pads(cy)
        side = 1 if idx % 2 == 0 else -1        # A fans down, B fans up
        base = cy if side == 1 else cy - 7.62

        n_out, n_neg, n_pos = net_of(u, OUT), net_of(u, NEG), net_of(u, POS)

        # identify this channel's discretes
        rs_neg = parts_on(n_neg, "R")           # Rf and Rg
        cs_neg = parts_on(n_neg, "C")           # Cf
        rf = [r for r in rs_neg if r in parts_on(n_out, "R")][0]
        rg = [r for r in rs_neg if r != rf][0]
        cf = cs_neg[0]
        rbias = parts_on(n_pos, "R")[0]
        cin = parts_on(n_pos, "C")[0]
        n_in = [n for (ref, pin), n in pin_net.items()
                if ref == cin and n != n_pos][0]
        jack = parts_on(n_in, "J")[0]

        # ---- placement + routing (channel B is the y-mirror of A) -------
        # side = +1 fans down, -1 fans up. NEG is the middle pin, so the
        # feedback parts hang straight off it and nothing has to cross.
        pads_out, pads_neg, pads_pos = pads[OUT], pads[NEG], pads[POS]
        d_down = (0, side)
        d_left, d_right = (-1, 0), (1, 0)

        def Y(dy):
            return base + side * dy

        # feedback pair: NEG end anchored under the -IN pin, running outward
        rf_neg, rf_out = b.place2(rf, footprints[rf],
                                  (pads_neg[0], Y(7.62)), d_left, n_neg,
                                  values[rf], pin_net)
        cf_neg, cf_out = b.place2(cf, footprints[cf],
                                  (pads_neg[0], Y(12.7)), d_left, n_neg,
                                  values[cf], pin_net)
        rg_neg, rg_vb = b.place2(rg, footprints[rg],
                                 (pads_neg[0], Y(16.5)), d_right, n_neg,
                                 values[rg], pin_net)
        rb_pos, rb_vb = b.place2(rbias, footprints[rbias],
                                 (CX + 12.7, Y(3.81)), d_down, n_pos,
                                 values[rbias], pin_net)
        ci_pos, ci_in = b.place2(cin, footprints[cin],
                                 (CX + 17.78, Y(3.81)), d_right, n_pos,
                                 values[cin], pin_net)
        j_in, _ = b.place2(jack, footprints[jack],
                           (CX + 27.94, Y(3.81)), d_down, n_in,
                           values[jack], pin_net)

        # OUT: hop clear of the pin row, then out to the feedback parts
        b.track([pads_out, (pads_out[0], Y(3.81)), (rf_out[0], Y(3.81)),
                 rf_out], n_out)
        b.track([rf_out, (rf_out[0], Y(12.7)), cf_out], n_out)
        # NEG: one straight run down the middle pin's column
        b.track([pads_neg, rf_neg, cf_neg, rg_neg], n_neg)
        # POS: out to the bias resistor and the input cap
        b.track([pads_pos, (pads_pos[0], Y(3.81)), rb_pos, ci_pos], n_pos)
        b.track([ci_in, j_in], n_in)
        # VBIAS hop on B.Cu (through-hole pads are the layer transition)
        b.track([rg_vb, (CX + 12.7, rg_vb[1]), rb_vb], "VBIAS",
                layer="B.Cu", width=POWER_TRACK)

        # ADC take-off: channel A leaves from its pad, channel B from the
        # jog above the pin row (its pad row is blocked by VDD)
        if side == 1:
            adc_sources.append(pads_out)
        else:
            hop = (pads_out[0], Y(3.81))
            b.via(hop, n_out)
            adc_sources.append(hop)
        adc_nets.append(n_out)
        layout_log.append(f"{n_out}: U{chip+1} pin {OUT}, Rf={rf} Cf={cf} "
                          f"Rg={rg} Rbias={rbias} Cin={cin} J={jack}")

    # ---- decoupling + 3V3 spine -----------------------------------------
    # Split by value, not by slicing: the rail also carries a bulk
    # electrolytic, and indexing the first three of a sorted list would
    # silently drop whichever cap sorted last.
    caps_3v3 = sorted(parts_on("+3V3", "C"))
    dec = [c for c in caps_3v3 if values[c] == "100n"]
    rail_bulk = [c for c in caps_3v3 if c not in dec]
    if len(dec) != len(CYS):
        sys.exit(f"expected {len(CYS)} 100n decoupling caps on +3V3, "
                 f"got {[(c, values[c]) for c in dec]}")
    if len(rail_bulk) != 1:
        sys.exit(f"expected 1 bulk cap on +3V3, got "
                 f"{[(c, values[c]) for c in rail_bulk]}")
    for chip, cy in enumerate(CYS):
        c = dec[chip]
        b.place(c, footprints[c], (CX - 7.7, cy - 7.62), 180, values[c],
                pin_net)
        b.track([(CX, cy - 7.62), (CX - 7.7, cy - 7.62)], "+3V3",
                width=POWER_TRACK)
    b.track([(CX - 7.7, CYS[0] - 7.62), (CX - 7.7, CYS[2] - 7.62)],
            "+3V3", width=POWER_TRACK)

    # ---- bias divider + bulk caps (top of board) ------------------------
    # Everything that touches VBIAS hangs off the spine with its VBIAS pad
    # sitting on the spine itself, so no extra jumper traces are needed.
    div = [r for r in parts_on("VBIAS", "R") if values[r] == "10k"]
    rtop = [r for r in div
            if "+3V3" in (net_of(r, "1"), net_of(r, "2"))][0]
    rbot = [r for r in div if r != rtop][0]
    _, r19_v3 = b.place2(rtop, footprints[rtop], (SPINE, 8.0), (-1, 0),
                         "VBIAS", values[rtop], pin_net)
    b.place2(rbot, footprints[rbot], (SPINE, 12.0), (1, 0), "VBIAS",
             values[rbot], pin_net)
    for k, c in enumerate(sorted(parts_on("VBIAS", "C"))):
        y = 18.0 + k * 7.5
        b.place2(c, footprints[c], (SPINE + 7.0, y), (1, 0), "VBIAS",
                 values[c], pin_net)
        b.track([(SPINE, y), (SPINE + 7.0, y)], "VBIAS",
                layer="B.Cu", width=POWER_TRACK)

    # +3V3: divider top -> spine -> each decoupling cap
    b.track([r19_v3, (CX - 7.7, r19_v3[1]), (CX - 7.7, CYS[0] - 7.62)],
            "+3V3", width=POWER_TRACK)
    # VBIAS spine down the board on B.Cu
    b.track([(SPINE, 8.0), (SPINE, CYS[2] + 3.81 + 7.62)], "VBIAS",
            layer="B.Cu", width=POWER_TRACK)
    for cy in CYS:
        for sd in (1, -1):
            bs = cy if sd == 1 else cy - 7.62
            y = bs + sd * (3.81 + 7.62)
            b.track([(SPINE, y), (CX + 12.7, y)], "VBIAS",
                    layer="B.Cu", width=POWER_TRACK)

    # ---- Teensy header + ADC fan ----------------------------------------
    hdr = [r for r in footprints
           if footprints[r].endswith("1x08_P2.54mm_Vertical")][0]
    b.place(hdr, footprints[hdr], (HX, HY), 90, values[hdr], pin_net)
    # rot 90 lays pin n at x = HX + (n-1)*2.54
    hdr_pin_x = {str(i + 1): HX + i * 2.54 for i in range(8)}

    # +3V3 down to the header, jogging above the pad row so it never shares
    # a lane with an ADC run
    px3 = hdr_pin_x[[p for p in hdr_pin_x if net_of(hdr, p) == "+3V3"][0]]
    b.track([(CX - 7.7, CYS[2] - 7.62), (CX - 7.7, HY - 7.0),
             (px3, HY - 7.0), (px3, HY)], "+3V3", width=POWER_TRACK)

    # Bulk cap sits on that run, close to where +3V3 actually enters the
    # board from the Teensy — bulk belongs at the supply entry, not out at
    # the far end past the three chips. It hangs left off the spine so its
    # GND pad reaches the pour without crossing the ADC fan, which owns
    # every lane below x = 32.
    cbulk = rail_bulk[0]
    b.place2(cbulk, footprints[cbulk], (CX - 7.7, 144.0), (-1, 0),
             "+3V3", values[cbulk], pin_net)

    # Each ADC: horizontal at its source y, then straight down to its pin.
    paths, order = [], []
    for k, net in enumerate(adc_nets):
        pin = [p for p in hdr_pin_x if net_of(hdr, p) == net][0]
        px = hdr_pin_x[pin]
        sx, sy = adc_sources[k]
        paths.append([(sx, sy), (px, sy), (px, HY)])
        order.append((net, pin, px, sy))

    bad = []
    for i in range(len(paths)):
        si = list(zip(paths[i], paths[i][1:]))
        for j in range(i + 1, len(paths)):
            sj = list(zip(paths[j], paths[j][1:]))
            if any(segs_cross(a, b_) for a in si for b_ in sj):
                bad.append((adc_nets[i], adc_nets[j]))
    if bad:
        print(f"WARNING: ADC fan crossings: {bad}")
    for net, path in zip(adc_nets, paths):
        b.track(path, net, layer="B.Cu")
    for net, pin, px, _ in order:
        b.text(net, (px, HY - 3.2), layer="B.SilkS", size=1.0)

    # ---- outline, pours, silkscreen -------------------------------------
    x1, y1, x2, y2 = BOARD
    b.edge((x1, y1), (x2, y1))
    b.edge((x2, y1), (x2, y2))
    b.edge((x2, y2), (x1, y2))
    b.edge((x1, y2), (x1, y1))
    poly = [(x1 + 0.3, y1 + 0.3), (x2 - 0.3, y1 + 0.3),
            (x2 - 0.3, y2 - 0.3), (x1 + 0.3, y2 - 0.3)]
    b.zone("F.Cu", poly)
    b.zone("B.Cu", poly)
    b.text("MIDI Guitar 6ch MCP6002 preamp", (x1 + 3, y1 + 4.5),
           size=1.4)
    b.text("pickup headers", (x2 - 26, y2 - 6), size=1.2)
    b.text("Teensy ->", (x1 + 3, HY - 9), size=1.2)

    for line in layout_log:
        print("  " + line)
    return b


LAYERS = """  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )"""


def emit(b):
    nets = "\n".join(f'  (net {c} "{n}")'
                     for n, c in sorted(b.nets.items(), key=lambda kv: kv[1]))
    body = "\n".join(dump(i, 1) for i in b.items)
    return f"""(kicad_pcb
  (version 20240108)
  (generator "gen_kicad_pcb.py")
  (generator_version "8.0")
  (general
    (thickness 1.6)
    (legacy_teardrops no)
  )
  (paper "A3")
{LAYERS}
  (setup
    (pad_to_mask_clearance 0)
    (allow_soldermask_bridges_in_footprints no)
    (pcbplotparams
      (layerselection 0x00000000_00000000_55555555_5755f5ff)
      (plot_on_all_layers_selection 0x0000000_00000000_00000000_00000000)
      (disableapertmacros no) (usegerberextensions no) (usegerberattributes yes)
      (usegerberadvancedattributes yes) (creategerberjobfile yes)
      (dashed_line_dash_ratio 12) (dashed_line_gap_ratio 3)
      (svgprecision 4) (plotframeref no) (mode 1) (useauxorigin no)
      (dxfpolygonmode yes) (dxfimperialunits yes) (dxfusepcbnewfont yes)
      (psnegative no) (psa4output no) (plotreference yes) (plotvalue yes)
      (plotfptext yes) (plotinvisibletext no) (sketchpadsonfab no)
      (subtractmaskfromsilk no) (outputformat 1) (mirror no) (drillshape 1)
      (scaleselection 1) (outputdirectory "")
    )
  )
{nets}
{body}
)
"""


def fill_zones():
    """Zones are written empty; KiCad computes the fill. Do it here so the
    file on disk is complete and GND connectivity holds without opening the
    GUI first."""
    cli = shutil.which("kicad-cli") or \
        "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
    r = subprocess.run([cli, "pcb", "drc", "--refill-zones", "--save-board",
                        "--format", "report", "-o", os.devnull, str(PCB)],
                       capture_output=True, text=True)
    return "unconnected items" in (r.stdout or "")


if __name__ == "__main__":
    board = build()
    PCB.write_text(emit(board))
    x1, y1, x2, y2 = BOARD
    print(f"wrote {PCB}")
    print(f"  footprints: {len(board.placed)}   nets: {len(board.nets) - 1}")
    print(f"  board: {x2 - x1:.0f} x {y2 - y1:.0f} mm, 2 layers")
    print("  zones filled" if fill_zones() else "  WARNING: zone fill failed")
