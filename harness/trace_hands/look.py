"""D4d H3/H4: the traced hands on our figures, `hand_style="traced"`.

Top row: 4x crops round each hand (Katherina's grip and her relaxed hand,
Krista dressed and in the base layer, Gero); bottom row: the same figures
whole, mitten against traced. Writes `out/trace_hands/look.png`.
"""

import io
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/trace_hands"


def base_layer(p):
    off = [n for n in c.Outfit.__dataclass_fields__ if n.endswith("_color") and n not in ("underwear_color", "boot_color")]
    return replace(p, outfit=replace(p.outfit, **dict.fromkeys(off)))


def render(p, scale):
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB"), sk


def hand_crop(p, s, label):
    im, sk = render(p, 4)
    ux, uy = c._hand_centre(sk, p, s)
    hx, hy = (sk.head_cx + ux * sk.head_r) * 4, (sk.head_cy + uy * sk.head_r) * 4
    r = sk.head_r * 4
    t = im.crop((int(hx - 0.8 * r), int(hy - 0.9 * r), int(hx + 0.8 * r), int(hy + 0.8 * r)))
    ImageDraw.Draw(t).text((3, 3), label, fill=(200, 0, 0))
    return t


def main():
    cases = (
        ("katherina grip", PRESETS["katherina"], -1),
        ("katherina relaxed", PRESETS["katherina"], 1),
        ("krista", PRESETS["krista"], 1),
        ("krista base layer", base_layer(PRESETS["krista"]), 1),
        ("gero", PRESETS["gero"], -1),
    )
    top = [hand_crop(replace(p, hand_style="traced"), s, label) for label, p, s in cases]
    bottom = []
    for name in ("katherina", "krista", "gero"):
        for style in ("mitten", "traced"):
            im, _ = render(replace(PRESETS[name], hand_style=style), 1.0)
            ImageDraw.Draw(im).text((3, 3), f"{name} {style}", fill=(200, 0, 0))
            bottom.append(im)
    tw = max(t.width for t in top)
    th = max(t.height for t in top)
    bw = max(t.width for t in bottom)
    bh = max(t.height for t in bottom)
    W = max(len(top) * (tw + 4), len(bottom) * (bw + 4))
    sheet = Image.new("RGB", (W, th + bh + 10), (190, 190, 190))
    for i, t in enumerate(top):
        sheet.paste(t, (i * (tw + 4), 0))
    for i, t in enumerate(bottom):
        sheet.paste(t, (i * (bw + 4), th + 10))
    sheet.save(f"{OUT}/look.png")
    print(f"{OUT}/look.png", sheet.size)


if __name__ == "__main__":
    main()
