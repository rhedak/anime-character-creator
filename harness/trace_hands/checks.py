"""D4d H4: the traced hands' remaining checks, `hand_style="traced"`.

Krista at heights 0.8 and 1.3; an arm swung out (her right, 30 degrees);
a very different skin tone; Katherina's grip with her arm swung further; and
Krista and Katherina at the smallest size a chapter insert shows a figure
(head radius about 21 px, 1x and 2x). Writes `out/trace_hands/checks.png`.
"""

import io
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS


def render(p, scale):
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB"), sk


def arms(p, label):
    im, sk = render(p, 2)
    r = sk.head_r * 2
    t = im.crop((int(sk.head_cx * 2 - 2.2 * r), int(sk.shoulder_y * 2), int(sk.head_cx * 2 + 2.2 * r), int(sk.hip_y * 2 + 1.4 * r)))
    ImageDraw.Draw(t).text((3, 3), label, fill=(200, 0, 0))
    return t


def small(p, label):
    sk = c.skeleton_for(p)
    tiles = []
    for d in (1, 2):
        im, _ = render(p, 21.0 * d / sk.head_r * 4)
        im = im.resize((im.width // 4, im.height // 4), Image.LANCZOS)
        tiles.append(im.resize((im.width * 2 // d, im.height * 2 // d), Image.NEAREST))
    out = Image.new("RGB", (tiles[0].width + tiles[1].width + 4, tiles[0].height), (255, 255, 255))
    out.paste(tiles[0], (0, 0))
    out.paste(tiles[1], (tiles[0].width + 4, 0))
    ImageDraw.Draw(out).text((3, 3), label, fill=(200, 0, 0))
    return out


def main():
    k = replace(PRESETS["krista"], hand_style="traced")
    kat = replace(PRESETS["katherina"], hand_style="traced")
    row1 = [
        arms(replace(k, height=0.8), "krista h0.8"),
        arms(replace(k, height=1.3), "krista h1.3"),
        arms(replace(k, right_arm_out=30.0), "krista arm out 30"),
        arms(replace(k, skin_tone="#6b4a35"), "dark skin"),
        arms(replace(kat, right_arm_out=kat.right_arm_out + 12), "katherina arm further out"),
    ]
    row2 = [small(k, "krista insert 1x, 2x (shown 2x)"), small(kat, "katherina insert 1x, 2x (shown 2x)")]
    w1 = sum(t.width for t in row1) + 4 * len(row1)
    h1 = max(t.height for t in row1)
    w2 = sum(t.width for t in row2) + 4 * len(row2)
    h2 = max(t.height for t in row2)
    sheet = Image.new("RGB", (max(w1, w2), h1 + h2 + 8), (190, 190, 190))
    x = 0
    for t in row1:
        sheet.paste(t, (x, 0))
        x += t.width + 4
    x = 0
    for t in row2:
        sheet.paste(t, (x, h1 + 8))
        x += t.width + 4
    sheet.save("out/trace_hands/checks.png")
    print("out/trace_hands/checks.png", sheet.size)


if __name__ == "__main__":
    main()
