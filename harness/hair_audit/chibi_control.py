"""Hair-trace audit, test 3, the positive control: does hair drawn on a chibi
body transfer with the head calibration alone?

`katherina_grok` (the tall-chibi design reference `tall_chibi` was measured
off) has the same family of hair, long and straight, drawn on a body like
ours. Its hair is taken by colour (`proportions.py`'s rule, holes filled), laid
flat in one tone with an outline at its edge, and placed behind our figures by
one uniform scale and a translation, the witch hat's calibration (650, 481),
173.7 px per head radius. No body mapping at all, which is the point: if the
reference's body is ours, there is nothing to map. The whole hair goes behind
the figure and its head part (above the chin) over it as well, so the
curtains lie over the face's sides as they do on the reference, the same
layering `retarget.py` uses.

Prediction: on Katherina at 1.0 the hair hangs beside the arms the way it does
on the reference, without the cape and without pinching. At 0.8 and 1.3 the
fit should still hold sideways, and only the length should be wrong, since a
trace has one length and `_hair_fall` is what makes length follow the body.
Satoko and Linnea, other palettes and faces, wear Katherina's hat here only to
cover the crown the reference's brim hides.

Written to `out/hair_audit/chibi_control.png`.

    ./harness/run.sh harness/hair_audit/chibi_control.py
"""

import io
from dataclasses import replace

import cairosvg
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/hair_audit"
PX = 70
BOX = (-2.6, -2.6, 2.6, 4.4)
CHIBI = ("ref-local/katherina_grok/katherina_grok.jpg", (650.0, 481.0, 173.7))


def ref_hair() -> Image.Image:
    path, (ox, oy, s) = CHIBI
    im = np.asarray(Image.open(path).convert("RGB")).astype(int)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    ys = (np.arange(im.shape[0])[:, None] - oy) / s
    purple = (r >= 45) & (r - g >= 14) & (b >= 65) & (b > r * 1.1) & (ys > -1.2)
    purple = ndi.binary_opening(purple, iterations=1)
    lab, n = ndi.label(purple)
    sizes = ndi.sum(purple, lab, range(1, n + 1))
    keep = np.isin(lab, 1 + np.nonzero(sizes > 2000)[0])
    keep = ndi.binary_closing(keep, iterations=6)
    keep = ndi.binary_fill_holes(keep)
    edge = keep & ~ndi.binary_erosion(keep, iterations=4)
    rgba = np.zeros((*keep.shape, 4), np.uint8)
    rgba[keep] = (110, 110, 110, 255)
    rgba[edge] = (13, 13, 13, 255)
    k = PX / s
    out = Image.fromarray(rgba, "RGBA")
    out = out.resize((round(out.width * k), round(out.height * k)), Image.LANCZOS)
    W, H = round((BOX[2] - BOX[0]) * PX), round((BOX[3] - BOX[1]) * PX)
    frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    frame.paste(out, (round(-BOX[0] * PX - ox * k), round(-BOX[1] * PX - oy * k)))
    return frame


def figure(p) -> Image.Image:
    sk = c.skeleton_for(p)
    orig = (c._hair_mass, c._hair_front)
    c._hair_mass, c._hair_front = (lambda sk, p: ""), (lambda sk, p: "")
    try:
        svg = c.render_character(p, sk)
    finally:
        c._hair_mass, c._hair_front = orig
    k = PX / sk.head_r
    body = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=k))).convert("RGBA")
    W, H = round((BOX[2] - BOX[0]) * PX), round((BOX[3] - BOX[1]) * PX)
    frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    frame.paste(body, (round(-BOX[0] * PX - sk.head_cx * k), round(-BOX[1] * PX - sk.head_cy * k)))
    return frame, sk


def cases():
    kat = PRESETS["katherina"]
    kat = replace(kat, familiar_color=None, hair_tail=0.0, outfit=replace(kat.outfit, staff_color=None))
    hat = {k: getattr(kat.outfit, k) for k in ("hat_color", "hat_band_color")}
    out = [(f"katherina h{h}", replace(kat, height=h)) for h in (0.8, 1.0, 1.3)]
    for name in ("satoko", "linnea"):
        p = PRESETS[name]
        out.append((f"{name} (+hat)", replace(p, outfit=replace(p.outfit, **hat))))
    return out


def main() -> None:
    hair = ref_hair()
    tiles = []
    for label, p in cases():
        body, sk = figure(p)
        W, H = body.size
        t = Image.new("RGBA", (W, H), (255, 255, 255, 255))
        t.alpha_composite(hair)
        t.alpha_composite(body)
        front = np.asarray(hair).copy()
        front[round((1.0 - BOX[1]) * PX) :, :, 3] = 0
        t.alpha_composite(Image.fromarray(front, "RGBA"))
        d = ImageDraw.Draw(t)
        for yr in range(-2, 5):
            y = (yr - BOX[1]) * PX
            d.line([(0, y), (W, y)], fill=(190, 190, 190), width=1)
            d.text((2, y - 11), f"{yr}", fill=(200, 0, 0))
        belt = (sk.waist_y - sk.head_cy) / sk.head_r
        y = (belt - BOX[1]) * PX
        d.line([(0, y), (24, y)], fill=(0, 140, 0), width=3)
        d.text((4, 4), label, fill=(200, 0, 0))
        tiles.append(t.convert("RGB"))
    W, H = tiles[0].size
    sheet = Image.new("RGB", (W * len(tiles) + 6 * (len(tiles) - 1), H), (120, 120, 120))
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * (W + 6), 0))
    sheet.save(f"{OUT}/chibi_control.png")
    print(f"{OUT}/chibi_control.png {sheet.size}")


if __name__ == "__main__":
    main()
