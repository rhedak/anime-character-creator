"""D4d, positioning: turn each traced hand so its wrist follows its sleeve.

The owner: zoom in on Katherina's arms and rotate the hands so the wrist's
angle matches the sleeve's. Each traced hand records the direction its
reference forearm came in from (`calib.py`'s `into_hand`: the grip's from the
side, the open hand's from above). Here each hand is turned about its wrist
so that direction lies along our forearm, from the elbow (at the waist, as
`_arms` draws it) to the wrist, and then turns with the arm's swing. The
staff still runs through the grip's channel, wherever that lands.

Rows: **upright** (the grip kept upright, `grip_study.py`'s "wrist,
smaller"); **half** (turned half way); **matched** (turned fully). Columns:
Katherina's staff arm and her other arm (the open hand at 0.50), 5x, and the
whole figure. Writes `out/trace_hands/wrist_angle.png`.

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
from PIL import Image, ImageDraw

sys.path.insert(0, "harness/trace_hands")
import grip_study as gs  # noqa: E402
import relaxed_study as rs  # noqa: E402
from anime_character_creator import character as c  # noqa: E402
from anime_character_creator.presets import PRESETS  # noqa: E402

CAL = json.load(open("out/trace_hands/calib.json"))
SHARE = {"k": 1.0}
LENGTH = 0.50


def forearm_local(sk, side):
    """Our forearm's direction, elbow to wrist, in the arm's unswung frame."""
    centre_top, _top_y, centre_wrist, wrist_y = c._arm_line(sk)
    centre_elbow = centre_top + (centre_wrist - centre_top) * 0.35
    return side * (centre_wrist - centre_elbow), wrist_y - sk.waist_y


def turn_for(sk, side, grip):
    """Degrees to turn the traced hand (in its drawn, mirrored orientation) so its
    reference forearm lies along ours, times the study's share."""
    ix, iy = CAL["grip" if grip else "relaxed"]["into_hand"]
    mirror = (side == 1) if grip else (side == -1)
    if mirror:
        ix = -ix
    fx, fy = forearm_local(sk, side)
    a = math.degrees(math.atan2(fy, fx) - math.atan2(iy, ix))
    a = (a + 180) % 360 - 180
    return a * SHARE["k"]


def draw(sk, p, cx, wrist_y, side):
    grip = side == -1 and p.outfit.staff_color is not None
    pieces = c._HAND_GRIP if grip else c._HAND_RELAXED
    mirror = (side == 1) if grip else (side == -1)
    k = LENGTH * sk.head_r

    def place(q):
        x = q[0] * k
        return (cx + (-x if mirror else x), wrist_y + q[1] * k)

    out = rs.draw_pieces(sk, p, pieces, place, False)
    a = turn_for(sk, side, grip)
    return f'<g transform="rotate({a:.2f} {cx:.1f} {wrist_y:.1f})">{out}</g>'


def traced(sk, p, cx, wrist_y, w_wrist, side):
    if SHARE["k"] is None:
        return gs.wrist_anchored(sk, p, cx, wrist_y, w_wrist, side) if side == -1 else rs.traced(
            sk, p, cx, wrist_y, w_wrist, side
        )
    return draw(sk, p, cx, wrist_y, side)


def centre(sk, p, s):
    if s != -1 or p.hand_style != "traced" or p.outfit.staff_color is None:
        return gs.CENTRE(sk, p, s)
    if SHARE["k"] is None:
        return gs.centre_on_channel(sk, p, s)
    wx, wy = gs.arm_wrist(sk, p, s)
    chx, chy = gs.channel()
    k = LENGTH * sk.head_r
    a = math.radians(turn_for(sk, s, True) + (-s * p.right_arm_out))
    x, y = chx * k, chy * k
    x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    return ((wx + x - sk.head_cx) / sk.head_r, (wy + y - sk.head_cy) / sk.head_r)


def main():
    p = replace(PRESETS["katherina"], hand_style="traced")
    rows = []
    rs.VARIANT["name"] = "open 0.50"
    try:
        c._traced_hand, c._hand_centre, c._HAND_TRACED_LENGTH = traced, centre, LENGTH
        for label, share in (("upright", None), ("half", 0.5), ("matched", 1.0)):
            SHARE["k"] = share
            sk = c.skeleton_for(p)
            svg = c.render_character(p, sk, background="#ffffff")
            big = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=5))).convert("RGB")
            whole = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=1.1))).convert("RGB")
            r = sk.head_r * 5
            row = []
            for s in (-1, 1):
                wx, wy = gs.arm_wrist(sk, p, s)
                t = big.crop((int(wx * 5 - 1.1 * r), int(wy * 5 - 1.3 * r), int(wx * 5 + 1.1 * r), int(wy * 5 + 0.9 * r)))
                ImageDraw.Draw(t).text((4, 4), f"{label}, {'staff arm' if s == -1 else 'other arm'}", fill=(200, 0, 0))
                row.append(t)
            row.append(whole)
            rows.append(row)
    finally:
        c._traced_hand, c._hand_centre, c._HAND_TRACED_LENGTH = gs.TRACED, gs.CENTRE, gs.LENGTH
    widths = [max(r[i].width for r in rows) for i in range(3)]
    th = max(max(t.height for t in r) for r in rows)
    sheet = Image.new("RGB", (sum(widths) + 12, len(rows) * (th + 6)), (190, 190, 190))
    for j, r in enumerate(rows):
        x = 0
        for i, t in enumerate(r):
            sheet.paste(t, (x, j * (th + 6)))
            x += widths[i] + 4
    sheet.save("out/trace_hands/wrist_angle.png")
    print("out/trace_hands/wrist_angle.png", sheet.size)
    sk = c.skeleton_for(p)
    print("turn, staff arm", round(turn_for(sk, -1, True), 1), "other arm", round(turn_for(sk, 1, False), 1))


if __name__ == "__main__":
    main()
