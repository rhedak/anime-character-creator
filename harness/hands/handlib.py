"""Shared helpers for the hands campaign (`docs/hands-plan.md`).

Rendering with a hand candidate applied, cropping to a hand, isolating one
hand's own SVG and measuring it against the footprint gate.

A candidate is a labelled way to draw the hands: a transform of the
`CharacterParams` plus, when the candidate is a code variant that does not
exist in `src/` yet, a context manager that patches the module while it
renders. New candidates (S, K1..K3, T) register themselves in `candidates.py`.
"""

import io
import re
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace

sys.path.insert(0, "src")

import cairosvg
import numpy as np
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

# The five presets the standard sheet shows, covering the range: a plain drawn
# sleeve, a coat, an apron and skirt, a lab coat, and the one wide traced
# sleeve with a staff.
SHEET_PRESETS = ("krista", "gero", "satoko", "keiko", "katherina")

# The footprint gate (`docs/hands-plan.md`): proposed from the mitten's measured
# footprint, the owner's to change. (low, high) in head radii or ratio.
GATE = {
    "height": (0.30, 0.42),
    "aspect": (0.70, 1.20),
    "ink_share": (0.0, 0.35),
    "narrowest_run": (1.5, float("inf")),
}

# The join with the arm, as a share of the mitten's on the same preset and side
# (the mitten closes the arm's end at its own width). Added after V0, when the
# owner said the traced hands do not connect to the arms well.
JOIN_VS_MITTEN = (0.90, 1.10)

DARK_SKIN = "#6b4a35"


@dataclass(frozen=True)
class Candidate:
    label: str
    desc: str
    apply: Callable[[c.CharacterParams], c.CharacterParams] = lambda p: p
    patch: Callable[[], object] | None = None

    def render_ctx(self):
        return self.patch() if self.patch else _null()


@contextmanager
def _null() -> Iterator[None]:
    yield


def render(p: c.CharacterParams, scale: float, cand: Candidate | None = None):
    """The figure as a PIL image at `scale` px per canvas unit, with `cand` applied."""
    q = cand.apply(p) if cand else p
    with cand.render_ctx() if cand else _null():
        sk = c.skeleton_for(q)
        svg = c.render_character(q, sk, background="#ffffff")
        im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB")
        centres = {s: c._hand_centre(sk, q, s) for s in (-1, 1)}
    return im, sk, centres


def crop_hand(im: Image.Image, sk, centre, scale: float, half_hr: float = 0.85, size: int = 200) -> Image.Image:
    """A square crop `half_hr` head radii either side of a hand's centre."""
    hx, hy = centre
    cx = (sk.head_cx + hx * sk.head_r) * scale
    cy = (sk.head_cy + hy * sk.head_r) * scale
    h = half_hr * sk.head_r * scale
    return im.crop((int(cx - h), int(cy - h), int(cx + h), int(cy + h))).resize((size, size), Image.LANCZOS)


def label(im: Image.Image, text: str, colour=(200, 0, 0)) -> Image.Image:
    ImageDraw.Draw(im).text((4, 3), text, fill=colour)
    return im


@contextmanager
def capture_hands() -> Iterator[list]:
    """Collect every `_hand` call's `(side, svg)` while rendering."""
    got: list = []
    orig = c._hand

    def wrap(sk, p, cx, wrist_y, w_wrist, side):
        out = orig(sk, p, cx, wrist_y, w_wrist, side)
        got.append((side, out))
        return out

    c._hand = wrap
    try:
        yield got
    finally:
        c._hand = orig


def hand_arrays(p: c.CharacterParams, cand: Candidate, scale: int = 8):
    """For each hand, its SVG rasterised alone on white: `{side: ndarray}`, plus the
    skeleton and the outline's drawn width in px at `scale`."""
    q = cand.apply(p)
    with cand.render_ctx(), capture_hands() as got:
        sk = c.skeleton_for(q)
        svg = c.render_character(q, sk, background="#ffffff")
    head = re.search(r"<svg[^>]*>", svg).group(0)
    out = {}
    for side, hand_svg in got:
        doc = head + '<rect width="100%" height="100%" fill="#ffffff"/>' + hand_svg + "</svg>"
        png = cairosvg.svg2png(bytestring=doc.encode(), scale=scale)
        out[side] = np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(int)
    outline_px = c._outline_w(c._stroke_w(sk), 0.85) * scale
    return out, sk, q, outline_px


def _skin_mask(arr, skin: str):
    rgb = np.array([int(skin[i : i + 2], 16) for i in (1, 3, 5)])
    return np.abs(arr - rgb).sum(axis=2) < 12


def _narrowest_run(skin_m, top: float = 0.30, bottom: float = 0.85) -> float:
    """The narrowest skin run, in px, over the rows between `top` and `bottom` of the hand's
    height (the tips taper to nothing by construction, so they are left out)."""
    ys = np.where(skin_m.any(axis=1))[0]
    if len(ys) == 0:
        return 0.0
    y0, y1 = ys.min(), ys.max()
    lo, hi = int(y0 + top * (y1 - y0)), int(y0 + bottom * (y1 - y0))
    best = float("inf")
    for y in range(lo, hi + 1):
        row = skin_m[y]
        edges = np.diff(np.concatenate(([0], row.view(np.int8), [0])))
        starts, ends = np.where(edges == 1)[0], np.where(edges == -1)[0]
        for a, b in zip(starts, ends, strict=True):
            best = min(best, b - a)
    return 0.0 if best == float("inf") else float(best)


def footprint(arr, skin: str, head_r: float, outline_px: float, scale: int = 8) -> dict:
    """The gate's measures for one isolated hand."""
    nonwhite = (arr < 245).any(axis=2)
    ys, xs = np.where(nonwhite)
    if len(xs) == 0:
        return {}
    w = (xs.max() - xs.min() + 1) / scale / head_r
    h = (ys.max() - ys.min() + 1) / scale / head_r
    ink = arr.sum(axis=2) < 120
    skin_m = _skin_mask(arr, skin)
    # Where the hand meets the arm: the mean width of its topmost rows (5% to 15% of its height).
    y0 = ys.min()
    lo, hi = int(y0 + 0.05 * (ys.max() - y0)), int(y0 + 0.15 * (ys.max() - y0))
    join = nonwhite[lo : hi + 1].sum(axis=1).mean() / scale / head_r
    return {
        "join": join,
        "width": w,
        "height": h,
        "aspect": h / w,
        "skin_area": skin_m.sum() / scale / scale / head_r**2,
        "ink_share": ink.sum() / max(1, nonwhite.sum()),
        "narrowest_run": _narrowest_run(skin_m) / outline_px,
    }


def gate_verdict(m: dict) -> dict[str, bool]:
    return {k: lo <= m[k] <= hi for k, (lo, hi) in GATE.items()}


def all_presets():
    return PRESETS


def with_height(p: c.CharacterParams, h: float) -> c.CharacterParams:
    return replace(p, height=h)
