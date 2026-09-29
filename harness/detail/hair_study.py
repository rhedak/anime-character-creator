"""D5 of `docs/detail-plan.md`: strand lines and a fringe parted into locks, on
`long_traced` first. A study for the owner to pick from; nothing in `src/`
changes (the candidates stand in for the cut's `hairline` and `strands`).

- **A** today: two sweeps off the parting, one line down each fall.
- **B** strands only: three lines of uneven length down each fall, a long one
  sweeping off the crown over the temple into the fall, and a lock divider
  running up from the fringe's edge toward the parting per lock; the hairline
  as today.
- **C** B with the fringe's edge parted into locks: three per side, the joins
  between them on today's hairline, each lock's tip hanging onto the forehead
  (0.12 head radii at the parting, a fifth of that at the temple, where the
  brows are close under the edge), leaning toward the temple the way the
  reference's sweep off the parting does. The dividers start at the joins.
- **D** C with four locks per side, longer (0.18).
- **E** C's locks with today's four lines and none of B's, added after the
  owner turned the strand lines down (2026-09-29): the flat mass reads as a
  choice, and lines drawn into it read as weird.

A first version cut the edge up into the hair between points on today's
line instead of hanging tips below it; across the slanted V of this cut's
hairline that read as bites out of the edge, not locks.

The fall strands are given in the trace's own frame and go through the same
stretch the mass does (`_long_scaled`), so they stay inside the fall at every
`hair_length`. Everything is clipped to the front hair, as the cut's strands
already are.

Written to `out/detail/`:

- `hair_study.png`: rows are the candidates; columns Katherina (her hat),
  Katherina with the hat off, Satoko (gold, pale tips), Kyoko (near black),
  Linnea (pink, a short fall), and a very different palette (silver hair on
  dark skin);
- `hair_study_zoom.png`: the heads close up at 3x, rows the candidates,
  columns Katherina with and without her hat, Satoko, Linnea and Chiyo (the
  shortest fall, under a hat);
- `hair_study_height.png`: whole figures, Katherina and Satoko at heights 0.8,
  1.0 and 1.3, A against C and D;
- `hair_study_small.png`: the smallest insert size (head radius 21 px) at 1x
  and 2x, shown 2x.
"""

import io
import math
import os
import sys
from dataclasses import replace

sys.path.insert(0, "harness/detail")

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"
ORIGINAL = c.HAIRSTYLES["long_traced"]


def qpt(p0, p1, p2, t):
    return (
        (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
        (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1],
    )


def sample(start, segs, n=60):
    pts = [start]
    prev = start
    for ctrl, end in segs:
        pts += [qpt(prev, ctrl, end, i / n) for i in range(1, n + 1)]
        prev = end
    return pts


def at_arc(pts, frac):
    """The point `frac` of the way along a polyline, and its unit tangent."""
    lens = [0.0]
    for a, b in zip(pts, pts[1:]):
        lens.append(lens[-1] + math.dist(a, b))
    want = frac * lens[-1]
    for i in range(1, len(pts)):
        if lens[i] >= want or i == len(pts) - 1:
            a, b = pts[i - 1], pts[i]
            u = (want - lens[i - 1]) / ((lens[i] - lens[i - 1]) or 1.0)
            tl = math.dist(a, b) or 1.0
            return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), ((b[0] - a[0]) / tl, (b[1] - a[1]) / tl)
    raise AssertionError


def fringe_sides(fall):
    """Today's hairline, split: the left fall's inside, the left fringe (temple
    to parting), the right fringe (temple to parting) and the right fall's
    inside. Indices off `_LONG_LINE`: 0-1 left fall, 2-3 left fringe, 4-5 right
    fringe, 6-9 right fall."""
    hs, hg = c._long_line(fall)
    left_fall = hg[:2]
    temple_l = hg[1][1]
    left = (temple_l, hg[2:4])
    part = hg[3][1]
    right_rev = c._reverse(part, hg[4:6])
    return hs, hg, left_fall, left, right_rev, part


def locks(side_chain, n, depth, lean=0.3, near_temple=0.2):
    """A fringe edge, temple to parting, as `n` locks hanging onto the forehead.

    The joins between locks stay on today's edge; each lock's tip hangs below
    it, `lean` of the way from its temple-side join and pointing down and out,
    `depth` head radii long at the parting and `near_temple` of that at the
    temple, where the brows are close under the edge. Returns the new segments
    and the joins (where the dividers start), temple first, the two ends
    excluded."""
    start, segs = side_chain
    pts = sample(start, segs)
    joins = [at_arc(pts, i / n)[0] for i in range(n + 1)]
    joins[0], joins[-1] = start, segs[-1][1]
    out_x = -1.0 if start[0] < segs[-1][1][0] else 1.0
    dl = math.hypot(0.40, 1.0)
    dx, dy = out_x * 0.40 / dl, 1.0 / dl
    out = []
    for i in range(n):
        a, b = joins[i], joins[i + 1]
        m, _ = at_arc(pts, (i + lean) / n)
        length = depth * (near_temple + (1 - near_temple) * (i + 0.5) / n)
        tip = (m[0] + dx * length, m[1] + dy * length)
        out.append((((a[0] + tip[0]) / 2, (a[1] + tip[1]) / 2), tip))
        bulge = 0.35 * length
        out.append((((tip[0] + b[0]) / 2 + dx * bulge, (tip[1] + b[1]) / 2 + dy * bulge), b))
    return out, joins[1:-1]


def divider(notch, part, side, reach=0.62):
    """A lock's divider, from its cut up toward the crown beside the parting,
    bowed outward."""
    top = (part[0] + side * 0.12, -1.02)
    end = (notch[0] + (top[0] - notch[0]) * reach, notch[1] + (top[1] - notch[1]) * reach)
    mid = ((notch[0] + end[0]) / 2 + side * 0.10, (notch[1] + end[1]) / 2 + 0.02)
    return notch, [(mid, end)]


# Left fall strands in the trace's frame (x left negative, y down, the base fall
# at `_LONG_BASE_TIP`); mirrored for the right. Uneven on purpose: evenly spaced
# parallels read as corduroy.
FALL_STRANDS = [
    ((-1.00, 0.12), [((-1.07, 0.80), (-1.01, 1.50))]),
    ((-1.15, 0.36), [((-1.22, 0.92), (-1.18, 1.36))]),
    ((-0.95, 0.86), [((-0.99, 1.20), (-0.92, 1.56))]),
]
CROWN_SWEEP = ((-0.46, -0.92), [((-0.98, -0.62), (-1.10, 0.10)), ((-1.17, 0.70), (-1.12, 1.28))])


def stretch(fall):
    span = c._LONG_BASE_TIP - c._HAIR_CHEEK_Y
    k = (fall - c._HAIR_CHEEK_Y) / span if span else 1.0

    def q(pt):
        return (pt[0], c._HAIR_CHEEK_Y + (pt[1] - c._HAIR_CHEEK_Y) * k) if pt[1] > c._HAIR_CHEEK_Y else pt

    return q


def mapped(chain, q, flip=False):
    s, segs = chain
    f = (lambda p: (-p[0], p[1])) if flip else (lambda p: p)
    return q(f(s)), [(q(f(a)), q(f(b))) for a, b in segs]


def candidate(n_locks=3, depth=0.0, extra_strands=True):
    def hairline(fall):
        hs, hg, left_fall, left, right_rev, part = fringe_sides(fall)
        if depth > 0:
            lsegs, _ = locks(left, n_locks, depth)
            rsegs, _ = locks(right_rev, n_locks, depth)
            _, rsegs = c._reverse(right_rev[0], rsegs)
            hg = [*left_fall, *lsegs, *rsegs, *hg[6:]]
        start, edge = c._long_scaled(fall)
        end = hg[-1][1]
        mass_start, mass_back = c._reverse(start, edge)
        back = [
            (((end[0] + mass_start[0]) / 2, (end[1] + mass_start[1]) / 2), mass_start),
            *mass_back,
            (((start[0] + hs[0]) / 2, (start[1] + hs[1]) / 2), hs),
        ]
        return hs, hg, back

    def strands(fall):
        q = stretch(fall)
        out = list(c._long_traced_strands(fall)[:2])
        for flip in (False, True):
            out.append(mapped(CROWN_SWEEP, q, flip))
            for s in FALL_STRANDS:
                out.append(mapped(s, q, flip))
        _, _, _, left, right_rev, part = fringe_sides(fall)
        for side, chain in ((-1, left), (1, right_rev)):
            _, joins = locks(chain, n_locks, depth)
            for jn in joins:
                out.append(divider(jn, part, side))
        return out

    return replace(ORIGINAL, hairline=hairline, strands=strands if extra_strands else ORIGINAL.strands)


VARIANTS = (
    ("A today", None),
    ("B strands", candidate(3, 0.0)),
    ("C B + 3 locks", candidate(3, 0.12)),
    ("D B + 4 longer locks", candidate(4, 0.18)),
    ("E 3 locks, today's lines", candidate(3, 0.12, extra_strands=False)),
)


def cases():
    k = PRESETS["katherina"]
    k_off = replace(k, outfit=replace(k.outfit, hat_color=None))
    odd = replace(PRESETS["satoko"], hair_color="#d8d8e4", skin_tone="#6b4a35", eye_color="#3a7bd5")
    return [
        ("katherina", k),
        ("katherina, no hat", k_off),
        ("satoko", PRESETS["satoko"]),
        ("kyoko", PRESETS["kyoko"]),
        ("linnea", PRESETS["linnea"]),
        ("silver on dark skin", odd),
    ]


def render(p, scale):
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB"), sk


def crop_head(im, sk, scale, pad=(1.55, 1.5, 1.55, 2.6)):
    r, cx, cy = sk.head_r * scale, sk.head_cx * scale, sk.head_cy * scale
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


def use(style):
    c.HAIRSTYLES["long_traced"] = style or ORIGINAL


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    rows, zoom, tall, small = [], [], [], []
    cs = dict(cases())
    close = [(n, cs[n]) for n in ("katherina", "katherina, no hat", "satoko", "linnea")]
    close.append(("chiyo", PRESETS["chiyo"]))
    try:
        for label, style in VARIANTS:
            use(style)
            row = []
            for name, p in cases():
                im, sk = render(p, 2)
                im = crop_head(im, sk, 2)
                ImageDraw.Draw(im).text((3, 3), f"{label} / {name}", fill=(200, 0, 0))
                row.append(im)
            rows.append(row)
            row = []
            for name, p in close:
                im, sk = render(p, 3)
                im = crop_head(im, sk, 3, (1.45, 1.2, 1.45, 1.4))
                ImageDraw.Draw(im).text((3, 3), f"{label} / {name}", fill=(200, 0, 0))
                row.append(im)
            zoom.append(row)
        for label, style in (VARIANTS[0], VARIANTS[2], VARIANTS[3]):
            use(style)
            row = []
            for name in ("katherina", "satoko"):
                for h in (0.8, 1.0, 1.3):
                    im, _ = render(replace(PRESETS[name], height=h), 1)
                    ImageDraw.Draw(im).text((3, 3), f"{label} / {name} h{h}", fill=(200, 0, 0))
                    row.append(im)
            tall.append(row)
            srow = []
            for name in ("katherina", "satoko", "kyoko"):
                p = PRESETS[name]
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
                ImageDraw.Draw(big).text((3, 3), f"{label} / {name}", fill=(200, 0, 0))
                srow.append(big)
            small.append(srow)
    finally:
        use(None)
    grid(rows, f"{OUT}/hair_study.png")
    grid(zoom, f"{OUT}/hair_study_zoom.png")
    grid(tall, f"{OUT}/hair_study_height.png")
    grid(small, f"{OUT}/hair_study_small.png")


if __name__ == "__main__":
    main()
