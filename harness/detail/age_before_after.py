"""D3 of `docs/detail-plan.md`: every preset's whole figure, as it is now
beside the proposed face age (`age_lineup.PROPOSED`), dressed as the preset
is, hats and props included. Each pair shares one render scale, so the only
difference is the face.

Writes `out/detail/age_before_after.png`.
"""

import io
import os
import sys
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from age_lineup import BAKED, PROPOSED  # noqa: E402

from anime_character_creator import character as c  # noqa: E402
from anime_character_creator.presets import PRESETS  # noqa: E402

OUT = "out/detail"
SCALE = 1.0
PER_ROW = 4


def figure(p: c.CharacterParams, label: str) -> Image.Image:
    svg = c.render_character(p, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGB")
    ImageDraw.Draw(im).text((4, 4), label, fill=(200, 0, 0))
    return im


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    pairs = []
    for n, age in PROPOSED.items():
        now = figure(PRESETS[n], f"{n}: now" + (f" (aged {BAKED[n]} baked in)" if n in BAKED else ""))
        new = figure(replace(PRESETS[n], face_age=age), f"{n}: age {age + BAKED.get(n, 0.0):.2f}")
        pair = Image.new("RGB", (now.width + new.width + 2, now.height), (150, 150, 150))
        pair.paste(now, (0, 0))
        pair.paste(new, (now.width + 2, 0))
        pairs.append(pair)
    pw = max(p.width for p in pairs)
    ph = max(p.height for p in pairs)
    rows = (len(pairs) + PER_ROW - 1) // PER_ROW
    gap = 14
    sheet = Image.new("RGB", (PER_ROW * (pw + gap), rows * (ph + gap)), (60, 60, 60))
    for i, p in enumerate(pairs):
        sheet.paste(p, ((i % PER_ROW) * (pw + gap), (i // PER_ROW) * (ph + gap)))
    sheet.save(f"{OUT}/age_before_after.png")
    print(f"{OUT}/age_before_after.png", sheet.size)


if __name__ == "__main__":
    main()
