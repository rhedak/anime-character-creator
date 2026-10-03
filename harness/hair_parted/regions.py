"""D5 plan, step 3, part 1: the reference's hair split into the regions the
renderer draws (`docs/detail-status.md`, D5 plan).

The reference is `ref-local/katherina_grok_nohat/` (it passed
`harness/hair_audit/gate.py`); the hair is its `long-purple-hair` segment, an
exact cut (`harness/hair_audit/segments.py`), placed at the offset that found.
The calibration is `gate.py`'s: our head radii through `katherina_grok`'s.

The hair's pixels fall in three classes by luminance: line (under 18, the
black ink), dark (18 to 32, the darker tone behind) and light (32 up). Per side,
outward from the body: the front lock (light), the dark strip (behind), the
outer fall (light), with a single dividing line where the front lock and the
outer fall touch, above the strip. That line starts inside the hair beside the
temple (`T`), not on the silhouette, so the light hair is one surface above it.
A **seam** from `T` straight out to the silhouette separates it: above the seam
everything is front; below it the front lock is front and the outer fall is
behind the arm.

- `mass`: the whole silhouette, filled behind the face and body (each row from
  the innermost hair either side, then holes filled; the notches between the
  bottom tips open onto the page and stay out).
- `front`: the light component holding the crown, after the seam cut, closed
  over the line work inside it.
- `outer`: the light hair below the seams that is not front, holes filled (the
  reference's ear sits on it).

The front and outer regions are grown by half the measured line width (2 px,
the interior lines' median), so their edges land on the centre of the drawn
line, the line this code strokes; the mass by one pixel, for the reason given
where it is built. Writes
`out/hair_parted/regions.npz` and `regions.png` (the map over the reference).

    ./harness/run.sh harness/hair_parted/regions.py
"""

import json
import os
import sys

sys.path.insert(0, "harness/hair_audit")

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

import gate

REF = "ref-local/katherina_grok_nohat"
OUT = "out/hair_parted"
LINE, DARK = 18, 32


def load():
    comp = np.asarray(Image.open(f"{REF}/katherina_grok_nohat.png").convert("RGB")).astype(float)
    seg = np.asarray(Image.open(f"{REF}/segments/long-purple-hair.png").convert("RGBA"))
    at = json.load(open("out/hair_audit/segments_katherina_grok_nohat.json"))["long-purple-hair"]["at"]
    A = np.zeros(comp.shape[:2], bool)
    A[at[1] : at[1] + seg.shape[0], at[0] : at[0] + seg.shape[1]] = seg[..., 3] > 128
    lum = comp @ np.array([0.299, 0.587, 0.114])
    base = gate.measure(gate.BASE)
    m = gate.measure(f"{REF}/katherina_grok_nohat.png")
    s, _, (ox, oy) = gate.calibrate(m, base)
    return comp, A, lum, (ox, oy, s)


def line_width(A, lum):
    """The ink's width: twice the median distance-to-edge along the middle of
    the line pixels inside the hair (their skeleton, roughly)."""
    ink = A & (lum < LINE)
    d = ndi.distance_transform_edt(ink)
    ridge = ink & (d >= ndi.maximum_filter(d, size=3))
    return float(2 * np.median(d[ridge]))


def find_t(A, light, cal, side):
    """The top of the line dividing the curtain from the outer fall on one
    side: the highest row where, between 0.95 and 1.35 head radii out, a
    non-light run separates two light runs, followed up from the cheek."""
    ox, oy, s = cal
    xs = np.arange(int(ox + side * 0.95 * s), int(ox + side * 1.35 * s), side)
    best = None
    for yr in np.arange(0.6, -0.8, -0.005):
        y = int(round(oy + yr * s))
        row = light[y, xs] & A[y, xs]
        # A gap: light, then not light, then light again.
        idx = np.nonzero(row)[0]
        if idx.size < 2:
            break
        gaps = np.nonzero(np.diff(idx) > 1)[0]
        if gaps.size == 0:
            break
        g = gaps[0]
        x = (xs[idx[g]] + xs[idx[g + 1]]) / 2
        best = (float(x), y)
    return best


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    comp, A, lum, cal = load()
    ox, oy, s = cal
    lw = line_width(A, lum)
    light = A & (lum >= DARK)
    print(f"calibration ({ox:.1f}, {oy:.1f}) {s:.2f} px/r; line width {lw:.1f} px ({lw / s:.4f} r)")

    # Mass: each row from the innermost hair on the left to the innermost on
    # the right, where both sides have hair; then holes.
    H, W = A.shape
    fill = A.copy()
    c0 = int(round(ox))
    for y in range(H):
        left = np.nonzero(A[y, :c0])[0]
        right = np.nonzero(A[y, c0:])[0]
        if left.size and right.size:
            fill[y, left.max() : c0 + right.min() + 1] = True
    mass = ndi.binary_fill_holes(fill)
    # The segment's alpha takes in only about a pixel of the outline (from its
    # edge to the first light pixel is a median 1 px), so its edge already lies
    # within a pixel of the drawn line's centre, under the fit's tolerance. One
    # pixel out puts it on the centre of a 2 px line. On a black page the
    # outline's outer edge cannot be measured, the page being the same colour.
    mass = ndi.binary_dilation(mass, iterations=1)

    # The seams.
    ts = {}
    for side, name in ((-1, "left"), (1, "right")):
        t = find_t(A, light, cal, side)
        ts[name] = t
        print(f"T {name}: ({(t[0] - ox) / s:+.3f}, {(t[1] - oy) / s:+.3f}) r")
    cut = light.copy()
    for name, side in (("left", -1), ("right", 1)):
        tx, ty = ts[name]
        x0, x1 = sorted((int(tx), int(tx + side * 1.2 * s)))
        cut[ty - 1 : ty + 2, x0 : x1 + 1] = False

    lab, n = ndi.label(cut)
    crown = lab[int(oy - 1.2 * s), c0]
    assert crown, "the crown seed is not on light hair"
    front_light = lab == crown
    # Close over the line work inside the front (lock lines with free ends)
    # and grow onto the lines' centres.
    grow = int(round(lw / 2))
    front = ndi.binary_closing(front_light, iterations=int(round(lw)))
    front = ndi.binary_fill_holes(front)
    front = ndi.binary_dilation(front, iterations=grow) & mass

    # Outer falls: light hair below the seams, not front.
    rows = np.arange(H)[:, None]
    below = np.zeros_like(A)
    for name, side in (("left", -1), ("right", 1)):
        tx, ty = ts[name]
        half = (np.arange(W)[None, :] < c0) if side < 0 else (np.arange(W)[None, :] >= c0)
        below |= half & (rows > ty)
    outer_light = cut & ~front_light & below
    # Drop specks: anything under 200 px is a sliver between lines.
    lab2, n2 = ndi.label(outer_light)
    sizes = ndi.sum(outer_light, lab2, range(1, n2 + 1))
    outer = np.isin(lab2, 1 + np.nonzero(sizes >= 200)[0])
    outer = ndi.binary_closing(outer, iterations=int(round(lw)))
    outer = ndi.binary_fill_holes(outer)
    outer = ndi.binary_dilation(outer, iterations=grow) & mass & ~front

    np.savez_compressed(
        f"{OUT}/regions.npz",
        mass=mass,
        front=front,
        outer=outer,
        cal=np.array(cal),
        line_width=lw,
        t=np.array([ts["left"], ts["right"]]),
    )
    print(
        f"areas (px): mass {mass.sum()}, front {front.sum()}, outer {outer.sum()}, "
        f"behind (mass - front - outer) {(mass & ~front & ~outer).sum()}"
    )

    # The map, over the reference brightened.
    view = np.clip(comp * 2.2, 0, 255)
    tint = np.zeros_like(view)
    tint[mass] = (90, 90, 90)
    tint[mass & ~front & ~outer] = (40, 40, 160)
    tint[outer] = (0, 170, 0)
    tint[front] = (220, 120, 0)
    out = (0.45 * view + 0.55 * tint).astype(np.uint8)
    for name in ("left", "right"):
        tx, ty = ts[name]
        out[ty - 3 : ty + 4, int(tx) - 3 : int(tx) + 4] = (255, 0, 255)
    Image.fromarray(out).crop((330, 180, 1000, 1000)).save(f"{OUT}/regions.png")
    print(f"{OUT}/regions.png")


if __name__ == "__main__":
    main()
