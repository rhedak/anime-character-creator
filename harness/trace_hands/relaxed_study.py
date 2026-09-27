"""D4d, positioning: the relaxed hand beside the smaller, wrist-anchored grip.

The owner: build both options for the relaxed hand and compare them before
locking anything in. Every column has the grip as `grip_study.py`'s "wrist,
smaller" (anchored at its own wrist, the staff through its channel, 0.50 head
radii). The relaxed hand:

- **mitten**: today's, for comparison;
- **open 0.65**: the traced open hand as built;
- **open 0.50**: the same at the grip's size;
- **fist, from above**: a loose fist made of the grip's traced pieces with
  nothing held, the channel filled with skin under a hull outline, upright,
  its top over the channel taking the wrist (the arm hangs);
- **fist, turned**: the same turned a quarter so its traced wrist (its side)
  faces up the arm.

Rows: Katherina whole with a 4x crop of her relaxed hand; Krista whole with a
crop; Krista in the base layer (a bare forearm). Writes
`out/trace_hands/relaxed_study.png`.

A record: the placement it studied went into `character.py` as
`_traced_placement` (the cuff fit) on 2026-09-27, and helpers it patches
(`_grip_anchor`, the upright grip) are gone, so it may no longer run.
"""

import io
import sys
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

sys.path.insert(0, "harness/trace_hands")
import grip_study as gs  # noqa: E402
from anime_character_creator import character as c  # noqa: E402
from anime_character_creator.presets import PRESETS  # noqa: E402

VARIANT = {"name": "open 0.65"}


def hull(points):
    pts = sorted(set(points))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for q in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    return lower[:-1] + upper[:-1]


def draw_pieces(sk, p, pieces, place, under_hull):
    sw = c._stroke_w(sk)

    def pt(q):
        x, y = place(q)
        return f"{x:.2f} {y:.2f}"

    def path(ch, closed):
        start, segs = ch
        d = f"M {pt(start)} " + " ".join(f"Q {pt(c1)} {pt(e)}" for c1, e in segs)
        return d + " Z" if closed else d

    parts = []
    if under_hull:
        pts = [q for piece in pieces for q in c._chain_points(piece[0])]
        h = hull(pts)
        d = "M " + " L ".join(pt(q) for q in h) + " Z"
        parts.append(
            f'<path d="{d}" fill="{p.skin_tone}" stroke="{c.OUTLINE}" '
            f'stroke-width="{c._outline_w(sw, 0.85):.2f}" stroke-linejoin="round" />'
        )
    for outline, holes, lines in pieces:
        d = " ".join(path(ch, True) for ch in (outline, *holes))
        parts.append(
            f'<path d="{d}" fill="{p.skin_tone}" fill-rule="evenodd" stroke="{c.OUTLINE}" '
            f'stroke-width="{c._outline_w(sw, 0.85):.2f}" stroke-linejoin="round" />'
        )
        for ln in lines:
            parts.append(
                f'<path d="{path(ln, False)}" fill="none" stroke="{c.OUTLINE}" '
                f'stroke-width="{c._interior_w(sw, 0.8):.2f}" stroke-linecap="round" />'
            )
    return "".join(parts)


def traced(sk, p, cx, wrist_y, w_wrist, side):
    grip = side == -1 and p.outfit.staff_color is not None
    if grip:
        return gs.wrist_anchored(sk, p, cx, wrist_y, w_wrist, side)
    v = VARIANT["name"]
    if v.startswith("open"):
        return gs.TRACED(sk, p, cx, wrist_y, w_wrist, side)
    k = 0.50 * sk.head_r
    mirror = side == 1
    swing = p.right_arm_out if side == -1 else p.left_arm_out
    if v == "fist, from above":
        ax, ay = c._grip_anchor()

        def place(q):
            x = (q[0] - ax) * k
            return (cx + (-x if mirror else x), wrist_y + (q[1] - ay) * k)
    else:
        # A quarter turn: the traced wrist (+x, the fist's side) faces up.
        def place(q):
            x, y = q[1] * k, -q[0] * k
            return (cx + (-x if mirror else x), wrist_y + y)

    out = draw_pieces(sk, p, c._HAND_GRIP, place, True)
    if swing:
        out = f'<g transform="rotate({side * swing:.2f} {cx:.1f} {wrist_y:.1f})">{out}</g>'
    return out


def render(p, scale):
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB"), sk


def column(p, s):
    whole, sk = render(p, 1.2)
    big, _ = render(p, 4)
    wx, wy = gs.arm_wrist(sk, p, s)
    r = sk.head_r * 4
    crop = big.crop((int(wx * 4 - 0.8 * r), int(wy * 4 - 0.5 * r), int(wx * 4 + 0.8 * r), int(wy * 4 + 1.1 * r)))
    crop = crop.resize((whole.width, int(crop.height * whole.width / crop.width)))
    out = Image.new("RGB", (whole.width, whole.height + crop.height + 4), (190, 190, 190))
    out.paste(whole, (0, 0))
    out.paste(crop, (0, whole.height + 4))
    return out


def main():
    krista = PRESETS["krista"]
    off = [n for n in c.Outfit.__dataclass_fields__ if n.endswith("_color") and n not in ("underwear_color", "boot_color")]
    cases = (
        ("katherina", replace(PRESETS["katherina"], hand_style="traced"), 1),
        ("krista", replace(krista, hand_style="traced"), 1),
        ("krista base", replace(krista, hand_style="traced", outfit=replace(krista.outfit, **dict.fromkeys(off))), 1),
    )
    variants = ("mitten", "open 0.65", "open 0.50", "fist, from above", "fist, turned")
    rows = []
    try:
        c._hand_centre = gs.centre_on_channel
        for name, p, s in cases:
            row = []
            for v in variants:
                VARIANT["name"] = v
                c._HAND_TRACED_LENGTH = 0.65 if v == "open 0.65" else 0.50
                c._traced_hand = traced
                q = replace(p, hand_style="mitten") if v == "mitten" else p
                t = column(q, s)
                ImageDraw.Draw(t).text((3, 3), f"{name}: {v}", fill=(200, 0, 0))
                row.append(t)
            rows.append(row)
    finally:
        c._traced_hand, c._hand_centre, c._HAND_TRACED_LENGTH = gs.TRACED, gs.CENTRE, gs.LENGTH
    tw = max(t.width for r in rows for t in r)
    th = max(t.height for r in rows for t in r)
    sheet = Image.new("RGB", (len(variants) * (tw + 4), len(rows) * (th + 6)), (150, 150, 150))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            sheet.paste(t, (i * (tw + 4), j * (th + 6)))
    sheet.save("out/trace_hands/relaxed_study.png")
    print("out/trace_hands/relaxed_study.png", sheet.size)


if __name__ == "__main__":
    main()
