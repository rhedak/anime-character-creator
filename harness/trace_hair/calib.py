"""The reference's hair against ours, in head radii (the trace skill's step 2).

`ref-local/katherina_grok_real/segments/purple-hair.png` is a pixel-exact cut
of the composite's hair at (435, 200): matched on 4000 sampled pixels, then
every opaque pixel, mean colour difference 0.6 and none over 20. So the hair's
mask needs no segmenting; its holes are where the hat, the face, the bat and
the body cover it.

The calibration is D0's (`harness/detail/baseline.py`): our face measured off
our render, the reference's face component, the scale from face width (83.9 px
per head radius). The second scale, widest row to chin, disagrees by about
40% by design: the reference's lower face is longer.

Writes `out/trace_hair/calib.png`: the reference's hair mask (purple) over our
Katherina's hair (grey, the hat off), both in head radii, with our face, our
shoulders and the reference's brim line marked; and prints the hair's extent
per row, both ways.
"""

import dataclasses
import sys

sys.path.insert(0, "harness/detail")

import numpy as np
from PIL import Image, ImageDraw

import baseline
from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

REF = "ref-local/katherina_grok_real/katherina_grok_real.png"
SEG = "ref-local/katherina_grok_real/segments/purple-hair.png"
SEG_AT = (435, 200)
OUT = "out/trace_hair"
PX = 60  # our plot's pixels per head radius
BOX = (-3.0, -1.6, 3.0, 7.0)


def ref_mask() -> np.ndarray:
    ref = Image.open(REF)
    s = np.asarray(Image.open(SEG).convert("RGBA"))[..., 3] > 128
    m = np.zeros((ref.height, ref.width), bool)
    m[SEG_AT[1] : SEG_AT[1] + s.shape[0], SEG_AT[0] : SEG_AT[0] + s.shape[1]] = s
    return m


def ours() -> tuple[np.ndarray, c.Skeleton]:
    import io

    import cairosvg

    p = PRESETS["katherina"]
    p = dataclasses.replace(p, outfit=dataclasses.replace(p.outfit, hat_color=None))
    sk = c.skeleton_for(p)
    style = c.HAIRSTYLES[p.hairstyle]
    start, segs = style.mass(c._hair_fall(sk, p))
    d = c._curve(0, 0, PX, start, segs)
    w, h = int((BOX[2] - BOX[0]) * PX), int((BOX[3] - BOX[1]) * PX)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
        f'<g transform="translate({-BOX[0] * PX} {-BOX[1] * PX})"><path d="{d}" fill="black" /></g></svg>'
    )
    a = np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert("RGBA"))[..., 3] > 128
    return a, sk


def main() -> None:
    lines: list[str] = []
    ox, oy, s = baseline.calibrate(lines)
    print("\n".join(lines))
    m = ref_mask()
    w, h = int((BOX[2] - BOX[0]) * PX), int((BOX[3] - BOX[1]) * PX)
    ys, xs = np.mgrid[0:h, 0:w]
    hx, hy = xs / PX + BOX[0], ys / PX + BOX[1]
    rx, ry = (ox + hx * s).astype(int), (oy + hy * s).astype(int)
    inside = (rx >= 0) & (rx < m.shape[1]) & (ry >= 0) & (ry < m.shape[0])
    rm = np.zeros((h, w), bool)
    rm[inside] = m[ry[inside], rx[inside]]
    om, sk = ours()

    img = np.full((h, w, 3), 255, np.uint8)
    img[om] = (190, 190, 190)
    img[rm] = (120, 60, 170)
    img[rm & om] = (80, 30, 110)
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)

    def P(x, y):
        return ((x - BOX[0]) * PX, (y - BOX[1]) * PX)

    d.ellipse([*P(-1, -1), *P(1, 1)], outline=(0, 0, 0))
    r = sk.head_r
    for name, y in (("shoulder", sk.shoulder_y), ("waist", sk.waist_y), ("hip", sk.hip_y)):
        yy = (y - sk.head_cy) / r
        d.line([P(BOX[0], yy), P(BOX[2], yy)], fill=(0, 140, 0))
        d.text(P(BOX[0] + 0.05, yy - 0.2), f"our {name} {yy:.2f}", fill=(0, 120, 0))
        sx = sk.shoulder_half_w / r
        if name == "shoulder":
            d.line([P(-sx, yy - 0.1), P(-sx, yy + 0.1)], fill=(0, 140, 0), width=3)
            d.line([P(sx, yy - 0.1), P(sx, yy + 0.1)], fill=(0, 140, 0), width=3)
    brim = (SEG_AT[1] - oy) / s
    d.line([P(BOX[0], brim), P(BOX[2], brim)], fill=(200, 0, 0))
    d.text(P(BOX[0] + 0.05, brim - 0.2), f"segment top (the brim) {brim:.2f}", fill=(200, 0, 0))
    im.save(f"{OUT}/calib.png")

    print("row (head radii): reference hair x range | ours")
    for y in np.arange(-1.2, 6.01, 0.4):
        j = int((y - BOX[1]) * PX)
        a, b = np.nonzero(rm[j])[0], np.nonzero(om[j])[0]
        f = (lambda v: f"{v.min() / PX + BOX[0]:+.2f}..{v.max() / PX + BOX[0]:+.2f}" if len(v) else "none")
        print(f"  {y:+.1f}: {f(a):>14} | {f(b)}")


if __name__ == "__main__":
    main()
