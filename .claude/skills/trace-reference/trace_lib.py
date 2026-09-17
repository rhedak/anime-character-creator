"""Reusable pieces of the reference-tracing pipeline.

Generalized out of `harness/trace/trace.py`, `contour.py`, `fit.py`, and
`emit.py`, which hardcoded one reference (`ref/satoshi-real.jpg`) and one
calibration. This module takes the reference path and the calibration as
arguments instead, so it works for any new part (a hat, a prop, a new
hairstyle) without copy-pasting the pipeline again.

The method, in one paragraph: pick two unambiguous points on the reference
to fix a coordinate system in head-radius units (origin + scale), same units
`character.py` already draws in. Threshold the reference into ink/not-ink.
Walk a scan (radial from an anchor, or column-by-column, whichever suits the
shape) to measure how far the ink reaches at each step: that is the raw
silhouette, in the SAME units the shape code uses, so porting it is pasting
numbers, not a fitting problem. Simplify the raw scan to a handful of marks
(Douglas-Peucker), least-squares fit one quadratic control point per segment
between consecutive marks, and emit the result as `Point`/`Segment` literals
ready to paste into a `_part_name()` function.

Nothing here calls an image model or touches the network. It is pixel
thresholding and curve fitting, the same kind of code `contour.py` already
shipped; this module just stops assuming one reference file.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image


def load_ink(path: str, *, alpha_threshold: int = 16, rgb_threshold: int = 700) -> np.ndarray:
    """A boolean ink/not-ink array for `path`, whichever kind of image it is.

    An exported layer PNG with real transparency (mode RGBA, alpha channel
    actually varies) is thresholded on alpha, which is exact: nothing to do
    with color, just "did this pixel get painted at all". A flat JPG/PNG on a
    white or dark page has no alpha to read, so it falls back to the
    line-art brightness sum `contour.py` used (`< rgb_threshold` reads as
    ink), which only works when the page background is unambiguously the
    opposite brightness from the figure. Check `im.mode` and the alpha
    channel's own range before trusting the fallback on a new reference;
    print `alpha.min()`/`alpha.max()` if unsure.
    """
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im)
    alpha = a[:, :, 3]
    if alpha.min() < 250 or alpha.max() > 5:
        # Real transparency exists in this file; trust it.
        return alpha > alpha_threshold
    rgb = a[:, :, :3].astype(int)
    return rgb.sum(2) < rgb_threshold


def calibrate_two_points(
    px_a: tuple[float, float],
    r_a: float,
    px_b: tuple[float, float],
    r_b: float,
) -> tuple[float, float, float]:
    """Fix (origin_x, origin_y, pixels_per_head_radius) from two known points.

    `px_a`/`px_b` are pixel coordinates in the reference image of two
    features whose head-radius-unit position (`r_a`/`r_b`, vertical distance
    from the head center this generator already uses, e.g. eye at 0.16,
    chin at 1.05 per `harness/trace/trace.py`) is known from the generator's
    own skeleton constants. Only the vertical axis is calibrated this way
    (matching the existing harness); assumes the reference is not rotated,
    which is true for every front-facing reference this project has used so
    far. If the two features do not share an x coordinate (they usually do:
    eye-center-to-chin is a vertical run), average their x for the origin.
    """
    scale = (px_b[1] - px_a[1]) / (r_b - r_a)
    origin_y = px_a[1] - r_a * scale
    origin_x = (px_a[0] + px_b[0]) / 2
    return origin_x, origin_y, scale


def radial_profile(
    ink: np.ndarray,
    origin: tuple[float, float],
    scale: float,
    *,
    deg_lo: int = -170,
    deg_hi: int = 171,
    deg_step: int = 1,
    r_max: float = 3.0,
    r_step: float = 0.002,
) -> list[tuple[float, float]]:
    """Furthest ink along each bearing from `origin`, in head radii.

    0 degrees is straight up from the origin (matches the existing harness's
    convention, `y = origin_y - cos(theta) * r`), positive degrees sweep
    toward positive x. Use this for anything roughly centered on one point
    (hair, a hat's crown). For a shape that is not radially arranged around
    one sensible center (a brim's outward reach, a held prop's shaft), scan
    columns or rows instead; `column_profile` below is the other case this
    project has needed.
    """
    ox, oy = origin
    out = []
    for deg in range(deg_lo, deg_hi, deg_step):
        th = math.radians(deg)
        last = None
        r = 0.05
        while r < r_max:
            x = round(ox + math.sin(th) * scale * r)
            y = round(oy - math.cos(th) * scale * r)
            if 0 <= y < ink.shape[0] and 0 <= x < ink.shape[1] and ink[y, x]:
                last = r
            r += r_step
        if last is not None:
            out.append((float(deg), last))
    return out


def column_profile(
    ink: np.ndarray,
    origin: tuple[float, float],
    scale: float,
    *,
    x_lo: float,
    x_hi: float,
    x_step: float = 0.01,
    from_top: bool = True,
) -> list[tuple[float, float]]:
    """Where the ink starts or ends in each column, in head-radius units.

    `x_lo`/`x_hi` are in head radii, relative to `origin`. `from_top=True`
    returns the topmost ink row per column (a brim's upper edge, a crown's
    silhouette against the sky); `False` returns the bottommost (a hem, a
    shaft's tip). Use when the shape has a natural left-to-right reading,
    which a brim does and a hair mass centered on the skull does not.
    """
    ox, oy = origin
    out = []
    x = x_lo
    rows = range(ink.shape[0]) if from_top else range(ink.shape[0] - 1, -1, -1)
    while x <= x_hi:
        px = round(ox + x * scale)
        if 0 <= px < ink.shape[1]:
            for py in rows:
                if ink[py, px]:
                    out.append((x, (py - oy) / scale))
                    break
        x += x_step
    return out


def _polar(deg: float, r: float) -> tuple[float, float]:
    a = math.radians(deg)
    return (math.sin(a) * r, -math.cos(a) * r)


def simplify(points: list[tuple[float, float]], tol: float) -> list[int]:
    """Douglas-Peucker on an xy point list; returns kept INDICES.

    Keeps whatever sits furthest from the chord between the current
    endpoints, recursively, which is exactly what a tip or a notch is, unlike
    thinning by local prominence (tried first in `fit.py`'s own history,
    silently ate a whole sawtooth of real detail on Satoshi's crop; see that
    module's docstring). `tol` is in the same units as `points` (head radii,
    if that is what was passed in): start around 0.03-0.07 and look at the
    result, this project has never picked it analytically.
    """

    def rec(lo: int, hi: int) -> list[int]:
        if hi - lo < 2:
            return [lo]
        ax, ay = points[lo]
        bx, by = points[hi]
        dx, dy = bx - ax, by - ay
        n = math.hypot(dx, dy) or 1e-9
        worst, at = -1.0, lo
        for i in range(lo + 1, hi):
            px, py = points[i]
            dist = abs(dx * (ay - py) - (ax - px) * dy) / n
            if dist > worst:
                worst, at = dist, i
        if worst <= tol:
            return [lo]
        return rec(lo, at) + rec(at, hi)

    return [*rec(0, len(points) - 1), len(points) - 1]


def fit_chain(
    xy_points: list[tuple[float, float]], mark_indices: list[int]
) -> tuple[tuple[float, float], list[tuple[tuple[float, float], tuple[float, float]]]]:
    """One least-squares quadratic control point per segment between marks.

    Endpoints pinned to the marked points (exact, not fitted); the single
    free control point per segment is a linear least-squares problem, solved
    directly rather than by search. Placing the control at the segment's own
    midpoint (the obvious first guess) bulges every edge outside the true
    contour; see `fit.py`'s docstring for why that failed here before.
    Returns `(start, segments)` in this project's own `Point`/`Segment`
    shape, ready for `emit_chain` or for `character.py` directly.
    """
    marks = [xy_points[i] for i in mark_indices]
    start = marks[0]
    segs = []
    for j in range(len(marks) - 1):
        p0, p2 = marks[j], marks[j + 1]
        lo, hi = mark_indices[j], mark_indices[j + 1]
        between = xy_points[lo + 1 : hi]
        if not between:
            mid = ((p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2)
            segs.append((mid, p2))
            continue
        num = np.zeros(2)
        den = 0.0
        n = len(between) + 1
        for k, (px, py) in enumerate(between, start=1):
            t = k / n
            w = 2 * (1 - t) * t
            q = np.array((px, py))
            res = q - (1 - t) ** 2 * np.array(p0) - t**2 * np.array(p2)
            num += w * res
            den += w * w
        c = (num / den) if den > 1e-9 else (np.array(p0) + np.array(p2)) / 2
        segs.append(((float(c[0]), float(c[1])), p2))
    return start, segs


def boundary(mask: np.ndarray) -> list[tuple[int, int]]:
    """The ordered outer boundary of `mask`'s largest blob, as (x, y) pixels.

    Moore-neighbour tracing, clockwise on screen, starting from the blob's
    topmost-leftmost pixel. A radial or column scan can only describe a shape
    that is a single-valued function of angle or of x; a brim seen from below,
    a crown whose tip curls back over itself, or a crescent-shaped patch is
    not, and needs its contour walked instead. Isolate the object first (a
    connected-component label of the non-outline fill, grown back by half an
    outline width so the boundary lands on the stroke's centre line): tracing
    a threshold of a composite image walks whatever touches the object too.
    """
    m = np.pad(mask.astype(bool), 1)
    labels, n = _label(m)
    if n > 1:
        sizes = np.bincount(labels.ravel())
        sizes[0] = 0
        m = labels == int(np.argmax(sizes))
    ys, xs = np.nonzero(m)
    i = int(np.lexsort((xs, ys))[0])
    start = (int(xs[i]), int(ys[i]))
    # neighbours clockwise on screen (y down), starting west
    nbrs = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1)]
    out = [start]
    cur, back = start, 0  # we entered `start` scanning from the west
    for _ in range(4 * m.size):
        for k in range(8):
            d = (back + k) % 8
            nx, ny = cur[0] + nbrs[d][0], cur[1] + nbrs[d][1]
            if m[ny, nx]:
                # next search starts from the neighbour just before this one
                back = (d + 5) % 8
                cur = (nx, ny)
                break
        else:
            break  # isolated pixel
        if cur == start:
            break
        out.append(cur)
    return [(x - 1, y - 1) for x, y in out]


def _label(m: np.ndarray) -> tuple[np.ndarray, int]:
    from scipy import ndimage

    return ndimage.label(m)


def fit_closed(
    points: list[tuple[float, float]], tol: float
) -> tuple[tuple[float, float], list[tuple[tuple[float, float], tuple[float, float]]]]:
    """`simplify` + `fit_chain` for a closed contour (the output of `boundary`).

    Douglas-Peucker needs two distinct endpoints, and a closed loop's first
    and last point are the same one, so the loop is opened at its most
    distant pair: starting at the point farthest from the centroid (a tip,
    which should be a mark anyway) and splitting again at the point farthest
    from that. Each half is simplified on its own and the marks rejoined.
    """
    xy = np.asarray(points, dtype=float)
    c = xy.mean(0)
    s = int(np.argmax(((xy - c) ** 2).sum(1)))
    loop = [*points[s:], *points[:s], points[s]]
    far = int(np.argmax(((np.asarray(loop) - loop[0]) ** 2).sum(1)))
    first = simplify(loop[: far + 1], tol)
    second = [far + i for i in simplify(loop[far:], tol)]
    marks = sorted(set(first) | set(second))
    return fit_chain(loop, marks)


def sample_chain(
    start: tuple[float, float],
    segs: list[tuple[tuple[float, float], tuple[float, float]]],
    per_segment: int = 12,
) -> list[tuple[float, float]]:
    """Points along a fitted chain, for drawing it back over the reference."""
    out = [start]
    p0 = start
    for c, p2 in segs:
        for k in range(1, per_segment + 1):
            t = k / per_segment
            out.append(
                (
                    (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t**2 * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t**2 * p2[1],
                )
            )
        p0 = p2
    return out


def emit_chain(
    start: tuple[float, float],
    segs: list[tuple[tuple[float, float], tuple[float, float]]],
    *,
    start_name: str = "_START",
    edge_name: str = "_EDGE",
) -> str:
    """Render a fitted chain as Python source, ready to paste into character.py."""
    lines = [f"# {len(segs)} segments"]
    lines.append(f"{start_name}: Point = ({start[0]:.3f}, {start[1]:.3f})")
    lines.append(f"{edge_name}: list[Segment] = [")
    for (cx, cy), (ex, ey) in segs:
        lines.append(f"    (({cx:6.3f}, {cy:6.3f}), ({ex:6.3f}, {ey:6.3f})),")
    lines.append("]")
    return "\n".join(lines)
