"""Satoshi on the default tall chibi with the head scaled against a fixed body,
to judge how much of the chibi look a smaller head costs
(`docs/satoshi-tall-chibi-plan.md`, "Head size").

A body profile's landmarks are in head radii, so changing `heads` rescales the
whole figure and changes nothing about the proportion. This scales only the
head: the body's anchors stay where they are in pixels, the chin stays put, the
head grows or shrinks about it, and the canvas gains headroom above so the hair
does not clip. Everything drawn off `head_r` (the face, the hair, the outline
weight) follows the head.

Scales are against the current head: 1.0 is the default body as it ships, and
about 1.39 is the shared chibi's head on this body.

Writes `out/head_size_variants.png`: the top row keeps the body the same size,
bottom-aligned, so the head is the only thing that changes; the bottom row
scales each to the same overall height, which is how it would sit on a canvas.
"""

import io
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

SCALES = (0.85, 1.0, 1.1, 1.2, 1.4)
K = 2


def variant(preset, s):
    p = PRESETS[preset]
    sk = c.skeleton_for(p)
    r = sk.head_r
    chin = sk.head_cy + r
    delta = chin * (s - 1.0) if s > 1.0 else 0.0
    r2 = r * s
    cy2 = chin - r2 + delta
    ys = ("shoulder_y", "waist_y", "hip_y", "hem_y", "knee_y", "ankle_y", "foot_y")
    shifted = {name: getattr(sk, name) + delta for name in ys}
    sk2 = replace(
        sk,
        canvas_h=sk.canvas_h + delta,
        head_r=r2,
        head_cy=cy2,
        neck_y=cy2 + r2 * 0.85,
        **shifted,
    )
    svg = c.render_character(p, sk2, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=K))).convert("RGB")
    return im, sk2


def main():
    tiles = [(s, *variant("satoshi", s)) for s in SCALES]
    pad, label = 20, 30
    tallest = max(im.height for _, im, _ in tiles)
    w = tiles[0][1].width
    sheet = Image.new("RGB", ((w + pad) * len(tiles) + pad, tallest + label + 30 + 620 + label), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 6), "same body size, bottom-aligned (only the head changes)", fill=(0, 0, 0))
    for i, (s, im, sk) in enumerate(tiles):
        x = pad + i * (w + pad)
        sheet.paste(im, (x, label + tallest - im.height))
        d.text((x, label + 4), f"head x{s:.2f}" + (" (current)" if s == 1.0 else ""), fill=(200, 0, 0))
    y0 = label + tallest + 30
    d.text((pad, y0 - 22), "same overall height (how each would sit on the canvas)", fill=(0, 0, 0))
    for i, (s, im, sk) in enumerate(tiles):
        x = pad + i * (w + pad)
        h = 620
        scaled = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
        sheet.paste(scaled, (x + (w - scaled.width) // 2, y0))
    sheet.save("out/head_size_variants.png")
    print(sheet.size)


main()
