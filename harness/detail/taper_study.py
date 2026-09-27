"""D4b of `docs/detail-plan.md`: taper the arms and legs.

The retired adult build's limb taper is still in `_arms` and `_legs_and_boots`,
riding the build, so at the chibi's pinned build it runs at a tenth: the
elbow 15% in and the wrist 34% at the full adult build, the ankle to 0.85 of
the leg. `_LIMB_TAPER` (0 today) sets how far along it the limbs are drawn.
The hand's width is the wrist's (`_hand`: `w_wrist * 1.02`), so a tapered
wrist also shrinks the hand; the last row keeps the hand at today's size.

Rows: taper 0 (today), 0.5, 1.0, 1.0 with the hands half way between the
tapered wrist and today's, 1.0 with the hands kept. Columns: Krista in
the base layer (bare arms and legs), Satoshi (sleeves, trousers), Keiko (the
traced coat's sleeves) and Satoko (a skirt, bare hands), each at height 1.0
and 1.3, one head size, feet on one line. Writes `out/detail/taper_study.png`.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"
HAND = c._hand


def hand_kept(sk, p, cx, wrist_y, w_wrist, side):
    return HAND(sk, p, cx, wrist_y, sk.arm_half_w * (1.0 - 0.34 * sk.build), side)


def hand_half(sk, p, cx, wrist_y, w_wrist, side):
    return HAND(sk, p, cx, wrist_y, (w_wrist + sk.arm_half_w * (1.0 - 0.34 * sk.build)) / 2, side)


def cases():
    krista = PRESETS["krista"]
    off = [n for n in c.Outfit.__dataclass_fields__ if n.endswith("_color") and n not in ("underwear_color", "boot_color")]
    base = replace(krista, outfit=replace(krista.outfit, **dict.fromkeys(off)))
    return [("krista base layer", base), ("satoshi", PRESETS["satoshi"]), ("keiko", PRESETS["keiko"]), ("satoko", PRESETS["satoko"])]


def tile(p, label, ref_r):
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=1.5))).convert("RGB")
    s = ref_r * 1.5 / (sk.head_r * 1.5)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    k = 1.5 * s
    foot, cx = sk.foot_y * k, sk.head_cx * k
    w, top = int(3.0 * ref_r * 1.5), int(foot - 9.0 * ref_r * 1.5)
    out = Image.new("RGB", (w, int(9.4 * ref_r * 1.5)), (255, 255, 255))
    out.paste(im.crop((int(cx - w / 2), max(0, top), int(cx + w / 2), min(im.height, int(foot + 0.4 * ref_r * 1.5)))), (0, max(0, -top)))
    ImageDraw.Draw(out).text((3, 3), label, fill=(200, 0, 0))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    ref_r = c.skeleton_for(PRESETS["satoko"]).head_r
    rows = []
    try:
        for label, taper, hand in (
            ("taper 0", 0.0, HAND),
            ("taper 0.5", 0.5, HAND),
            ("taper 1", 1.0, HAND),
            ("taper 1, hands half way", 1.0, hand_half),
            ("taper 1, hands kept", 1.0, hand_kept),
        ):
            c._LIMB_TAPER = taper
            c._hand = hand
            rows.append([tile(replace(p, height=h), f"{n} h{h}: {label}", ref_r) for n, p in cases() for h in (1.0, 1.3)])
    finally:
        c._LIMB_TAPER, c._hand = 0.0, HAND
    tw = max(t.width for r in rows for t in r)
    th = max(t.height for r in rows for t in r)
    sheet = Image.new("RGB", (len(rows[0]) * (tw + 3), len(rows) * (th + 5)), (190, 190, 190))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            sheet.paste(t, (i * (tw + 3), j * (th + 5)))
    sheet.save(f"{OUT}/taper_study.png")
    print(f"{OUT}/taper_study.png", sheet.size)


if __name__ == "__main__":
    main()
