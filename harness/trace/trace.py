"""Tracing harness: draw curves given in head-radius units over the reference.

The whole point is that a curve is authored in the SAME coordinate system the
shape code uses, head-radius units with the origin at the head centre, so
"applying it to our head" is dropping the numbers into `character.py` rather
than a fitting problem. Tracing in image pixels and scaling afterwards was the
alternative and it makes every later edit a negotiation with a transform.

Calibration of `ref/satoshi-real.jpg` is eye centre to drawn chin: our eye sits
at 0.16 head radii and our chin ink at 1.05, so that run is 0.89 r, and both
ends are unambiguous ink in the reference. See the ear constants in
`character.py` for why eye-to-mouth is not usable here.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "src")

from PIL import Image, ImageDraw  # noqa: E402

from anime_character_creator import character as C  # noqa: E402
from anime_character_creator.presets import PRESETS  # noqa: E402
from anime_character_creator.skeleton import BUILDS, build_skeleton  # noqa: E402

REF = "ref/satoshi-real.jpg"
REF_EYE_Y, REF_CHIN_Y = 172.0, 260.0
REF_CX = 437.5                      # midpoint of the two pupils
REF_R = (REF_CHIN_Y - REF_EYE_Y) / 0.89
REF_CY = REF_EYE_Y - 0.16 * REF_R


def sample(start, segments, per=28):
    """A quadratic chain as a dense point list, in whatever units it came in."""
    pts = [start]
    prev = start
    for ctrl, end in segments:
        for i in range(1, per + 1):
            t = i / per
            pts.append(
                (
                    (1 - t) ** 2 * prev[0] + 2 * (1 - t) * t * ctrl[0] + t**2 * end[0],
                    (1 - t) ** 2 * prev[1] + 2 * (1 - t) * t * ctrl[1] + t**2 * end[1],
                )
            )
        prev = end
    return pts


def draw_chain(d, chain, cx, cy, r, colour, width=2, dash=6):
    pts = [(cx + x * r, cy + y * r) for x, y in sample(*chain)]
    for i in range(len(pts) - 1):
        if dash and (i // dash) % 2:
            continue
        d.line([pts[i], pts[i + 1]], fill=colour, width=width)


def on_ref(chains, box=(250, 20, 630, 320), zoom=3, dash=6):
    im = Image.open(REF).convert("RGB").crop(box)
    im = im.resize((im.width * zoom, im.height * zoom), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    cx = (REF_CX - box[0]) * zoom
    cy = (REF_CY - box[1]) * zoom
    for chain, colour in chains:
        draw_chain(d, chain, cx, cy, REF_R * zoom, colour, width=2 * zoom // 2 or 1, dash=dash)
    return im


def on_ours(chains, build="realistic", dash=6):
    p = PRESETS["satoshi"]
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    import cairosvg

    cairosvg.svg2png(bytestring=C.render_character(p, sk).encode(), write_to="out/trace/_t.png")
    im = Image.open("out/trace/_t.png").convert("RGB")
    scale = im.width / sk.canvas_w
    frac = 0.46 if build == "chibi" else 0.26
    box = (int(im.width * 0.14), 0, int(im.width * 0.86), int(im.height * frac))
    im = im.crop(box)
    zoom = 3
    im = im.resize((im.width * zoom, im.height * zoom), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    cx = (sk.head_cx * scale - box[0]) * zoom
    cy = (sk.head_cy * scale - box[1]) * zoom
    for chain, colour in chains:
        draw_chain(d, chain, cx, cy, sk.head_r * scale * zoom, colour, width=3, dash=dash)
    return im


def strip(images, path, pad=12):
    h = max(i.height for i in images)
    w = sum(i.width for i in images) + pad * (len(images) - 1)
    s = Image.new("RGB", (w, h), "white")
    x = 0
    for i in images:
        s.paste(i, (x, 0))
        x += i.width + pad
    s.save(path)
    print("wrote", path, s.size)
