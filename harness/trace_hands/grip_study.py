"""D4d, positioning: where the traced grip sits on Katherina's staff arm.

The owner: the traced hands look odd on the tall-chibi Katherina holding her
staff (the chibi reference, `ref-local/katherina_grok/`, for comparison). Her
staff arm is swung out 36 degrees, so it is not the hanging arm option (a)
assumed: the forearm comes in from the upper side, as in both references, and
the fist kept upright with its wrist taken from above left a wedge between
the diagonal cuff and the fist's flat top.

- **now**: as built, the fist's top over the staff's channel at the wrist;
- **wrist**: the fist anchored at its own traced wrist (its right side, where
  the reference's forearm met it) on the arm's wrist, upright, the staff moved
  to run through the fist's channel (`_hand_centre` there);
- **wrist, smaller**: the same at 0.50 head radii rather than 0.65 (the chibi
  reference's fist is about 0.45 against its head).

Each at 5x round the fist, and whole. Writes `out/trace_hands/grip_study.png`.

A record: the placement it studied went into `character.py` as
`_traced_placement` (the cuff fit) on 2026-09-27, and helpers it patches
(`_grip_anchor`, the upright grip) are gone, so it may no longer run.
"""

import io
import math
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

TRACED = c._traced_hand
CENTRE = c._hand_centre
LENGTH = c._HAND_TRACED_LENGTH


def channel() -> tuple[float, float]:
    *fingers, _back = c._HAND_GRIP
    gx, _gy = c._grip_anchor()
    ys = [y for piece in fingers for _, y in c._chain_points(piece[0])]
    return gx, (min(ys) + max(ys)) / 2


def arm_wrist(sk, p, s):
    """The arm's wrist in the picture, after its swing."""
    _t, _e, centre_wrist, wrist_y = c._arm_line(sk)
    px, py = c._arm_pivot(sk, p, s)
    x, y = sk.head_cx + s * centre_wrist, wrist_y
    swing = p.right_arm_out if s == -1 else p.left_arm_out
    a = math.radians(-s * swing)
    return px + (x - px) * math.cos(a) - (y - py) * math.sin(a), py + (x - px) * math.sin(a) + (y - py) * math.cos(a)


def wrist_anchored(sk, p, cx, wrist_y, w_wrist, side):
    if not (side == -1 and p.outfit.staff_color is not None):
        return TRACED(sk, p, cx, wrist_y, w_wrist, side)
    k = c._HAND_TRACED_LENGTH * sk.head_r
    sw = c._stroke_w(sk)

    def pt(q):
        return f"{cx + q[0] * k:.2f} {wrist_y + q[1] * k:.2f}"

    def path(ch, closed):
        start, segs = ch
        d = f"M {pt(start)} " + " ".join(f"Q {pt(c1)} {pt(e)}" for c1, e in segs)
        return d + " Z" if closed else d

    parts = []
    for outline, holes, lines in c._HAND_GRIP:
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
    swing = p.right_arm_out
    return f'<g transform="rotate({side * swing:.2f} {cx:.1f} {wrist_y:.1f})">{"".join(parts)}</g>'


def centre_on_channel(sk, p, s):
    if s != -1 or p.hand_style != "traced" or p.outfit.staff_color is None:
        return CENTRE(sk, p, s)
    wx, wy = arm_wrist(sk, p, s)
    chx, chy = channel()
    k = c._HAND_TRACED_LENGTH * sk.head_r
    return ((wx + chx * k - sk.head_cx) / sk.head_r, (wy + chy * k - sk.head_cy) / sk.head_r)


def render(p, scale):
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB"), sk


def main():
    p = replace(PRESETS["katherina"], hand_style="traced")
    rows = []
    try:
        for label, anchored, length in (("now", False, 0.65), ("wrist", True, 0.65), ("wrist, smaller", True, 0.50)):
            c._HAND_TRACED_LENGTH = length
            if anchored:
                c._traced_hand, c._hand_centre = wrist_anchored, centre_on_channel
            im, sk = render(p, 5)
            wx, wy = arm_wrist(sk, p, -1)
            r = sk.head_r * 5
            zoom = im.crop((int(wx * 5 - 1.4 * r), int(wy * 5 - 1.1 * r), int(wx * 5 + 0.9 * r), int(wy * 5 + 1.0 * r)))
            ImageDraw.Draw(zoom).text((4, 4), label, fill=(200, 0, 0))
            whole, _ = render(p, 1.4)
            rows.append((zoom, whole))
            c._traced_hand, c._hand_centre = TRACED, CENTRE
    finally:
        c._traced_hand, c._hand_centre, c._HAND_TRACED_LENGTH = TRACED, CENTRE, LENGTH
    ref = Image.open("ref-local/katherina_grok/katherina_grok.jpg").convert("RGB")
    ref = ref.resize((int(ref.width * rows[0][1].height / ref.height), rows[0][1].height))
    zw = max(z.width for z, _ in rows)
    zh = max(z.height for z, _ in rows)
    ww = max(w.width for _, w in rows)
    sheet = Image.new("RGB", (3 * (zw + 4), zh + rows[0][1].height + 8), (190, 190, 190))
    for i, (z, _w) in enumerate(rows):
        sheet.paste(z, (i * (zw + 4), 0))
    x = 0
    for _z, w in rows:
        sheet.paste(w, (x, zh + 8))
        x += ww + 4
    sheet.paste(ref, (x, zh + 8))
    sheet.save("out/trace_hands/grip_study.png")
    print("out/trace_hands/grip_study.png", sheet.size)


if __name__ == "__main__":
    main()
