"""Flat shapes for backdrops: a wall, a floor, a window, a table, a bank of mist.

Generic pieces only. The places a story needs (an inn's common room, the road to
a valley) are built from these by the story's own repo. Every function returns
SVG in panel coordinates, flat colour and a hard outline, no gradient, matching
the cast and the cover: a backdrop does not try to beat painted art on its own
ground (`cover.py`, the owner's call of 2026-08-08).

A shape that needs a `<clipPath>` takes a `uid` so two of them on one page never
share an id; the caller makes it unique, as the strip does for panels.
"""

from __future__ import annotations

from ..character import OUTLINE
from ..cover import mist_band

LINE = 2.6


def rect(x: float, y: float, w: float, h: float, fill: str, stroke: str | None = None) -> str:
    """A plain rectangle, outlined when `stroke` is given."""
    edge = f' stroke="{stroke}" stroke-width="{LINE}"' if stroke else ""
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}"{edge} />'


def planks(x: float, y: float, w: float, h: float, fill: str, seam: str, rows: int = 4) -> str:
    """A floor or a wall of horizontal boards: a fill and `rows - 1` seams across it."""
    lines = "".join(
        f'<line x1="{x:.2f}" y1="{y + h * i / rows:.2f}" x2="{x + w:.2f}" y2="{y + h * i / rows:.2f}" '
        f'stroke="{seam}" stroke-width="{LINE * 0.7:.2f}" />'
        for i in range(1, rows)
    )
    return rect(x, y, w, h, fill) + lines


def window(
    x: float,
    y: float,
    w: float,
    h: float,
    uid: str,
    outside: str = "",
    glass: str = "#9fb0b3",
    frame: str = "#6b5640",
    border: float = 12.0,
    bars: tuple[int, int] = (2, 2),
    sill: bool = True,
) -> str:
    """A window seen from inside, front on.

    The glass is `glass`, with `outside` drawn over it and clipped to it, in panel
    coordinates, so whatever is beyond (a wall of mist, the night) is placed on the
    panel and the window is a frame cut through it. `bars` is columns and rows of
    panes. The frame and the sill are the wood's one flat colour.
    """
    gx, gy, gw, gh = x + border, y + border, w - 2 * border, h - 2 * border
    clip = f"win-{uid}"
    cols, rows = bars
    mullions = "".join(
        rect(gx + gw * i / cols - border / 4, gy, border / 2, gh, frame) for i in range(1, cols)
    ) + "".join(
        rect(gx, gy + gh * j / rows - border / 4, gw, border / 2, frame) for j in range(1, rows)
    )
    ledge = rect(x - border * 0.6, y + h - border * 0.2, w + border * 1.2, border * 0.9, frame, OUTLINE) if sill else ""
    return (
        f'<clipPath id="{clip}"><rect x="{gx:.2f}" y="{gy:.2f}" width="{gw:.2f}" height="{gh:.2f}" /></clipPath>'
        + rect(x, y, w, h, frame, OUTLINE)
        + rect(gx, gy, gw, gh, glass)
        + f'<g clip-path="url(#{clip})">{outside}</g>'
        + rect(gx, gy, gw, gh, "none", OUTLINE)
        + mullions
        + ledge
    )


def table(
    x: float, y: float, w: float, top: float, leg: float, fill: str, leg_w: float = 14.0
) -> str:
    """A table seen from the front, its top edge at `y`: a slab of thickness `top` on two legs."""
    legs = rect(x + 10, y + top, leg_w, leg, fill, OUTLINE) + rect(
        x + w - 10 - leg_w, y + top, leg_w, leg, fill, OUTLINE
    )
    return legs + rect(x, y, w, top, fill, OUTLINE)


def mist(width: float, y: float, tones: tuple[str, ...], depth: float, scale: float = 0.18) -> str:
    """Banks of mist, back to front, one per tone, each a little lower than the last.

    Uses the cover's `mist_band`, so the mist here is the cover's mist. `tones` runs
    dark to light, back to front, as the cover's palette does.
    """
    step = depth / max(len(tones), 1)
    return "".join(
        mist_band(width, y + i * step * 0.6, depth - i * step * 0.5, tone, seed=3 + 5 * i, scale=scale)
        for i, tone in enumerate(tones)
    )
