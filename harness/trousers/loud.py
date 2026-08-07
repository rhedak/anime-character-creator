"""The rebuilt trousers on palettes well outside the ones they were tuned on.

The seams are `shade()` derivations of the trouser colour, so they are the part
that can come out wrong outside the default hue range: on a light garment a
darker seam has to stay visible against it, and on a near-black one it has to
stay distinguishable from the outline it sits beside.
"""

from __future__ import annotations

import sys
from dataclasses import replace

sys.path.insert(0, "src")

import cairosvg  # noqa: E402
from PIL import Image  # noqa: E402

from anime_character_creator import character as C  # noqa: E402
from anime_character_creator.presets import PRESETS  # noqa: E402
from anime_character_creator.skeleton import BUILDS, build_skeleton  # noqa: E402

PALETTES = [
    ("default", None, None),
    ("near black", "#17181c", "#2b2018"),
    ("bone on white", "#e8e4d6", "#cfc6b0"),
    ("hot pink", "#c8317a", "#6d2f8c"),
]
tiles = []
for label, trouser, belt in PALETTES:
    for build in ("chibi", "realistic"):
        base = PRESETS["satoshi"]
        outfit = base.outfit
        if trouser is not None:
            outfit = replace(outfit, trouser_color=trouser, belt_color=belt)
        p = replace(base, outfit=outfit)
        sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
        cairosvg.svg2png(
            bytestring=C.render_character(p, sk).encode(), write_to="out/trousers/_l.png"
        )
        im = Image.open("out/trousers/_l.png").convert("RGB")
        w, h = im.size
        top = 0.62 if build == "chibi" else 0.40
        t = im.crop((int(w * 0.20), int(h * top), int(w * 0.80), h))
        tiles.append(t.resize((int(t.width * 320 / t.height), 320), Image.LANCZOS))
W = sum(t.width for t in tiles) + 8 * len(tiles)
sheet = Image.new("RGB", (W, 320), "white")
x = 0
for t in tiles:
    sheet.paste(t, (x, 0))
    x += t.width + 8
sheet.save("out/trousers/loud.png")
print("wrote out/trousers/loud.png", [p[0] for p in PALETTES])
