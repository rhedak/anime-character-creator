"""Trace `ref-local/katherina_hair/` into the two pieces our renderer draws
(the owner, 2026-09-29): the hair behind the body and the hair in front of it.

- **The full hair** is `hair_only.png`'s alpha; drawn as the mass, behind the
  body, which covers the part of it a body would.
- **The front piece** is `hair_with_human_shape.png`'s alpha: the same hair
  with a human silhouette cut out, so what is left hangs in front of the body;
  drawn over the body with its whole outline stroked.
- **The back hair** is the difference; it needs no shape of its own, the mass
  carries it.

Nothing is hidden in this reference, so nothing is filled in. Both pieces keep
their holes and islands. The outline is the alpha's edge moved in by half the
reference's measured outline width, so our stroke lands on its centre line.

**Line work** is `harness/trace_hair/lines.py`'s method on `hair_only.png`:
the black-hat (after clamping the luminance at the fill's 70th percentile, so
the sheen's bright zigzags do not make lines along their edges), hysteresis,
thinning, walking, merging through junctions and gaps, fitting. Lines along
the front piece's edge are its outline and are dropped; the rest go on the
piece they lie on.

**Frame**: `register.py`'s scale and offset put the reference in
`katherina_grok_real`'s pixels, which D0's face-width calibration ties to our
head; then the as-is belt squeeze (below the cheek line, y only) that puts
that reference's belt on Katherina's at height 1.3.

Writes `out/hair_only/hair.json` (the preview's schema) and `overlay.png`
(the traced chains over the reference).
"""

import json
import sys

sys.path.insert(0, "harness/trace_hair")
sys.path.insert(0, "harness/detail")
sys.path.insert(0, ".claude/skills/trace-reference")

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

import lines as L
import trace_lib as tl
from trace_hair import CHEEK, katherina_belt

DIR = "ref-local/katherina_hair"
OUT = "out/hair_only"
ORIGIN, S = (636, 290), 88.7
REF_BELT = 4.398
HEIGHT = 1.3
R = 6
HI, LO = 22.0, 9.0
CLAMP = 70
MIN_LEN = 18
TOL_SHAPE, TOL_LINE = 0.008, 0.006


def alpha(name):
    return np.asarray(Image.open(f"{DIR}/{name}.png").convert("RGBA"))[..., 3] > 128


def outline_width(img, m):
    """The reference's outline: the dark band just inside the alpha's edge,
    its thickness twice the median distance transform on its middle."""
    lum = img[..., :3] @ np.array([0.299, 0.587, 0.114])
    band = m & ~ndi.binary_erosion(m, iterations=8) & (lum < 12)
    d = ndi.distance_transform_edt(band)
    return float(2 * np.median(d[d > 0]))


def main() -> None:
    reg = json.load(open(f"{OUT}/register.json"))
    sc, (dx, dy) = reg["scale"], reg["offset"]
    img = np.asarray(Image.open(f"{DIR}/hair_only.png").convert("RGBA")).astype(float)
    full = alpha("hair_only")
    front = alpha("hair_with_human_shape")
    print(f"front inside full: {(front & full).sum() / front.sum():.1%}")
    full |= front
    ow = outline_width(img, full)
    half = max(1, int(round(ow / 2)))
    print(f"outline about {ow:.1f} px; masks moved in by {half}")
    full_c = ndi.binary_erosion(full, iterations=half)
    front_c = ndi.binary_erosion(front, iterations=half)

    k = (katherina_belt(HEIGHT) - CHEEK) / (REF_BELT - CHEEK)
    print(f"belt squeeze below the cheek: {k:.3f}")

    def to_head(pts):
        out = []
        for x, y in pts:
            hx = (x * sc + dx - ORIGIN[0]) / S
            hy = (y * sc + dy - ORIGIN[1]) / S
            out.append((hx, CHEEK + (hy - CHEEK) * k if hy > CHEEK else hy))
        return out

    def parts(mm, min_px=200):
        res = []
        lab, n = ndi.label(mm)
        for i in range(1, n + 1):
            piece = lab == i
            if piece.sum() < min_px:
                continue
            outer = tl.fit_closed(to_head(tl.boundary(piece)), TOL_SHAPE)
            holes = []
            hl, nh = ndi.label(ndi.binary_fill_holes(piece) & ~piece)
            for j in range(1, nh + 1):
                if (hl == j).sum() >= min_px:
                    holes.append(tl.fit_closed(to_head(tl.boundary(hl == j)), TOL_SHAPE))
            res.append([outer, holes])
        return res

    mass_parts, front_parts = parts(full_c), parts(front_c)
    print(f"mass {len(mass_parts)} pieces {sum(len(h) for _, h in mass_parts)} holes; front {len(front_parts)} pieces {sum(len(h) for _, h in front_parts)} holes")

    # Line work.
    lum = img[..., :3] @ np.array([0.299, 0.587, 0.114])
    cap = np.percentile(lum[full], CLAMP)
    lc = np.where(full, np.minimum(lum, cap), cap)
    disk = np.hypot(*np.mgrid[-R : R + 1, -R : R + 1]) <= R
    bh = ndi.grey_closing(lc, footprint=disk) - lc
    inner = ndi.binary_erosion(full, iterations=half + 2)
    lo = inner & (bh > LO)
    lab, n = ndi.label(lo, structure=np.ones((3, 3)))
    strong = np.unique(lab[inner & (bh > HI)])
    ln = np.isin(lab, strong[strong > 0])
    ln = ndi.binary_closing(ln, np.ones((3, 3))) & inner
    widths = 2 * ndi.distance_transform_edt(ln)
    sk = L.thin(ln)
    L.GAP, L.TURN = 12.0, 35.0
    front_edge = front & ~ndi.binary_erosion(front, iterations=int(ow) + 3)
    front_edge |= ndi.binary_dilation(front, iterations=int(ow) + 3) & ~front
    strands = []
    for p in L.paths(sk):
        if len(p) < MIN_LEN:
            continue
        on_edge = np.mean([front_edge[int(y), int(x)] for x, y in p])
        if on_edge > 0.6:
            continue
        in_front = np.mean([front[int(y), int(x)] for x, y in p]) > 0.5
        u = to_head(p)
        strands.append({"chain": tl.fit_chain(u, tl.simplify(u, TOL_LINE)), "front": bool(in_front), "px": len(p)})
    print(f"lines: {len(strands)} ({sum(s['front'] for s in strands)} front), widths median {np.median(widths[sk]):.1f} px ({np.median(widths[sk]) * sc / S:.4f} head radii)")

    largest = max(front_parts, key=lambda pr: len(pr[0][1]))[0]
    json.dump(
        {
            "mass_parts": mass_parts,
            "front_parts": front_parts,
            "mass": max(mass_parts, key=lambda pr: len(pr[0][1]))[0],
            "front": largest,
            "front_edges": [largest],
            "strands": strands,
            "lines": [],
            "squeeze": k,
            "cheek": CHEEK,
            "calibration": {"origin": list(ORIGIN), "px_per_r": S},
            "new_ref": {"scale": sc, "offset": [dx, dy]},
            "line_width_r": float(np.median(widths[sk]) * sc / S),
            "outline_width_r": ow * sc / S,
        },
        open(f"{OUT}/hair.json", "w"),
        indent=1,
    )

    # Overlay in the reference's own pixels (undo the squeeze and the frame).
    def back(q):
        hx, hy = q
        hy = CHEEK + (hy - CHEEK) / k if hy > CHEEK else hy
        return ((hx * S + ORIGIN[0] - dx) / sc, (hy * S + ORIGIN[1] - dy) / sc)

    base = np.where(full[..., None], np.clip(img[..., :3] * 2.2, 0, 255), 255).astype(np.uint8)
    im = Image.fromarray(base)
    d = ImageDraw.Draw(im)
    for key, col in (("mass_parts", (0, 200, 0)), ("front_parts", (255, 60, 60))):
        for outer, holes in json.load(open(f"{OUT}/hair.json"))[key]:
            for ch in [outer, *holes]:
                d.line([back(q) for q in tl.sample_chain(*ch)], fill=col, width=3)
    for st in strands:
        d.line([back(q) for q in tl.sample_chain(*st["chain"])], fill=(0, 140, 255) if st["front"] else (255, 170, 0), width=3)
    im.save(f"{OUT}/overlay.png")
    print(f"{OUT}/overlay.png")


if __name__ == "__main__":
    main()
