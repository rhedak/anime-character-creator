"""D4b of `docs/detail-plan.md`, round two: the limb taper following the height.

The owner's call on the first study: the hands follow the wrists, and the
taper grows with the height rather than being one amount for everyone, so a
short figure keeps the chibi's tube of an arm and a tall one tapers:
`_LIMB_TAPER = clamp((height - 0.8) / 0.5, 0, 1)`, 0 at 0.8, 0.4 at 1.0 (where
every preset stands), 1 at 1.3.

Two sheets in `out/detail/`: `taper_sweep.png`, whole figures at heights 0.8
to 1.3 in steps of 0.1 (Krista's base layer, Satoshi, Keiko, Satoko), one head
size, feet on one line; and `taper_sweep_arms.png`, the base layer's arms and
hands at 2x across the same heights.

A record: the taper is now `Skeleton.limb_taper`, set from the height
(`character._limb_taper_at`), and the `_LIMB_TAPER` this patches is gone, so
it no longer draws what it did.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"
HEIGHTS = (0.8, 0.9, 1.0, 1.1, 1.2, 1.3)


def taper_for(h: float) -> float:
    return min(1.0, max(0.0, (h - 0.8) / 0.5))


def cases():
    krista = PRESETS["krista"]
    off = [n for n in c.Outfit.__dataclass_fields__ if n.endswith("_color") and n not in ("underwear_color", "boot_color")]
    base = replace(krista, outfit=replace(krista.outfit, **dict.fromkeys(off)))
    return [("krista base layer", base), ("satoshi", PRESETS["satoshi"]), ("keiko", PRESETS["keiko"]), ("satoko", PRESETS["satoko"])]


def render(p: c.CharacterParams, scale: float) -> tuple[Image.Image, c.Skeleton]:
    c._LIMB_TAPER = taper_for(p.height)
    try:
        sk = c.skeleton_for(p)
        svg = c.render_character(p, sk, background="#ffffff")
    finally:
        c._LIMB_TAPER = 0.0
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB"), sk


def grid(rows, path):
    tw = max(t.width for r in rows for t in r)
    th = max(t.height for r in rows for t in r)
    sheet = Image.new("RGB", (len(rows[0]) * (tw + 3), len(rows) * (th + 5)), (190, 190, 190))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            sheet.paste(t, (i * (tw + 3), j * (th + 5)))
    sheet.save(path)
    print(path, sheet.size)


def main():
    os.makedirs(OUT, exist_ok=True)
    ref_r = c.skeleton_for(PRESETS["satoko"]).head_r
    rows = []
    for name, p in cases():
        row = []
        for h in HEIGHTS:
            im, sk = render(replace(p, height=h), 1.0)
            s = ref_r / sk.head_r
            im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
            foot, cx = sk.foot_y * s, sk.head_cx * s
            w, top = int(2.9 * ref_r), int(foot - 11.5 * ref_r)
            tile = Image.new("RGB", (w, int(12.0 * ref_r)), (255, 255, 255))
            tile.paste(im.crop((int(cx - w / 2), max(0, top), int(cx + w / 2), min(im.height, int(foot + 0.4 * ref_r)))), (0, max(0, -top)))
            ImageDraw.Draw(tile).text((3, 3), f"{name} h{h} taper {taper_for(h):.1f}", fill=(200, 0, 0))
            row.append(tile)
        rows.append(row)
    grid(rows, f"{OUT}/taper_sweep.png")

    arms = []
    base = cases()[0][1]
    for h in HEIGHTS:
        im, sk = render(replace(base, height=h), 2.0)
        k = 2.0
        r, cx = sk.head_r * k, sk.head_cx * k
        crop = im.crop((int(cx - 2.0 * r), int(sk.shoulder_y * k), int(cx + 2.0 * r), int(sk.hip_y * k + 0.9 * r)))
        s = 2.0 * ref_r * 2 / crop.width * 1.0
        crop = crop.resize((int(4.0 * ref_r * 2 * 0.6), int(crop.height * (4.0 * ref_r * 2 * 0.6) / crop.width)), Image.LANCZOS)
        ImageDraw.Draw(crop).text((3, 3), f"h{h} taper {taper_for(h):.1f}", fill=(200, 0, 0))
        arms.append(crop)
    grid([arms], f"{OUT}/taper_sweep_arms.png")


if __name__ == "__main__":
    main()
