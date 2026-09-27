"""D4d, positioning: each traced hand fitted to its cuff's opening.

The owner: match the hands to the cuff openings, their positions and angles.
The opening, in the arm's own (unswung) frame, which is the frame the hand is
drawn in:

- on a traced sleeve (Katherina's jacket), the cuff band's chain placed on the
  figure: its principal axis is the band's length, the side of it further
  along the forearm is the opening, and a line fitted through that side's
  points gives the opening's centre, direction and width;
- on a drawn arm or sleeve, the wrist line (`_arm_line`), level.

The hand is turned so its traced wrist (`calib.py`: `across` and `into_hand`)
lies along the opening, facing out of it, and its wrist's centre is put on
the opening's centre, tucked `TUCK` head radii inside (the hand is drawn under
its arm, so the cuff's edge lies over the wrist). The open hand's wrist widens
to 0.9 of the opening; the grip keeps its shape and the staff runs through its
channel. Size 0.50 head radii.

Columns: Katherina's staff arm, her other arm, her whole figure; Krista's arm
and the base layer's bare arm; 5x. Writes `out/trace_hands/cuff_fit.png` and
prints each opening.

A record: the placement it studied went into `character.py` as
`_traced_placement` (the cuff fit) on 2026-09-27, and helpers it patches
(`_grip_anchor`, the upright grip) are gone, so it may no longer run.
"""

import io
import json
import math
import sys
from dataclasses import replace

import cairosvg
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "harness/trace_hands")
import grip_study as gs  # noqa: E402
import relaxed_study as rs  # noqa: E402
from anime_character_creator import character as c  # noqa: E402
from anime_character_creator.presets import PRESETS  # noqa: E402

CAL = json.load(open("out/trace_hands/calib.json"))
LENGTH = 0.50
TUCK = 0.04


def forearm(sk, side):
    centre_top, _t, centre_wrist, wrist_y = c._arm_line(sk)
    centre_elbow = centre_top + (centre_wrist - centre_top) * 0.35
    f = np.array([side * (centre_wrist - centre_elbow), wrist_y - sk.waist_y])
    return f / np.linalg.norm(f)


def opening(sk, p, side):
    """`(centre, direction, half_width, out)` of the cuff's opening, in pixels, in
    the arm's unswung frame; `out` the unit normal pointing out of the sleeve."""
    f = forearm(sk, side)
    cut = c._worn_sleeve(sk, p)
    if cut is None:
        _t, _ty, centre_wrist, wrist_y = c._arm_line(sk)
        w = sk.arm_half_w * (1.0 - 0.34 * c._limb_build(sk))
        return np.array([sk.head_cx + side * centre_wrist, wrist_y]), np.array([1.0, 0.0]), w, np.array([0.0, 1.0])
    place = c._sleeve_placement(sk, cut, side)
    pts = np.array([place(q) for q in c._chain_points(cut.cuff, 16)])
    pts = np.stack([sk.head_cx + pts[:, 0] * sk.head_r, sk.head_cy + pts[:, 1] * sk.head_r], 1)
    cen = pts.mean(0)
    _u, _s, vt = np.linalg.svd(pts - cen)
    m = vt[1] if vt[1] @ f > 0 else -vt[1]
    far = pts[(pts - cen) @ m > 0]
    fc = far.mean(0)
    _u, _s, vt2 = np.linalg.svd(far - fc)
    e = vt2[0]
    t = (far - fc) @ e
    half = (t.max() - t.min()) / 2
    mid = fc + e * (t.max() + t.min()) / 2
    out = np.array([-e[1], e[0]])
    if out @ f < 0:
        out = -out
    return mid, e, half, out


def hand_transform(sk, p, side, grip):
    """A function mapping a traced hand's point to the picture (unswung frame)."""
    name = "grip" if grip else "relaxed"
    mirror = (side == 1) if grip else (side == -1)
    ix, iy = CAL[name]["into_hand"]
    if mirror:
        ix = -ix
    mid, _e, half, out = opening(sk, p, side)
    theta = math.atan2(out[1], out[0]) - math.atan2(iy, ix)
    k = LENGTH * sk.head_r
    widen = 1.0
    if not grip:
        widen = 0.9 * half / (c._traced_wrist_half(c._HAND_RELAXED) * k)
    base = mid - out * TUCK * sk.head_r

    def place(q):
        x, y = q
        if not grip and y < c._HAND_WRIST_STRETCH:
            s = 1.0 - max(0.0, y) / c._HAND_WRIST_STRETCH
            x *= 1.0 + (widen - 1.0) * s * s
        x = -x if mirror else x
        x, y = x * k, y * k
        return (
            base[0] + x * math.cos(theta) - y * math.sin(theta),
            base[1] + x * math.sin(theta) + y * math.cos(theta),
        )

    return place


def traced(sk, p, cx, wrist_y, w_wrist, side):
    grip = side == -1 and p.outfit.staff_color is not None
    pieces = c._HAND_GRIP if grip else c._HAND_RELAXED
    return rs.draw_pieces(sk, p, pieces, hand_transform(sk, p, side, grip), False)


def centre(sk, p, s):
    if s != -1 or p.hand_style != "traced" or p.outfit.staff_color is None:
        return gs.CENTRE(sk, p, s)
    x, y = hand_transform(sk, p, s, True)(gs.channel())
    px, py = c._arm_pivot(sk, p, s)
    a = math.radians(-s * p.right_arm_out)
    rx = px + (x - px) * math.cos(a) - (y - py) * math.sin(a)
    ry = py + (x - px) * math.sin(a) + (y - py) * math.cos(a)
    return ((rx - sk.head_cx) / sk.head_r, (ry - sk.head_cy) / sk.head_r)


def main():
    kat = replace(PRESETS["katherina"], hand_style="traced")
    krista = replace(PRESETS["krista"], hand_style="traced")
    off = [n for n in c.Outfit.__dataclass_fields__ if n.endswith("_color") and n not in ("underwear_color", "boot_color")]
    bare = replace(krista, outfit=replace(krista.outfit, **dict.fromkeys(off)))
    tiles = []
    try:
        c._traced_hand, c._hand_centre = traced, centre
        for label, p, sides, whole in (("katherina", kat, (-1, 1), True), ("krista", krista, (1,), False), ("krista base", bare, (1,), False)):
            sk = c.skeleton_for(p)
            for s in sides:
                mid, e, half, out = opening(sk, p, s)
                print(label, s, "opening centre", mid.round(1), "angle", round(math.degrees(math.atan2(e[1], e[0])), 1), "half width", round(half / sk.head_r, 3))
            svg = c.render_character(p, sk, background="#ffffff")
            big = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=5))).convert("RGB")
            r = sk.head_r * 5
            for s in sides:
                wx, wy = gs.arm_wrist(sk, p, s)
                t = big.crop((int(wx * 5 - 1.1 * r), int(wy * 5 - 1.2 * r), int(wx * 5 + 1.1 * r), int(wy * 5 + 1.0 * r)))
                ImageDraw.Draw(t).text((4, 4), f"{label} {'staff arm' if (s == -1 and p.outfit.staff_color) else 'arm'}", fill=(200, 0, 0))
                tiles.append(t)
            if whole:
                tiles.append(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=1.1))).convert("RGB"))
    finally:
        c._traced_hand, c._hand_centre = gs.TRACED, gs.CENTRE
    h = max(t.height for t in tiles)
    sheet = Image.new("RGB", (sum(t.width for t in tiles) + 4 * len(tiles), h), (190, 190, 190))
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 0))
        x += t.width + 4
    sheet.save("out/trace_hands/cuff_fit.png")
    print("out/trace_hands/cuff_fit.png", sheet.size)


if __name__ == "__main__":
    main()
