"""A reference's hair on our figures, placed by its head calibration alone,
before anything is traced (`docs/detail-status.md`, D5 plan, between steps 2
and 3).

The hair is the reference's `segments/long-purple-hair.png`, an exact cut of
its composite (`segments.py`), at the offset `segments.py` found; the
calibration is `gate.py`'s (face-width scale, head centre from the chin). Laid
flat in each preset's own hair colour with an outline at its edge, it goes on
Katherina (hat, bat, staff and side tail off) at heights 0.8, 1.0 and 1.3, and
on Satoko and Linnea, at one head radius.

Two rows, because the composite cannot say which hair is in front of the body:
the top row draws the hair behind the figure with only its head part (above
the chin) over it; the bottom row draws all of it over the figure. The traced
cut lies between the two: its front locks over the body, the rest behind.

    ./harness/run.sh harness/hair_audit/preview_ref.py ref-local/katherina_grok_nohat

Written to `out/hair_audit/preview_<folder>.png`.
"""

import io
import json
import pathlib
import sys
from dataclasses import replace

sys.path.insert(0, "harness/hair_audit")

import cairosvg
import numpy as np
from PIL import Image, ImageColor, ImageDraw
from scipy import ndimage as ndi

import gate
from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/hair_audit"
PX = 70
BOX = (-2.4, -1.6, 2.4, 4.6)


def frame_size():
    return round((BOX[2] - BOX[0]) * PX), round((BOX[3] - BOX[1]) * PX)


def hair_mask(folder: pathlib.Path):
    """The hair segment's alpha in the sheet's frame, and the chin row."""
    comp = folder / f"{folder.name}.png"
    seg = json.load(open(f"{OUT}/segments_{folder.name}.json"))["long-purple-hair"]
    base = gate.measure(gate.BASE)
    m = gate.measure(str(comp))
    s, _, (ox, oy) = gate.calibrate(m, base)
    a = np.asarray(Image.open(folder / "segments" / "long-purple-hair.png").convert("RGBA"))[..., 3]
    full = np.zeros(np.asarray(Image.open(comp)).shape[:2], np.uint8)
    x, y = seg["at"]
    full[y : y + a.shape[0], x : x + a.shape[1]] = a
    k = PX / s
    im = Image.fromarray(full).resize((round(full.shape[1] * k), round(full.shape[0] * k)), Image.LANCZOS)
    W, H = frame_size()
    out = Image.new("L", (W, H), 0)
    out.paste(im, (round(-BOX[0] * PX - ox * k), round(-BOX[1] * PX - oy * k)))
    return np.asarray(out) > 128


def flat(mask, colour):
    edge = mask & ~ndi.binary_erosion(mask, iterations=2)
    rgba = np.zeros((*mask.shape, 4), np.uint8)
    rgba[mask] = (*ImageColor.getrgb(colour), 255)
    rgba[edge] = (13, 13, 13, 255)
    return Image.fromarray(rgba, "RGBA")


def figure(p):
    sk = c.skeleton_for(p)
    orig = (c._hair_mass, c._hair_front)
    c._hair_mass, c._hair_front = (lambda sk, p: ""), (lambda sk, p: "")
    try:
        svg = c.render_character(p, sk)
    finally:
        c._hair_mass, c._hair_front = orig
    k = PX / sk.head_r
    body = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=k))).convert("RGBA")
    W, H = frame_size()
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(body, (round(-BOX[0] * PX - sk.head_cx * k), round(-BOX[1] * PX - sk.head_cy * k)))
    return out, sk


def cases():
    kat = PRESETS["katherina"]
    kat = replace(
        kat,
        familiar_color=None,
        hair_tail=0.0,
        outfit=replace(kat.outfit, hat_color=None, hat_band_color=None, staff_color=None),
    )
    out = [(f"katherina h{h}", replace(kat, height=h)) for h in (0.8, 1.0, 1.3)]
    out += [(name, PRESETS[name]) for name in ("satoko", "linnea")]
    return out


def main() -> None:
    folder = pathlib.Path(sys.argv[1].rstrip("/"))
    mask = hair_mask(folder)
    chin_row = round((1.0 - BOX[1]) * PX)
    rows = []
    for front_all in (False, True):
        tiles = []
        for label, p in cases():
            body, sk = figure(p)
            hair = flat(mask, p.hair_color)
            W, H = body.size
            t = Image.new("RGBA", (W, H), (255, 255, 255, 255))
            if front_all:
                t.alpha_composite(body)
                t.alpha_composite(hair)
            else:
                t.alpha_composite(hair)
                t.alpha_composite(body)
                head = np.asarray(hair).copy()
                head[chin_row:, :, 3] = 0
                t.alpha_composite(Image.fromarray(head, "RGBA"))
            d = ImageDraw.Draw(t)
            for yr in range(-1, 5):
                y = (yr - BOX[1]) * PX
                d.line([(0, y), (12, y)], fill=(200, 0, 0), width=1)
                d.text((14, y - 6), f"{yr}", fill=(200, 0, 0))
            belt = (sk.waist_y - sk.head_cy) / sk.head_r
            y = (belt - BOX[1]) * PX
            d.line([(W - 24, y), (W, y)], fill=(0, 140, 0), width=3)
            d.text((4, 4), f"{label}, {'all in front' if front_all else 'behind, head in front'}", fill=(200, 0, 0))
            tiles.append(t.convert("RGB"))
        rows.append(tiles)
    W, H = rows[0][0].size
    n = len(rows[0])
    sheet = Image.new("RGB", (W * n + 6 * (n - 1), H * 2 + 6), (120, 120, 120))
    for j, tiles in enumerate(rows):
        for i, t in enumerate(tiles):
            sheet.paste(t, (i * (W + 6), j * (H + 6)))
    path = f"{OUT}/preview_{folder.name}.png"
    sheet.save(path)
    print(path, sheet.size)


if __name__ == "__main__":
    main()
