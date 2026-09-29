"""The front lock as the owner traced it (2026-09-29), replacing `locks.py`.

`locks.py` funnelled the traced curtain (its whole width, neck to the hair's
outer edge) into a lock below the shoulder. The owner's reading of
`katherina_grok_real`, on a screenshot (`owner_trace.py` registers it): the
front lock is **one narrow strip** from near the top of the head straight down
to the chest, ending in its own tip; the hair outside it is the back hair, a
separate unit; and between the lock and the neck lies a **darker patch** of
back hair (the cyan), also not part of the lock.

So here:

- The **front piece** is the traced front hair (the crown and the fringe, from
  `hair_with_human_shape.png`) cut to inside the lock's outer edge from the top
  down, and below the cheek line only the two strips, each between the owner's
  red lines, tip included. Nothing wider than the lock hangs in front; the hair
  outside it is the mass behind, so its edge is the lock's own edge.
- The **dark patch** is a second, darker tone of the hair (`dark_factor`, the
  reference's underside measures about 0.63 of the fill's value) drawn on the
  mass, between the lock's inner edge and the centre line, from the cheek line
  down to below our shoulder. It sits behind the head, neck and jacket, which
  cover what they cover; only the wedge beside the jaw shows.
- The **lines**: the traced ones stay while they lie on the front piece and
  are cut a little below the cheek line; each strip gets one line of its own
  along it.

The vertices are the owner's marks read off `out/hair_only/owner_trace.json`'s
screenshot pixels (`SHOT` below), the check being that every red pixel lies
within a few pixels of them (printed). They are put in head radii through the
registration, D0's face-width calibration and the belt squeeze, like the rest.

Reads `hair.json` and `owner_trace.json`; writes `hair_lock2.json` (the same
schema plus `dark_parts` and `dark_factor`) and `lock2.png`.
"""

import dataclasses
import json
import sys

sys.path.insert(0, "harness/hair_only")
sys.path.insert(0, "harness/trace_hair")

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

import trace as T
import trace_lib as tl
from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/hair_only"
ORIGIN, S = T.ORIGIN, T.S
DARK_FACTOR = 0.65
# How far below the cheek line the traced lines run before the strip's own
# line takes over, and how far below our shoulder the dark patch runs (under
# the jacket).
LINE_CUT = 0.3
DARK_BELOW_SHOULDER = 0.3
# Where the dark patch starts above the cheek line: behind the face, which
# covers its flat top, so only the wedge beside the jaw shows.
DARK_ABOVE_SPLIT = 0.6
# The traced curtain's face-side edge is drawn onto the lock's inner line this
# far above the cheek line, so the two meet without a step.
BLEND = 0.35
# The owner's lock ends on a slanted edge; the tip is drawn pointed, this far
# below where the owner's outer edge ends.
TIP_EXTEND = 0.3
SIDES = (-1, 1)


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


# The owner's marks, in the screenshot's pixels (owner_trace.json's frame),
# top to bottom. A strip is its outer edge then its inner edge reversed; the
# outer edge ends in the lock's tip.
SHOT = {
    -1: dict(
        outer=[(467, 60), (430, 190), (425, 202), (397, 975), (399, 990), (440, 1097), (510, 1135)],
        inner=[(546, 77), (500, 208), (496, 215), (486, 990), (489, 995), (530, 1078)],
    ),
    1: dict(
        outer=[(995, 160), (1017, 560), (990, 905), (985, 917), (1003, 1072), (987, 1140)],
        inner=[(927, 163), (940, 440), (888, 988), (918, 1078)],
    ),
}
# Where the dark patch starts: the top of the cyan marks.
CYAN_TOP = 428


def main() -> None:
    reg = json.load(open(f"{OUT}/register.json"))
    sc, (dx, dy) = reg["scale"], tuple(reg["offset"])
    own = json.load(open(f"{OUT}/owner_trace.json"))
    ss, (sx, sy) = own["scale"], own["offset"]
    hair = json.load(open(f"{OUT}/hair.json"))
    k = hair["squeeze"]
    px_r = S / sc
    ox = (ORIGIN[0] - dx) / sc

    def y_to_h(y):
        hy = (y * sc + dy - ORIGIN[1]) / S
        return T.CHEEK + (hy - T.CHEEK) * k if hy > T.CHEEK else hy

    def h_to_y(hy):
        hu = T.CHEEK + (hy - T.CHEEK) / k if hy > T.CHEEK else hy
        return (ORIGIN[1] + hu * S - dy) / sc

    def shot_to_head(u, v):
        X, Y = u / ss + sx, v / ss + sy
        hy = (Y - ORIGIN[1]) / S
        return (X - ORIGIN[0]) / S, T.CHEEK + (hy - T.CHEEK) * k if hy > T.CHEEK else hy

    def head_to_raster(hx, hy):
        return (hx * S + ORIGIN[0] - dx) / sc, h_to_y(hy)

    # The marks in head radii, and how well they cover the red pixels.
    lines = {s: {n: [shot_to_head(*p) for p in pts] for n, pts in SHOT[s].items()} for s in SIDES}
    # The thin part of each lock's outer edge (the reference draws it fine):
    # down to where the lock's tip begins.
    thin = {s: lines[s]["outer"][: len(lines[s]["outer"]) - (2 if s < 0 else 1)] for s in SIDES}
    for s in SIDES:
        x, y = lines[s]["outer"][-1]
        lines[s]["outer"][-1] = (x, y + TIP_EXTEND)
    red = np.array(own["red"])
    segs = [np.array(pts, float) for s in SIDES for pts in SHOT[s].values()]
    tip_u = {s: SHOT[s]["outer"][-1] for s in SIDES}
    reds_shot = np.column_stack([(red[:, 0] - sx) * ss, (red[:, 1] - sy) * ss])

    def dist_to(poly, pts):
        d = np.full(len(pts), np.inf)
        for a, b in zip(poly[:-1], poly[1:]):
            ab = b - a
            t = np.clip(((pts - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
            d = np.minimum(d, np.hypot(*(pts - (a + t[:, None] * ab)).T))
        return d

    d_all = np.min([dist_to(p, reds_shot) for p in segs], axis=0)
    print(f"red pixels within 3 px of the vertices: {(d_all <= 3).mean():.1%}, max {d_all.max():.1f} px (screenshot)")

    def curve(side, name, hy):
        """Distance from the centre line at height `hy`, along a mark; past its
        ends it continues on the end segment's line."""
        pts = np.array(lines[side][name])
        ys, xs = pts[:, 1], np.abs(pts[:, 0])
        if hy <= ys[0]:
            slope = (xs[1] - xs[0]) / (ys[1] - ys[0])
            return float(xs[0] + slope * (hy - ys[0]))
        return float(np.interp(hy, ys, xs))

    img = np.asarray(Image.open(f"{T.DIR}/hair_only.png").convert("RGBA")).astype(float)
    front = T.alpha("hair_with_human_shape")
    full = T.alpha("hair_only") | front
    ow = T.outline_width(img, full)
    front_c = ndi.binary_erosion(front, iterations=max(1, int(round(ow / 2))))

    sk = c.skeleton_for(dataclasses.replace(PRESETS["katherina"], height=T.HEIGHT))
    y_sh = (sk.shoulder_y - sk.head_cy) / sk.head_r
    y_split = shot_to_head(0, CYAN_TOP)[1]
    row_split = int(round(h_to_y(y_split)))
    print(f"cheek split {y_split:.3f} r (row {row_split}); shoulder {y_sh:.3f}")

    # The front piece: the traced hair inside the lock's outer edge down to the
    # cheek line, then only the strips.
    new = np.zeros_like(front_c)
    xs_all = np.arange(front_c.shape[1])
    y_blend = y_split - BLEND
    row_b = int(round(h_to_y(y_blend)))
    # The curtain's face-side edge where the easing starts, per side: its
    # nearest hair beyond the temple locks (over 0.7 r from the centre line).
    edge0 = {}
    for side in SIDES:
        d = np.abs(np.nonzero(front_c[row_b])[0] - ox)
        d = d[(d > 0.7 * px_r) & ((np.nonzero(front_c[row_b])[0] < ox) == (side < 0))]
        edge0[side] = float(d.min()) if len(d) else curve(side, "inner", y_blend) * px_r
    print(f"curtain's face-side edge at {y_blend:.2f} r: {edge0[-1] / px_r:.3f} and {edge0[1] / px_r:.3f} r; the lock's {curve(-1, 'inner', y_blend):.3f} and {curve(1, 'inner', y_blend):.3f}")
    for y in range(0, row_split + 1):
        hy = y_to_h(y)
        left_out, right_out = (ox - curve(s, "outer", hy) * px_r if s < 0 else ox + curve(s, "outer", hy) * px_r for s in SIDES)
        keep = (xs_all >= left_out) & (xs_all <= right_out)
        if hy >= y_blend:
            # The curtain's own face-side edge, eased onto the lock's inner line.
            e = smooth((hy - y_blend) / BLEND)
            bound = {s: edge0[s] + (curve(s, "inner", hy) * px_r - edge0[s]) * e for s in SIDES}
            keep &= (xs_all <= ox - bound[-1]) | (xs_all >= ox + bound[1])
        new[y] = front_c[y] & keep
    im_strips = Image.new("1", front_c.shape[::-1], 0)
    for side in SIDES:
        poly = lines[side]["outer"] + lines[side]["inner"][::-1]
        ImageDraw.Draw(im_strips).polygon([head_to_raster(*p) for p in poly], fill=1)
    strips = np.asarray(im_strips)
    new |= strips
    lab, _ = ndi.label(new)
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    new = lab == int(np.argmax(sizes))

    def to_head(pts):
        return [((x * sc + dx - ORIGIN[0]) / S, y_to_h(y)) for x, y in pts]

    def parts(mm, min_px=200):
        res = []
        lab_p, n_p = ndi.label(mm)
        for i in range(1, n_p + 1):
            piece = lab_p == i
            if piece.sum() < min_px:
                continue
            outer = tl.fit_closed(to_head(tl.boundary(piece)), T.TOL_SHAPE)
            holes = []
            hl, nh = ndi.label(ndi.binary_fill_holes(piece) & ~piece)
            for j in range(1, nh + 1):
                if (hl == j).sum() >= min_px:
                    holes.append(tl.fit_closed(to_head(tl.boundary(hl == j)), T.TOL_SHAPE))
            res.append([outer, holes])
        return res

    front_parts = parts(new)
    largest = max(front_parts, key=lambda pr: len(pr[0][1]))[0]
    print(f"front: {len(front_parts)} pieces, {sum(len(h) for _, h in front_parts)} holes")

    def in_new(pt):
        x, y = head_to_raster(*pt)
        x, y = int(round(x)), int(round(y))
        return 0 <= y < new.shape[0] and 0 <= x < new.shape[1] and bool(new[y, x])

    # The traced lines.
    y_cut = y_split + LINE_CUT
    strands, n_front = [], 0
    for st in hair["strands"]:
        pts = tl.sample_chain(*st["chain"])
        kept = [p for p in pts if p[1] <= y_cut]
        if in_new(pts[len(pts) // 2]) and len(kept) >= 8:
            strands.append({**st, "front": True, "chain": tl.fit_chain(kept, tl.simplify(kept, T.TOL_LINE))})
            n_front += 1
        else:
            strands.append({**st, "front": False})
    print(f"traced lines: {n_front} on the front piece, {len(strands) - n_front} on the mass")

    # Each strip's own line, along it from below the cut to short of the tip.
    for side in SIDES:
        y_end = min(lines[side]["outer"][-1][1], lines[side]["inner"][-1][1]) - 0.15
        pts = []
        for hy in np.linspace(y_cut - 0.1, y_end, 20):
            a, b = curve(side, "inner", float(hy)), curve(side, "outer", float(hy))
            pts.append((side * (a + 0.45 * (b - a)), float(hy)))
        strands.append({"chain": tl.fit_chain(pts, tl.simplify(pts, T.TOL_LINE)), "front": True, "px": 0})

    # The dark patch: from the lock's inner edge to the centre line.
    def straight(pts):
        segs = [(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b) for a, b in zip(pts, [*pts[1:], pts[0]])]
        return pts[0], segs

    dark = []
    y_bot = y_sh + DARK_BELOW_SHOULDER
    for side in SIDES:
        ys = np.linspace(y_split - DARK_ABOVE_SPLIT, y_bot, 18)
        edge = [(side * curve(side, "inner", float(y)), float(y)) for y in ys]
        dark.append(straight([*edge, (0.0, float(ys[-1])), (0.0, float(ys[0]))]))

    out = {**hair, "front_parts": front_parts, "front": largest, "front_edges": [largest], "strands": strands}
    out["dark_parts"], out["dark_factor"] = dark, DARK_FACTOR
    out["owner_lock"] = {str(s): lines[s] for s in SIDES}
    # The thin edge runs on up past the top mark, on that segment's line.
    out["thin_edges"] = [[(s * curve(s, "outer", -1.5), -1.5), *thin[s]] for s in SIDES]
    json.dump(out, open(f"{OUT}/hair_lock2.json", "w"), indent=1)

    view = np.where(front[..., None], np.clip(img[..., :3] * 2.2, 0, 255), 255)
    view[front_c & ~new] = (220, 60, 60)
    view[new] = (60, 180, 70)
    im = Image.fromarray(view.astype(np.uint8))
    d = ImageDraw.Draw(im)
    for ch in dark:
        d.polygon([head_to_raster(*q) for q in tl.sample_chain(*ch)], outline=(0, 90, 220))
    d.line([(0, row_split), (im.width, row_split)], fill=(255, 220, 0), width=3)
    im.crop((200, 150, 1120, 1450)).resize((690, 975)).save(f"{OUT}/lock2.png")
    print(f"{OUT}/hair_lock2.json, {OUT}/lock2.png")


if __name__ == "__main__":
    main()
