"""The cover at a few head sizes (`docs/satoshi-tall-chibi-plan.md`, "Head size"),
so the head is judged where it is largest.

The head is scaled against a fixed body exactly as in `head_size_variants.py`
(chin fixed, headroom added above, everything drawn off `head_r` follows), and
the cover's own `_placement` then fits the taller canvas to the page as it
always does, so a bigger head comes with a slightly smaller body rather than a
head on the title.

Writes `out/head_size_covers.png`.
"""

import io
from dataclasses import replace

import cairosvg
import numpy as np
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator import cover as cv

SCALES = (1.0, 1.1, 1.2)
_orig_skeleton_for = cv.skeleton_for


def head_scaled(sk, s):
    r = sk.head_r
    chin = sk.head_cy + r
    delta = chin * (s - 1.0) if s > 1.0 else 0.0
    r2 = r * s
    cy2 = chin - r2 + delta
    ys = ("shoulder_y", "waist_y", "hip_y", "hem_y", "knee_y", "ankle_y", "foot_y")
    return replace(
        sk,
        canvas_h=sk.canvas_h + delta,
        head_r=r2,
        head_cy=cy2,
        neck_y=cy2 + r2 * 0.85,
        **{name: getattr(sk, name) + delta for name in ys},
    )


def render(s):
    cv.skeleton_for = lambda character, heads=None: head_scaled(_orig_skeleton_for(character, heads), s)
    try:
        p = cv.CoverParams()
        svg = cv.render_cover(p)
        sk, character, k, x, y = cv._placement(p)
    finally:
        cv.skeleton_for = _orig_skeleton_for
    png = cairosvg.svg2png(bytestring=svg.encode(), scale=0.5)
    im = Image.open(io.BytesIO(png)).convert("RGB")
    # Hair top on the page: the top of the figure's own silhouette.
    doc = c.render_character(character, sk)
    fig = np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=doc.encode()))).convert("RGBA"))
    top = int(np.nonzero(fig[:, :, 3].any(1))[0].min())
    return im, y + top * k, 2 * sk.head_r * k


def main():
    p = cv.CoverParams()
    size = p.height * 0.072
    title_bottom = p.height * 0.115 + 2 * size * 1.16
    tiles = []
    for s in SCALES:
        im, hair_top, head_px = render(s)
        print(
            f"head x{s:.1f}: hair top {hair_top:.0f}px, {hair_top - title_bottom:.0f}px under the title,"
            f" head {head_px:.0f}px across"
        )
        ImageDraw.Draw(im).text((8, 4), f"head x{s:.1f}" + (" (current)" if s == 1.0 else ""), fill=(255, 255, 0))
        tiles.append(im)
    w, h = tiles[0].size
    sheet = Image.new("RGB", (w * len(tiles) + 10 * (len(tiles) - 1), h), (230, 230, 230))
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * (w + 10), 0))
    sheet.save("out/head_size_covers.png")
    print(sheet.size)


main()
