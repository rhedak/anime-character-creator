"""D4d H1 of `docs/detail-plan.md`: trace the reference's two hands.

Per `.claude/skills/trace-reference/SKILL.md` step 3: the fills between the
outlines are labelled (`seg.py` mapped them), the hand's pieces picked by seed,
unioned, closed over the thin interior outlines and grown by half the outline
so the boundary lands on the stroke's centre line. A gap that is background
showing through (the relaxed hand's, between the thumb and the fingers) is
kept as a hole; the gaps a closing bridges are interior lines. The interior
lines are the dark pixels inside the hull eroded past the outline, each
ordered along its main axis and averaged into a centre line.

Units and frame: each hand's points are relative to its wrist's centre
(`calib.py`), in the image's own axes (x right, y down), in units of the
hand's length, so size B is a direct 0.65 head radii. The forearm's direction
is recorded with each hand: the grip's comes in from the side, the relaxed
hand's from above, and H3 decides how each is turned onto our figure.

Writes `out/trace_hands/hands.json` and `out/trace_hands/trace_<hand>.png`
(the fitted chains drawn back over the reference, brightened, at 6x).
"""

import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

REF = "ref-local/katherina_grok_real/katherina_grok_real.png"
OUT = "out/trace_hands"
HALF_STROKE = 1
TOL_PX = 0.8
SPECS = {
    "grip": {
        "box": (340, 700, 450, 800),
        "body_last": True,
    },
    "relaxed": {
        "box": (790, 850, 880, 975),
        "body_last": False,
    },
}
DISK = ndi.generate_binary_structure(2, 1)


def grow(m, n):
    return ndi.binary_dilation(m, structure=DISK, iterations=n) if n else m


def shrink(m, n):
    return ndi.binary_erosion(m, structure=DISK, iterations=n) if n else m


def pieces(a, spec):
    """Every skin fill in the hand's box, over 30 px with a mean red above 150
    (the staff's wood is about 69, the dress and the page darker), each its own
    piece. Seeds were tried first and two landed in one piece where a curled
    fingertip is a sliver. Ordered for drawing: the biggest piece is the hand's
    body; on the grip it goes last (the back of the hand and the thumb lie over
    the finger rolls), on the relaxed hand first (the curled fingertips over it)."""
    x0, y0, x1, y1 = spec["box"]
    fill = np.zeros(a.shape[:2], bool)
    fill[y0:y1, x0:x1] = a[y0:y1, x0:x1].sum(2) > 150
    lab, n = ndi.label(fill)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() > 30 and a[m][:, 0].mean() > 150:
            out.append(m)
    out.sort(key=lambda m: -m.sum())
    body, rest = out[0], sorted(out[1:], key=lambda m: np.nonzero(m)[0].mean())
    return [*rest, body] if spec["body_last"] else [body, *rest]


def piece_shape(m):
    """One piece: closed over its own thin interior lines, a gap that is
    background showing through kept as a hole, grown by half the outline."""
    closed = shrink(grow(m, 1), 1)
    filled = ndi.binary_fill_holes(closed)
    holes, n = ndi.label(filled & ~closed)
    big = np.zeros_like(filled)
    for i in range(1, n + 1):
        h = holes == i
        if h.sum() > 40:
            big |= h
    return grow(filled & ~big, HALF_STROKE), shrink(big, HALF_STROKE)


def to_units(pts, origin, length):
    ox, oy = origin
    return [((x - ox) / length, (y - oy) / length) for x, y in pts]


def fit_open(pts):
    marks = tl.simplify(pts, TOL_PX)
    return tl.fit_chain(pts, marks)


def interior_lines(a, body):
    # Skin sums to about 600, the outline to under 100; the staff showing
    # between the grip's finger rolls and the back of its hand is lighter wood,
    # about 250 to 330, and is a line here too.
    inside = shrink(body, 2)
    dark = inside & (a.sum(2) <= 330)
    lab, n = ndi.label(dark, structure=np.ones((3, 3)))
    lines = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(xs) < 6:
            continue
        p = np.stack([xs, ys], 1).astype(float)
        c = p.mean(0)
        _u, _s, vt = np.linalg.svd(p - c)
        t = (p - c) @ vt[0]
        order = np.argsort(t)
        bins = np.array_split(order, max(2, min(8, len(order) // 4)))
        centre = [tuple(p[b].mean(0)) for b in bins if len(b)]
        lines.append(centre)
    return lines


def chain_px(start, segs, origin, length):
    ox, oy = origin

    def back(q):
        return (ox + q[0] * length, oy + q[1] * length)

    return back(start), [(back(cp), back(end)) for cp, end in segs]


def main():
    a = np.asarray(Image.open(REF).convert("RGB")).astype(int)
    cal = json.load(open(f"{OUT}/calib.json"))
    out = {}
    for name, spec in SPECS.items():
        origin, length = cal[name]["wrist_centre"], cal[name]["length"]
        def u(ch):
            s0, segs = ch
            return (to_units([s0], origin, length)[0], [tuple(to_units([cp, e], origin, length)) for cp, e in segs])

        drawn = []
        parts = []
        for m in pieces(a, spec):
            body, hole = piece_shape(m)
            outline = tl.fit_closed(tl.boundary(body), TOL_PX)
            holes = [tl.fit_closed(tl.boundary(hole), TOL_PX)] if hole.any() else []
            lines = [fit_open(ln) for ln in interior_lines(a, body) if len(ln) >= 2]
            parts.append({"outline": u(outline), "holes": [u(h) for h in holes], "lines": [u(ln) for ln in lines]})
            drawn.append((outline, holes, lines))
        out[name] = {
            "pieces": parts,
            "forearm": [-v for v in cal[name]["into_hand"]],
            "wrist_width": cal[name]["wrist_width"] / length,
        }
        x0, y0, x1, y1 = spec["box"]
        k = 6
        view = np.clip(a[y0:y1, x0:x1] * 1.6, 0, 255).astype(np.uint8)
        im = Image.fromarray(view).resize(((x1 - x0) * k, (y1 - y0) * k), Image.NEAREST)
        d = ImageDraw.Draw(im)

        def draw(ch, colour, closed):
            pts = tl.sample_chain(*ch)
            pts = [((x - x0) * k, (y - y0) * k) for x, y in pts]
            if closed:
                pts.append(pts[0])
            d.line(pts, fill=colour, width=2)

        for outline, holes, lines in drawn:
            draw(outline, (255, 40, 40), True)
            for h in holes:
                draw(h, (40, 200, 255), True)
            for ln in lines:
                draw(ln, (40, 255, 80), False)
        im.save(f"{OUT}/trace_{name}.png")
        print(name, [(len(o[1]), len(h), len(ln)) for o, h, ln in drawn])
    with open(f"{OUT}/hands.json", "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
