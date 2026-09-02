#!/usr/bin/env python3
"""Print a full-size paper template of the Iceman body outline on Letter paper.

Pipeline
  1. OpenSCAD renders the 2D outline from body/iceman.scad (so the corner
     softening is exactly the model's, not a reimplementation) and exports SVG.
  2. That SVG is parsed back into polylines, at 1 SVG unit = 1 mm.
  3. The outline is tiled across Letter sheets with an overlap band, and a
     multi-page PDF is written by hand (no third-party deps).

Print the PDF at 100% / "Actual size" -- NOT "Fit to page". Every sheet carries
a 100 mm ruler in the footer; measure it before cutting anything.

    python3 scripts/gen_body_template.py
    python3 scripts/gen_body_template.py --soften 20 --overlap 20
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile

MM = 72.0 / 25.4                      # mm -> PDF points
OPENSCAD = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAPER = {                             # (width_mm, height_mm) portrait
    "letter": (215.9, 279.4),
    "a4": (210.0, 297.0),
}


# --------------------------------------------------------------------------
# 1. outline from OpenSCAD
# --------------------------------------------------------------------------

def export_outline_svg(scad_path, soften, fn, out_svg):
    """Render the 2D outline via OpenSCAD and return the SVG path."""
    if not os.path.exists(OPENSCAD):
        sys.exit(f"OpenSCAD not found at {OPENSCAD}")

    # `use` imports the modules but not the top-level linear_extrude, so we get
    # the flat 2D shape. soften/$fn come in via -D.
    wrapper = (
        f'use <{scad_path}>\n'
        'soften = 8;\n'
        '$fn = 64;\n'
        'soften_corners(soften) iceman_outline();\n'
    )
    with tempfile.NamedTemporaryFile("w", suffix=".scad", delete=False) as fh:
        fh.write(wrapper)
        wrapper_path = fh.name
    try:
        subprocess.run(
            [OPENSCAD, "-o", out_svg,
             "-D", f"soften={soften}", "-D", f"$fn={fn}", wrapper_path],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as exc:
        sys.exit(f"OpenSCAD failed:\n{exc.stderr}")
    finally:
        os.unlink(wrapper_path)
    return out_svg


def parse_svg_paths(svg_path):
    """OpenSCAD emits only M/L commands. Return [[(x, y), ...], ...] in mm,
    y flipped back to the usual maths convention (up is +)."""
    with open(svg_path) as fh:
        svg = fh.read()

    loops = []
    for d in re.findall(r'<path[^>]*\sd="([^"]*)"', svg, re.S):
        current = []
        for cmd, args in re.findall(r'([MLZmlz])([^MLZmlz]*)', d):
            nums = [float(n) for n in re.findall(r'-?\d+\.?\d*(?:[eE][-+]?\d+)?', args)]
            if cmd in "Mm":
                if len(current) > 2:
                    loops.append(current)
                current = []
            for i in range(0, len(nums) - 1, 2):
                current.append((nums[i], -nums[i + 1]))   # un-flip Y
        if len(current) > 2:
            loops.append(current)
    if not loops:
        sys.exit("No path data found in the exported SVG.")
    return loops


# --------------------------------------------------------------------------
# 2. minimal PDF writer
# --------------------------------------------------------------------------

class Pdf:
    def __init__(self, page_w_mm, page_h_mm):
        self.w, self.h = page_w_mm * MM, page_h_mm * MM
        self.pages = []          # list of content-stream strings

    def add_page(self, content):
        self.pages.append(content)

    def write(self, path):
        objs = {}                # number -> bytes body
        n_pages = len(self.pages)
        font_id = 3
        first = 4

        kids = " ".join(f"{first + 2 * i} 0 R" for i in range(n_pages))
        objs[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
        objs[2] = (f"<< /Type /Pages /Count {n_pages} /Kids [{kids}] >>").encode()
        objs[font_id] = (b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
                         b"/Encoding /WinAnsiEncoding >>")

        for i, content in enumerate(self.pages):
            pid, cid = first + 2 * i, first + 2 * i + 1
            objs[pid] = (
                f"<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 {self.w:.2f} {self.h:.2f}] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
                f"/Contents {cid} 0 R >>"
            ).encode()
            data = content.encode("latin-1")
            objs[cid] = (f"<< /Length {len(data)} >>\nstream\n".encode()
                         + data + b"\nendstream")

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = {}
        for num in sorted(objs):
            offsets[num] = len(out)
            out += f"{num} 0 obj\n".encode() + objs[num] + b"\nendobj\n"

        xref_at = len(out)
        top = max(objs) + 1
        out += f"xref\n0 {top}\n".encode()
        out += b"0000000000 65535 f \n"
        for num in range(1, top):
            out += f"{offsets[num]:010d} 00000 n \n".encode()
        out += (f"trailer\n<< /Size {top} /Root 1 0 R >>\n"
                f"startxref\n{xref_at}\n%%EOF\n").encode()

        with open(path, "wb") as fh:
            fh.write(out)


# --------------------------------------------------------------------------
# 3. drawing helpers (all take/emit mm, converted at the boundary)
# --------------------------------------------------------------------------

def line(x1, y1, x2, y2):
    return f"{x1*MM:.2f} {y1*MM:.2f} m {x2*MM:.2f} {y2*MM:.2f} l S\n"


def text(x, y, s, size=8):
    s = s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
    return f"BT /F1 {size} Tf {x*MM:.2f} {y*MM:.2f} Td ({s}) Tj ET\n"


def polyline(pts, close=True):
    if not pts:
        return ""
    out = f"{pts[0][0]*MM:.2f} {pts[0][1]*MM:.2f} m\n"
    for x, y in pts[1:]:
        out += f"{x*MM:.2f} {y*MM:.2f} l\n"
    return out + ("h S\n" if close else "S\n")


def cross(x, y, size=4.0):
    return (line(x - size, y, x + size, y) + line(x, y - size, x, y + size)
            + f"{(x)*MM:.2f} {(y)*MM:.2f} m {(x)*MM:.2f} {(y)*MM:.2f} l S\n")


def ruler(x, y, length=100.0):
    """A length-mm ruler with 10 mm ticks, drawn from (x, y) rightwards."""
    out = line(x, y, x + length, y)
    for i in range(0, int(length) + 1, 10):
        h = 3.0 if i % 50 == 0 else 1.8
        out += line(x + i, y, x + i, y + h)
    out += text(x, y + 4.5, f"{length:.0f} mm reference - measure before cutting", 7)
    return out


# --------------------------------------------------------------------------
# 4. tiling
# --------------------------------------------------------------------------

def build(loops, args):
    paper_w, paper_h = PAPER[args.paper]
    if args.landscape:
        paper_w, paper_h = paper_h, paper_w

    m = args.margin
    footer = 16.0
    usable_w = paper_w - 2 * m
    usable_h = paper_h - 2 * m - footer          # tiled content area
    pitch_x = usable_w - args.overlap
    pitch_y = usable_h - args.overlap
    if pitch_x <= 0 or pitch_y <= 0:
        sys.exit("Overlap is larger than the printable area.")

    xs = [p[0] for lp in loops for p in lp]
    ys = [p[1] for lp in loops for p in lp]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    bw, bh = maxx - minx, maxy - miny

    cols = max(1, -(-int(round((bw - usable_w) * 1000)) // int(pitch_x * 1000)) + 1) \
        if bw > usable_w else 1
    rows = max(1, -(-int(round((bh - usable_h) * 1000)) // int(pitch_y * 1000)) + 1) \
        if bh > usable_h else 1
    while (cols - 1) * pitch_x + usable_w < bw:
        cols += 1
    while (rows - 1) * pitch_y + usable_h < bh:
        rows += 1

    sheet_w = (cols - 1) * pitch_x + usable_w
    sheet_h = (rows - 1) * pitch_y + usable_h
    # model -> sheet space, centred
    ox = (sheet_w - bw) / 2 - minx
    oy = (sheet_h - bh) / 2 - miny
    sloops = [[(x + ox, y + oy) for x, y in lp] for lp in loops]
    centre_x = 0.0 + ox                          # model X=0 is the body centreline

    pdf = Pdf(paper_w, paper_h)
    label = lambda r, c: f"R{r+1}C{c+1}"

    # ---- overview page -------------------------------------------------
    c = "0.2 w 0 G\n"
    notes_h = 36.0                                # reserved instruction band
    head_h = 16.0                                 # reserved title band
    map_h = usable_h - notes_h - head_h
    fit = min(usable_w / sheet_w, map_h / sheet_h)
    px0 = m + (usable_w - sheet_w * fit) / 2
    py0 = m + footer + notes_h + (map_h - sheet_h * fit) / 2
    S = lambda x, y: (px0 + x * fit, py0 + y * fit)

    c += "0.8 w\n"
    for lp in sloops:
        c += polyline([S(x, y) for x, y in lp])
    c += "0.3 w 0.6 G [2 2] 0 d\n"
    for r in range(rows):
        for col in range(cols):
            x0, y0 = col * pitch_x, (rows - 1 - r) * pitch_y
            a, b = S(x0, y0)
            c += (f"{a*MM:.2f} {b*MM:.2f} {usable_w*fit*MM:.2f} "
                  f"{usable_h*fit*MM:.2f} re S\n")
    c += "[] 0 d 0 G\n"
    for r in range(rows):
        for col in range(cols):
            a, b = S(col * pitch_x + usable_w / 2, (rows - 1 - r) * pitch_y + usable_h / 2)
            c += text(a - 6, b, label(r, col), 11)
    c += text(m, paper_h - m - 4, "ICEMAN BODY TEMPLATE - assembly map", 13)
    c += text(m, paper_h - m - 12,
              f"{bw:.1f} x {bh:.1f} mm outline  |  soften r={args.soften} mm  "
              f"|  {rows} x {cols} sheets, {args.overlap:.0f} mm overlap", 8)
    y = m + footer + 4
    for s_ in (
        "1. Print at 100% / Actual Size. Turn OFF 'fit to page' and 'shrink oversized pages'.",
        "2. Check the 100 mm ruler in every footer with a steel rule. If it is off, the print is off - fix it, do not compensate.",
        "3. Trim each sheet along the dashed line on its RIGHT and BOTTOM edges only.",
        "4. Lay sheets out per this map. Slide until the + crosses in the overlap sit exactly on top of each other, then tape.",
        "5. The dash-dot line is the body centreline. It must be dead straight across the whole assembly - that is your check.",
    )[::-1]:
        c += text(m, y, s_, 8)
        y += 5.6
    c += ruler(m, m + 4)
    pdf.add_page(c)

    # ---- tile pages ----------------------------------------------------
    for r in range(rows):
        for col in range(cols):
            x0, y0 = col * pitch_x, (rows - 1 - r) * pitch_y
            P = lambda x, y: (m + (x - x0), m + footer + (y - y0))

            c = "0.2 w 0 G\n"
            c += (f"q {m*MM:.2f} {(m+footer)*MM:.2f} {usable_w*MM:.2f} "
                  f"{usable_h*MM:.2f} re W n\n")

            # centreline: dash-dot, the straightness check across the assembly
            c += "0.35 w 0.45 G [6 2 1 2] 0 d\n"
            c += line(*P(centre_x, y0), *P(centre_x, y0 + usable_h))
            c += "[] 0 d 0 G\n"
            if x0 + 4 <= centre_x <= x0 + usable_w - 4:
                c += text(*P(centre_x + 2.0, y0 + usable_h - 30), "CENTRELINE", 6)
            c += "0.9 w\n"

            for lp in sloops:
                c += polyline([P(x, y) for x, y in lp])

            # overlap bands + registration crosses
            c += "0.3 w 0.5 G [3 2] 0 d\n"
            if col < cols - 1:                       # right edge is overlapped
                bx = (col + 1) * pitch_x + args.overlap / 2
                c += line(*P(bx, y0), *P(bx, y0 + usable_h))
            if r < rows - 1:                         # bottom edge is overlapped
                by = (rows - 1 - r) * pitch_y - args.overlap / 2 + args.overlap
                by = y0 + args.overlap / 2
                c += line(*P(x0, by), *P(x0 + usable_w, by))
            c += "[] 0 d 0 G 0.4 w\n"

            for bcol in range(cols - 1):             # vertical overlap centres
                bx = (bcol + 1) * pitch_x + args.overlap / 2
                if x0 - 0.01 <= bx <= x0 + usable_w + 0.01:
                    yy = y0 + 20
                    while yy < y0 + usable_h - 10:
                        c += cross(*P(bx, yy))
                        yy += 60
            for brow in range(rows - 1):             # horizontal overlap centres
                by = (brow + 1) * pitch_y + args.overlap / 2
                if y0 - 0.01 <= by <= y0 + usable_h + 0.01:
                    xx = x0 + 20
                    while xx < x0 + usable_w - 10:
                        c += cross(*P(xx, by))
                        xx += 60

            c += "Q 0 G 0.3 w\n"
            c += text(m, m + 11.5, f"{label(r, col)}  of  {rows}x{cols}"
                                   f"   |  Iceman body outline, front view  "
                                   f"|  PRINT AT 100%", 9)
            c += ruler(m, m + 4)
            pdf.add_page(c)

    return pdf, rows, cols, bw, bh


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scad", default=os.path.join(REPO, "body", "iceman.scad"))
    ap.add_argument("--out", default=os.path.join(REPO, "body", "iceman_template.pdf"))
    ap.add_argument("--soften", type=float, default=8.0, help="corner radius, mm")
    ap.add_argument("--fn", type=int, default=128, help="arc segments")
    ap.add_argument("--overlap", type=float, default=15.0, help="sheet overlap, mm")
    ap.add_argument("--margin", type=float, default=10.0,
                    help="unprintable margin to keep clear, mm")
    ap.add_argument("--paper", choices=sorted(PAPER), default="letter")
    ap.add_argument("--landscape", action="store_true")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        svg = export_outline_svg(args.scad, args.soften, args.fn,
                                 os.path.join(tmp, "outline.svg"))
        loops = parse_svg_paths(svg)

    pdf, rows, cols, bw, bh = build(loops, args)
    pdf.write(args.out)
    print(f"outline   {bw:.1f} x {bh:.1f} mm  ({bw/25.4:.2f} x {bh/25.4:.2f} in)")
    print(f"loops     {len(loops)}  ({sum(len(l) for l in loops)} points)")
    print(f"sheets    {rows} x {cols} = {rows*cols} tiles + 1 assembly map "
          f"= {rows*cols+1} pages, {args.paper}")
    print(f"wrote     {args.out}")


if __name__ == "__main__":
    main()
