#!/usr/bin/env python3
"""Tuner-layout geometry for the paddle headstock. Not a shape design -- this
sizes the envelope the shape has to contain.

For 6-inline and 3+3 it reports:
  1. minimum paddle width and length the posts need
  2. how far each string sits off straight pull at the nut
  3. for 6-inline, how close each string runs to the posts it passes

Everything here is an assumption until the tuners are in hand -- post spacing
and bushing diameter vary by brand. Edit CONFIG and re-run.

    python3 scripts/headstock_layout.py
"""

import math

IN = 25.4

CONFIG = {
    "paddle_w": 4.5 * IN,
    "paddle_l": 7.5 * IN,

    "nut_width": 1.6875 * IN,
    "string_spread": 36.0,        # E-to-e centres at the nut

    "nut_to_first_post": 25.0,    # nut face to nearest post centre
    "tip_margin": 15.0,           # last post centre to end of paddle

    "post_dia": 6.35,             # the post itself, for string-fouling checks
    "bushing_dia": 12.0,
    "edge_wood_min": 4.0,         # wood left between bushing edge and paddle edge
    "string_clear_min": 2.0,      # clearance a string needs past a post it passes
}

SPACING = {"6-inline": 27.0, "3+3": 35.0}    # typical, verify against real tuners
NAMES = ["E ", "A ", "D ", "G ", "B ", "e "]


def edge_clr(c):
    return c["bushing_dia"] / 2 + c["edge_wood_min"]


def nut_x(c):
    s = c["string_spread"]
    return [-s / 2 + i * s / 5 for i in range(6)]   # index 0 = low E, bass side


def build(layout, off, c):
    """Post (x, y) per string index, for a given lateral offset."""
    step, y0 = SPACING[layout], c["nut_to_first_post"]
    if layout == "6-inline":
        # collinear posts, all on the bass side. Low E takes the nearest post.
        return [(-off, y0 + i * step) for i in range(6)]
    # 3+3: OUTER strings take the NEAR posts, so the inner strings (D, G) get
    # the long run to the far post and stay close to straight. Getting this
    # ordering backwards is what produces a 30 deg pull on the G.
    return [(-off, y0), (-off, y0 + step), (-off, y0 + 2 * step),   # E A D
            (+off, y0 + 2 * step), (+off, y0 + step), (+off, y0)]   # G B e


def splay(posts, c):
    return [math.degrees(math.atan2(px - nx, py))
            for (px, py), nx in zip(posts, nut_x(c))]


def best_offset(layout, c):
    """Lateral offset that minimises the worst string's splay."""
    lo, hi = 0.0, c["paddle_w"] / 2 - edge_clr(c)
    for _ in range(200):
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        f = lambda o: max(abs(s) for s in splay(build(layout, o, c), c))
        lo, hi = (lo, m2) if f(m1) < f(m2) else (m1, hi)
    return (lo + hi) / 2


def clearances(posts, c):
    """6-inline only: how close does each string pass the posts before its own?

    Tight numbers here are NORMAL -- every Strat runs its strings within a mm or
    two of the intervening posts. It is not a fault, it is a precision warning:
    hole placement has to be accurate and staggered-height tuners help."""
    out = []
    for i, ((px, py), nx) in enumerate(zip(posts, nut_x(c))):
        for j, (qx, qy) in enumerate(posts):
            if qy >= py:                     # only posts between nut and target
                continue
            dx, dy = px - nx, py - 0.0
            t = ((qx - nx) * dx + qy * dy) / (dx * dx + dy * dy)
            if not 0 < t < 1:
                continue
            d = math.hypot(nx + t * dx - qx, t * dy - qy)
            out.append((NAMES[i].strip(), j + 1, d,
                        c["post_dia"] / 2 + c["string_clear_min"]))
    return out


def main():
    c = CONFIG
    W, L, clr = c["paddle_w"], c["paddle_l"], edge_clr(c)
    print(f"Paddle  {W:.1f} x {L:.1f} mm  ({W/IN:.2f} x {L/IN:.2f} in)")
    print(f"Post centres stay {clr:.1f} mm off any edge "
          f"({c['bushing_dia']:.0f} mm bushing + {c['edge_wood_min']:.0f} mm wood)\n")

    for layout in ("6-inline", "3+3"):
        off = best_offset(layout, c)
        posts = build(layout, off, c)
        sp = splay(posts, c)
        need_l = max(p[1] for p in posts) + c["tip_margin"]
        # width must hold the posts AND the nut end of the headstock
        need_w = max(max(abs(px) for px, _ in posts) + clr,
                     c["nut_width"] / 2 + 3.0) * 2

        print(f"── {layout}   posts {SPACING[layout]:.0f} mm apart, "
              f"offset {off:.1f} mm from centreline")
        print(f"   needs {need_w:.1f} x {need_l:.1f} mm   "
              f"→ spare {W-need_w:+.1f} wide, {L-need_l:+.1f} long"
              f"   [{'FITS' if need_w<=W and need_l<=L else 'DOES NOT FIT'}]")
        for n, s in zip(NAMES, sp):
            print(f"     {n} {s:+5.1f}deg {'#' * int(abs(s) * 3)}")
        print(f"   worst pull {max(abs(s) for s in sp):.1f} deg")
        if layout == "6-inline":
            cl = clearances(posts, c)
            tight = min(cl, key=lambda r: r[2]) if cl else None
            print("   string clearance past intervening posts "
                  "(normal to be tight -- see docstring):")
            print("     " + ", ".join(f"{s}/p{p} {d:.1f}" for s, p, d, _ in cl)
                  + " mm")
            if tight:
                print(f"     tightest: {tight[0]} string passes {tight[2]:.1f} mm "
                      f"from post {tight[1]}")
        print()


if __name__ == "__main__":
    main()
