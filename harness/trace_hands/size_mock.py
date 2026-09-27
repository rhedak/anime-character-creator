"""D4d H0: how big should a traced hand be on the chibi? A mock-up for the
owner's decision, not a render: the reference's relaxed hand, cut out of the
picture by its skin component (grown by its outline), pasted over our figure's
hanging hand at three sizes. Nothing here ships; the harness only.

- **A, by the wrist**: scaled so its wrist matches ours; its length follows
  (2.72 wrists, about 1.06 head radii), an adult's hand, as the reference's is.
- **B, halfway**: its length 0.65 head radii.
- **C, chibi**: its length 0.45 head radii (the research: a chibi hand is a half
  to a third of the face's height), its wrist then narrower than our arm.

Our figure: Krista at heights 1.0 and 1.3. Writes `out/trace_hands/size_mock.png`.
"""

import io
import json
from dataclasses import replace

import cairosvg
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

REF = "ref-local/katherina_grok_real/katherina_grok_real.png"
OUT = "out/trace_hands"
SCALE = 3


def cutout():
    cal = json.load(open(f"{OUT}/calib.json"))["relaxed"]
    a = np.asarray(Image.open(REF).convert("RGB"))
    seed, box = (820, 880), (780, 840, 900, 990)
    col = a[seed[1], seed[0]].astype(int)
    m = np.abs(a.astype(int) - col).sum(2) < 110
    keep = np.zeros_like(m)
    keep[box[1] : box[3], box[0] : box[2]] = True
    lab, _ = ndi.label(ndi.binary_closing(m & keep, iterations=3))
    hand = ndi.binary_fill_holes(lab == lab[seed[1], seed[0]])
    hand = ndi.binary_dilation(hand, iterations=3)
    rgba = np.dstack([a, (hand * 255).astype(np.uint8)])
    ys, xs = np.nonzero(hand)
    crop = Image.fromarray(rgba).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    wx, wy = cal["wrist_centre"]
    return crop, (wx - xs.min(), wy - ys.min()), cal["wrist_width"], cal["length"]


def main():
    hand, (ax, ay), ref_wrist, ref_len = cutout()
    krista = PRESETS["krista"]
    tiles = []
    for h in (1.0, 1.3):
        p = replace(krista, height=h)
        sk = c.skeleton_for(p)
        svg = c.render_character(p, sk, background="#ffffff")
        base = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGBA")
        _t, _e, centre_wrist, wrist_y = c._arm_line(sk)
        w_wrist = sk.arm_half_w * (1.0 - 0.34 * c._limb_build(sk))
        wx, wy = (sk.head_cx + centre_wrist) * SCALE, wrist_y * SCALE
        r = sk.head_r * SCALE
        for label, k in (
            ("today", None),
            ("A by the wrist", 2 * w_wrist * SCALE / ref_wrist),
            ("B 0.65 r", 0.65 * r / ref_len),
            ("C 0.45 r", 0.45 * r / ref_len),
        ):
            im = base.copy()
            if k is not None:
                hs = hand.resize((int(hand.width * k), int(hand.height * k)), Image.LANCZOS)
                im.alpha_composite(hs, (int(wx - ax * k), int(wy - ay * k)))
            box = (int(wx - 1.6 * r), int(sk.shoulder_y * SCALE - 0.3 * r), int(wx + 0.9 * r), int(wy + 1.4 * r))
            t = im.crop(box).convert("RGB")
            ImageDraw.Draw(t).text((3, 3), f"h{h}: {label}", fill=(200, 0, 0))
            tiles.append(t)
    w = max(t.width for t in tiles)
    hh = max(t.height for t in tiles)
    sheet = Image.new("RGB", (4 * (w + 4), 2 * (hh + 4)), (190, 190, 190))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % 4) * (w + 4), (i // 4) * (hh + 4)))
    sheet.save(f"{OUT}/size_mock.png")
    print(f"{OUT}/size_mock.png", sheet.size)


if __name__ == "__main__":
    main()
