"""D1 of `docs/detail-plan.md`: how heavy should the line be? A study for the
owner to pick from; nothing in `src/` changes.

Each variant rescales the drawn `stroke-width` attributes of a render, and
nothing else, so the geometry that reads `_stroke_w` (offsets, radii,
thresholds, clamps: `docs/detail-inventory/strokes.md`) stays where it is,
which is what the change itself will do. A stroke is a silhouette when its
width is within 5% of `_stroke_w` or above it, interior otherwise (the
inventory: silhouettes draw at the full weight on 37 of 53 sites, interior
lines at 0.4 to 0.7 of it). A variant is `(silhouette scale, interior scale)`:

- (1.0, 1.0) today, 0.043 head radii;
- (0.75, 0.75) and (0.6, 0.6): lighter throughout, the ratio kept;
- (0.75, 0.55) and (0.6, 0.4): lighter, with the interior lines lighter
  still relative to the outline, as the reference draws them.

Two sheets, in `out/detail/`:

- `line_weight_full.png`: the head and torso of four characters at twice
  their render size, one row per variant;
- `line_weight_small.png`: the same figures at the smallest size
  `../valley_of_mist` shows them (head radius about 21 px, `detail-status.md`),
  at 1x and 2x.
"""

import io
import os
import re

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"
NAMES = ("satoko", "krista", "keiko", "katherina")
VARIANTS = ((1.0, 1.0), (0.75, 0.75), (0.6, 0.6), (0.75, 0.55), (0.6, 0.4))
SMALL_HEAD_R = 21.0
CARD = (242, 242, 240)


def reweighted(svg: str, sw: float, sil: float, inner: float) -> str:
    def one(m: re.Match) -> str:
        w = float(m.group(1))
        return f'stroke-width="{w * (sil if w >= sw * 0.95 else inner):.2f}"'

    return re.sub(r'stroke-width="([0-9.]+)"', one, svg)


def render(name: str, sil: float, inner: float, scale: float) -> tuple[Image.Image, c.Skeleton]:
    p = PRESETS[name]
    sk = c.skeleton_for(p)
    svg = reweighted(c.render_character(p, sk), c._stroke_w(sk), sil, inner)
    png = cairosvg.svg2png(bytestring=svg.encode(), scale=scale)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    card = Image.new("RGBA", im.size, CARD + (255,))
    return Image.alpha_composite(card, im).convert("RGB"), sk


def label(img: Image.Image, text: str) -> Image.Image:
    out = Image.new("RGB", (img.width, img.height + 16), (200, 200, 200))
    out.paste(img, (0, 16))
    ImageDraw.Draw(out).text((3, 2), text, fill=(0, 0, 0))
    return out


def grid(rows: list[list[Image.Image]], pad: int = 6) -> Image.Image:
    tw = max(t.width for r in rows for t in r)
    th = max(t.height for r in rows for t in r)
    sheet = Image.new("RGB", (pad + len(rows[0]) * (tw + pad), pad + len(rows) * (th + pad)), (200, 200, 200))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            sheet.paste(t, (pad + i * (tw + pad), pad + j * (th + pad)))
    return sheet


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    full, small = [], []
    for sil, inner in VARIANTS:
        tag = f"outline x{sil}, interior x{inner}"
        row, srow = [], []
        for name in NAMES:
            im, sk = render(name, sil, inner, 2.0)
            r, cx, cy = sk.head_r * 2, sk.head_cx * 2, sk.head_cy * 2
            crop = im.crop((int(cx - 1.9 * r), int(cy - 1.4 * r), int(cx + 1.9 * r), int(sk.hip_y * 2)))
            row.append(label(crop, f"{name}: {tag}"))
            tiles = []
            for density in (1, 2):
                k = SMALL_HEAD_R * density / sk.head_r
                big, _ = render(name, sil, inner, k * 4)
                tiles.append(big.resize((int(big.width / 4), int(big.height / 4)), Image.LANCZOS))
            both = Image.new("RGB", (tiles[0].width + tiles[1].width + 4, tiles[1].height), CARD)
            both.paste(tiles[0], (0, tiles[1].height - tiles[0].height))
            both.paste(tiles[1], (tiles[0].width + 4, 0))
            srow.append(label(both, f"{name}: {tag}  (1x, 2x)"))
        full.append(row)
        small.append(srow)
    grid(full).save(f"{OUT}/line_weight_full.png")
    grid(small).save(f"{OUT}/line_weight_small.png")
    print(f"{OUT}/line_weight_full.png", f"{OUT}/line_weight_small.png")


if __name__ == "__main__":
    main()
