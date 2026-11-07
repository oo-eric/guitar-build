#!/usr/bin/env python3
"""Render the headstock studies in body/headstock.scad side by side, to scale.

Exports each layout to SVG via OpenSCAD (exact, 1 unit = 1 mm), parses it, and
draws with PIL so the two can be annotated and compared at a known scale.

    python3 scripts/headstock_preview.py out.png
"""

import os
import re
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

OPENSCAD = "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAD = os.path.join(REPO, "body", "headstock.scad")

PADDLE_W, PADDLE_L = 114.3, 190.5
PX_PER_MM = 3.2
PAD = 46


def svg_loops(layout, show_ref):
    """Render one layout to SVG and return its loops in mm, y-up."""
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "o.svg")
        r = subprocess.run(
            [OPENSCAD, "-D", f"layout={layout}",
             "-D", f"show_ref={'true' if show_ref else 'false'}",
             "-o", out, SCAD],
            capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"OpenSCAD failed for layout {layout}:\n{r.stderr}")
        svg = open(out).read()

    loops = []
    for d in re.findall(r'<path[^>]*\sd="([^"]*)"', svg, re.S):
        cur = []
        for cmd, args in re.findall(r'([MLZmlz])([^MLZmlz]*)', d):
            nums = [float(n) for n in
                    re.findall(r'-?\d+\.?\d*(?:[eE][-+]?\d+)?', args)]
            if cmd in "Mm":
                if len(cur) > 2:
                    loops.append(cur)
                cur = []
            for i in range(0, len(nums) - 1, 2):
                cur.append((nums[i], -nums[i + 1]))
        if len(cur) > 2:
            loops.append(cur)
    return loops


def font(sz):
    for p in ("/System/Library/Fonts/Helvetica.ttc",
              "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def panel(layout, title, subtitle, notes):
    w = int(PADDLE_W * PX_PER_MM) + 2 * PAD
    h = int(PADDLE_L * PX_PER_MM) + 2 * PAD + 140
    im = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(im)
    top = 74

    def P(x, y):                       # mm -> px, y flipped, nut at bottom
        return (PAD + (x + PADDLE_W / 2) * PX_PER_MM,
                top + (PADDLE_L - y) * PX_PER_MM)

    d.text((PAD, 14), title, fill="black", font=font(24))
    d.text((PAD, 46), subtitle, fill="#666", font=font(14))

    d.rectangle([P(-PADDLE_W / 2, PADDLE_L), P(PADDLE_W / 2, 0)],
                outline="#c8c8c8", width=2)
    d.text((PAD + 4, top - 17), '4.5 x 7.5" blank', fill="#a0a0a0", font=font(12))

    for lp in svg_loops(layout, show_ref=False):
        d.polygon([P(x, y) for x, y in lp], fill="#4a6fa5")
    for lp in svg_loops(layout, show_ref=True):
        d.line([P(x, y) for x, y in lp] + [P(*lp[0])], fill="white", width=2)

    d.line([P(-PADDLE_W / 2, 0), P(PADDLE_W / 2, 0)], fill="#d03030", width=3)
    d.text((PAD - 40, P(0, 0)[1] - 8), "NUT", fill="#d03030", font=font(13))

    y = h - 118
    for n in notes:
        d.text((PAD, y), n, fill="#333", font=font(14))
        y += 22
    return im


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "headstock_compare.png"
    a = panel(1, "6-inline", "posts 27 mm apart, 13.1 mm off centreline", [
        "Uses 175 of 190.5 mm - 15 mm left past the last post",
        "Worst string pull   11.0 deg",
        "Tuner mass averages 92 mm from the nut",
        "Every string threads past the posts before it",
    ])
    b = panel(2, "3 + 3", "posts 35 mm apart, 15 mm off centreline", [
        "Uses 141 of 190.5 mm - 50 mm unused, on purpose",
        "Worst string pull    6.8 deg",
        "Tuner mass averages 60 mm from the nut - 32 mm closer",
        "No string crosses another post",
    ])
    im = Image.new("RGB", (a.width + b.width + 24, max(a.height, b.height)),
                   "white")
    im.paste(a, (0, 0))
    im.paste(b, (a.width + 24, 0))
    im.save(out)
    print(f"wrote {out}  {im.size[0]}x{im.size[1]}")


if __name__ == "__main__":
    main()
