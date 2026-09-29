"""The traced hair (`trace_hair.py`'s `hair.json`) on our Katherina, for the
owner. Nothing in `src/` changes: `_hair_mass` and `_hair_front` are stood in
for while rendering.

The mass is drawn where `_hair_mass` draws it, behind the body, filled and
outlined; the front piece where `_hair_front` draws it, over the body, filled
without a stroke, its drawn edges (all of its outline but the cut across the
back hair) stroked on top. The reference's interior lines, if drawn, go on the
piece they lie on, clipped to it, at the strands' weight.

Rows: today; traced, no interior lines; traced with the reference's lines.
Columns: Katherina with her hat, without it, and Linnea (another palette on
the same cut). Written to `out/trace_hair/`: `preview.png` (heads at 3x),
`preview_full.png` (whole figures), `preview_small.png` (the insert size,
head radius 21 px, 1x and 2x, shown 2x).
"""

import io
import json
import sys
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/trace_hair"
# `--as-is`: `trace_hair.py --as-is`'s unmapped trace, on Katherina at the
# tallest height (the owner, 2026-09-29), written as `preview_asis*.png`.
AS_IS = "--as-is" in sys.argv
# `--hair-only`: `harness/hair_only/trace.py`'s trace of the owner's hair-only
# reference, the same view as `--as-is`, written as `preview_hair_only*.png`.
HAIR_ONLY = "--hair-only" in sys.argv
AS_IS = AS_IS or HAIR_ONLY
TAG = "_hair_only" if HAIR_ONLY else "_asis" if AS_IS else ""
HEIGHT = 1.3 if AS_IS else None
HAIR = json.load(open("out/hair_only/hair.json" if HAIR_ONLY else f"{OUT}/hair{TAG}.json"))
# The as-is preview takes its line work from `lines.py` (the black-hat trace),
# in the same unmapped head radii. The hair clip's ring is traced there too and
# is dropped: our figure draws its own clip.
RING = ((0.65, -0.56), (0.26, 0.17))


def _on_ring(chain):
    (cx, cy), (rx, ry) = RING
    pts = [chain[0], *[e for _, e in chain[1]]]
    return sum(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1 for x, y in pts) > len(pts) / 2


def _in_front(chain) -> bool:
    """Whether a line's middle lies on the front piece (a raster of its chain)."""
    from PIL import ImageDraw as D

    k, box = 100, (-3.0, -2.0, 3.0, 5.0)
    im = Image.new("1", (int((box[2] - box[0]) * k), int((box[3] - box[1]) * k)), 0)
    pts = [((x - box[0]) * k, (y - box[1]) * k) for x, y in c_sample(HAIR["front"])]
    D.Draw(im).polygon(pts, fill=1)
    pts = [chain[0], *[e for _, e in chain[1]]]
    x, y = pts[len(pts) // 2]
    return bool(im.getpixel((int((x - box[0]) * k), int((y - box[1]) * k))))


def c_sample(chain, n=8):
    (x0, y0), segs = chain
    out, p = [(x0, y0)], (x0, y0)
    for (cx, cy), (ex, ey) in segs:
        for i in range(1, n + 1):
            t = i / n
            out.append(((1 - t) ** 2 * p[0] + 2 * (1 - t) * t * cx + t * t * ex, (1 - t) ** 2 * p[1] + 2 * (1 - t) * t * cy + t * t * ey))
        p = (ex, ey)
    return out


if AS_IS and not HAIR_ONLY:
    HAIR["strands"] = [
        {"chain": ch, "front": _in_front(ch)} for ch in HAIR["lines"] if not _on_ring(ch)
    ]
ORIG = (c._hair_mass, c._hair_front)


def stroke(sk, chain, w, clip=None):
    d = c._curve(sk.head_cx, sk.head_cy, sk.head_r, *chain, close=False)
    cp = f' clip-path="url(#{clip})"' if clip else ""
    return f'<path d="{d}" fill="none" stroke="{c.OUTLINE}" stroke-width="{w:.2f}" stroke-linecap="round" stroke-linejoin="round"{cp} />'


def pieces_d(sk, key):
    """A shape's path: its one outline, or, where the trace kept pieces and
    holes (`<key>_parts`), all of them, for an even-odd fill."""
    ps = HAIR.get(f"{key}_parts") or []
    if not ps:
        return c._curve(sk.head_cx, sk.head_cy, sk.head_r, *HAIR[key]), []
    ds, extra = [], []
    largest = max(range(len(ps)), key=lambda i: len(ps[i][0][1]))
    for i, (outer, holes) in enumerate(ps):
        ds.append(c._curve(sk.head_cx, sk.head_cy, sk.head_r, *outer))
        if i != largest:
            extra.append(outer)
        for h in holes:
            ds.append(c._curve(sk.head_cx, sk.head_cy, sk.head_r, *h))
            extra.append(h)
    return " ".join(ds), extra


def traced(lines: bool, ref_weight: bool = False):
    def line_w(sw, sk):
        # The segment's lines measure a median 2 px and a 75th percentile 4 px
        # at 88.7 px per head radius (`audit.py`): about 0.028 head radii, near
        # its outline's weight, where ours are drawn under half of the outline.
        return HAIR.get("line_width_r", 0.028) * sk.head_r if ref_weight else c._interior_w(sw, 0.55)

    def mass(sk, p):
        sw = c._stroke_w(sk)
        d, _ = pieces_d(sk, "mass")
        parts = [f'<defs><clipPath id="traced-mass"><path d="{d}" clip-rule="evenodd" /></clipPath></defs>']
        parts.append(f'<path d="{d}" fill="{p.hair_color}" fill-rule="evenodd" />')
        if lines:
            for st in HAIR["strands"]:
                if not st["front"]:
                    parts.append(stroke(sk, st["chain"], line_w(sw, sk), "traced-mass"))
        parts.append(
            f'<path d="{d}" fill="none" stroke="{c.OUTLINE}" stroke-width="{c._outline_w(sw):.2f}" stroke-linejoin="round" />'
        )
        return "".join(parts)

    def front(sk, p):
        sw = c._stroke_w(sk)
        d, extra = pieces_d(sk, "front")
        parts = [f'<defs><clipPath id="traced-front"><path d="{d}" clip-rule="evenodd" /></clipPath></defs>']
        parts.append(f'<path d="{d}" fill="{p.hair_color}" fill-rule="evenodd" />')
        if lines:
            for st in HAIR["strands"]:
                if st["front"]:
                    parts.append(stroke(sk, st["chain"], line_w(sw, sk), "traced-front"))
        for e in [*HAIR["front_edges"], *extra]:
            parts.append(stroke(sk, e, c._outline_w(sw)))
        return "".join(parts)

    return mass, front


VARIANTS = (("today", None), ("traced", traced(False)), ("traced + its lines", traced(True)))
if AS_IS:
    VARIANTS = (*VARIANTS, ("traced + its lines at its weight", traced(True, True)))


def cases():
    k = PRESETS["katherina"]
    if HEIGHT is not None:
        k = replace(k, height=HEIGHT)
        return [("katherina h1.3", k), ("katherina h1.3, no hat", replace(k, outfit=replace(k.outfit, hat_color=None)))]
    return [
        ("katherina", k),
        ("katherina, no hat", replace(k, outfit=replace(k.outfit, hat_color=None))),
        ("linnea", replace(PRESETS["linnea"], hair_length=k.hair_length)),
    ]


def render(p, scale):
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB"), sk


def crop(im, sk, k, pad):
    r, cx, cy = sk.head_r * k, sk.head_cx * k, sk.head_cy * k
    return im.crop((int(cx - pad[0] * r), int(cy - pad[1] * r), int(cx + pad[2] * r), int(cy + pad[3] * r)))


def grid(rows, path):
    tw = max(t.width for r in rows for t in r)
    th = max(t.height for r in rows for t in r)
    sheet = Image.new("RGB", (len(rows[0]) * (tw + 4), len(rows) * (th + 4)), (190, 190, 190))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            sheet.paste(t, (i * (tw + 4), j * (th + 4)))
    sheet.save(path)
    print(path, sheet.size)


REF = "ref-local/katherina_grok_real/katherina_grok_real.png"


def reference_tile(size, pad):
    """The reference cut to the same head-radius window as a head tile, at
    D0's face-width calibration (the one the trace is in), scaled to `size`.
    With `--hair-only`, the hair-only reference, placed by its registration
    (`harness/hair_only/register.py`) and unsqueezed, on white."""
    (ox, oy), s = HAIR["calibration"]["origin"], HAIR["calibration"]["px_per_r"]
    box = (ox - pad[0] * s, oy - pad[1] * s, ox + pad[2] * s, oy + pad[3] * s)
    if HAIR_ONLY:
        sc, (dx, dy) = HAIR["new_ref"]["scale"], HAIR["new_ref"]["offset"]
        ref = Image.open("ref-local/katherina_hair/hair_only.png").convert("RGBA")
        bg = Image.new("RGBA", ref.size, (255, 255, 255, 255))
        bg.alpha_composite(ref)
        box = tuple((v - o) / sc for v, o in zip(box, (dx, dy, dx, dy)))
        label, ref = "reference (katherina_hair, unsqueezed)", bg.convert("RGB")
    else:
        label, ref = "reference (katherina_grok_real)", Image.open(REF).convert("RGB")
    t = ref.crop(tuple(int(v) for v in box)).resize(size, Image.LANCZOS)
    ImageDraw.Draw(t).text((3, 3), label, fill=(255, 80, 80))
    return t


def main() -> None:
    heads, full, small = [], [], []
    try:
        for label, fns in VARIANTS:
            c._hair_mass, c._hair_front = fns or ORIG
            hrow, frow, srow = [], [], []
            for name, p in cases():
                im, sk = render(p, 3)
                t = crop(im, sk, 3, (2.4, 1.5, 2.4, 4.8) if AS_IS else (1.7, 1.5, 1.7, 2.4))
                ImageDraw.Draw(t).text((3, 3), f"{label} / {name}", fill=(200, 0, 0))
                hrow.append(t)
                im, _ = render(p, 1)
                ImageDraw.Draw(im).text((3, 3), f"{label} / {name}", fill=(200, 0, 0))
                frow.append(im)
            for name, p in cases()[:1]:
                sk = c.skeleton_for(p)
                tiles = []
                for density in (1, 2):
                    k = 21.0 * density / sk.head_r
                    im, _ = render(p, k * 4)
                    tiles.append(im.resize((im.width // 4, im.height // 4), Image.LANCZOS))
                both = Image.new("RGB", (tiles[0].width + tiles[1].width + 4, tiles[1].height), (255, 255, 255))
                both.paste(tiles[0], (0, 0))
                both.paste(tiles[1], (tiles[0].width + 4, 0))
                big = both.resize((both.width * 2, both.height * 2), Image.NEAREST)
                ImageDraw.Draw(big).text((3, 3), label, fill=(200, 0, 0))
                srow.append(big)
            if AS_IS:
                hrow.insert(0, reference_tile(hrow[0].size, (2.4, 1.5, 2.4, 4.8)))
            heads.append(hrow)
            full.append(frow)
            small.append(srow)
    finally:
        c._hair_mass, c._hair_front = ORIG
    grid(heads, f"{OUT}/preview{TAG}.png")
    grid(full, f"{OUT}/preview{TAG}_full.png")
    grid(small, f"{OUT}/preview{TAG}_small.png")


if __name__ == "__main__":
    main()
