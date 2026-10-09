"""Checks on a panel's lettering, from the conventions in `docs/comic/research.md`.

Each check returns plain sentences naming what is wrong and where, and an empty list
means nothing was found. They are conventions, not laws: a panel may break one on
purpose, and then the sentence is the thing to look at, not an error to silence. What
they catch is the ordinary accident, a bubble drawn over the face it belongs to.

Looks only at `Panel.bubbles` and the figures' heads, so a bubble written straight into
`Panel.overlay` as SVG is invisible to it.
"""

from __future__ import annotations

import math
import re

from .bubbles import Bubble
from .layout import Panel, Strip

MAX_BUBBLES = 3
MAX_SENTENCES = 4
MIN_TYPE = 17.0
EDGE = 6.0  # a bubble closer to the frame than this touches it


def _inside(x: float, y: float, e: tuple[float, float, float, float], grow: float = 0.0) -> bool:
    cx, cy, rx, ry = e
    return ((x - cx) / (rx + grow)) ** 2 + ((y - cy) / (ry + grow)) ** 2 <= 1.0


def _touches_ellipse(e1, e2) -> bool:
    """Whether two ellipses overlap, by sampling the first's rim and centre against the second."""
    cx, cy, rx, ry = e1
    pts = [(cx, cy)] + [
        (cx + rx * math.cos(t * math.pi / 12), cy + ry * math.sin(t * math.pi / 12))
        for t in range(24)
    ]
    return any(_inside(x, y, e2) for x, y in pts) or any(
        _inside(x, y, e1)
        for x, y in [(e2[0], e2[1])]
        + [
            (e2[0] + e2[2] * math.cos(t * math.pi / 12), e2[1] + e2[3] * math.sin(t * math.pi / 12))
            for t in range(24)
        ]
    )


def _hits_head(e, head) -> bool:
    """Whether the ellipse covers the face: the head's centre, or its ring from the brows down.

    The top of the head is hair or a hat, which a bubble may overlap; the face is what
    it must not.
    """
    hx, hy, hr = head
    pts = [(hx, hy)] + [
        (hx + 0.85 * hr * math.cos(t * math.pi / 8), hy + 0.85 * hr * math.sin(t * math.pi / 8))
        for t in range(16)
    ]
    return any(_inside(x, y, e) for x, y in pts if y >= hy - 0.45 * hr)


def _cross(p1, p2, p3, p4) -> bool:
    """Whether segment p1-p2 crosses segment p3-p4."""

    def side(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    return side(p1, p2, p3) * side(p1, p2, p4) < 0 and side(p3, p4, p1) * side(p3, p4, p2) < 0


def check_panel(panel: Panel) -> list[str]:
    """What is wrong with this panel's lettering, as sentences. Empty when nothing is."""
    bubbles = [b for b in panel.bubbles if isinstance(b, Bubble)]
    out: list[str] = []
    if len(bubbles) > MAX_BUBBLES:
        out.append(f"{len(bubbles)} bubbles in one panel, more than {MAX_BUBBLES}")
    shapes = [b.shape() for b in bubbles]
    heads = panel.heads()
    for i, (b, e) in enumerate(zip(bubbles, shapes, strict=True), 1):
        name = f"bubble {i} ({b.text[:24]!r})"
        sentences = len([s for s in re.split(r"[.!?]+\s*", b.text) if s.strip()])
        if sentences > MAX_SENTENCES:
            out.append(f"{name} has {sentences} sentences, more than {MAX_SENTENCES}")
        if b.size < MIN_TYPE:
            out.append(f"{name} is set at {b.size:g} px, under {MIN_TYPE:g}")
        cx, cy, rx, ry = e
        if (
            cx - rx < EDGE
            or cy - ry < EDGE
            or cx + rx > panel.width - EDGE
            or cy + ry > panel.height - EDGE
        ):
            out.append(f"{name} touches or leaves the panel's edge")
        for k, head in enumerate(heads, 1):
            if _hits_head(e, head):
                out.append(f"{name} covers the face of figure {k}")
    for i in range(len(bubbles)):
        for j in range(i + 1, len(bubbles)):
            if _touches_ellipse(shapes[i], shapes[j]):
                out.append(f"bubbles {i + 1} and {j + 1} overlap")
            ti, tj = bubbles[i].tail_to, bubbles[j].tail_to
            if ti and tj and _cross(shapes[i][:2], ti, shapes[j][:2], tj):
                out.append(f"the tails of bubbles {i + 1} and {j + 1} cross")
            for a, b_ in ((i, j), (j, i)):
                tail = bubbles[a].tail_to
                if tail and any(_inside(*pt, shapes[b_]) for pt in _along(shapes[a][:2], tail)):
                    out.append(f"the tail of bubble {a + 1} runs through bubble {b_ + 1}")
                    break
            # Reading order: the first bubble is the highest, or the leftmost of a row.
            (_, cyi, _, ryi), (cxj, cyj, _, ryj) = shapes[i], shapes[j]
            cxi = shapes[i][0]
            above = cyj + ryj < cyi - ryi
            same_row = abs(cyj - cyi) < max(ryi, ryj)
            if above or (same_row and cxj < cxi):
                out.append(
                    f"bubble {j + 1} is read after bubble {i + 1} but sits above or left of it"
                )
    return out


def _along(a, b, steps: int = 12):
    """Points along the segment from a to b, past the first quarter, so the tail's root is not counted."""
    return [
        (a[0] + (b[0] - a[0]) * t / steps, a[1] + (b[1] - a[1]) * t / steps)
        for t in range(3, steps + 1)
    ]


def check_strip(strip: Strip) -> list[str]:
    """Every problem in a strip, each prefixed with its panel's number (from 1)."""
    return [f"panel {n}: {msg}" for n, p in enumerate(strip.panels, 1) for msg in check_panel(p)]
