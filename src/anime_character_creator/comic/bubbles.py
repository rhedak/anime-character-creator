"""Captions and speech bubbles, drawn as flat shapes with outline text inside.

A caption is the narrator's box; a bubble is a character's voice and points at
them with a tail. Both return SVG for a panel's `overlay`, in panel coordinates,
and both set their text with `text.py`, so the width of a line is measured and
not guessed and the same font gives the same bytes everywhere.

Flat colour and a hard outline, like everything else here: no shadow, no
gradient. The tail is part of the bubble's outline, not a second shape laid on
top of it.
"""

from __future__ import annotations

import math

from ..character import OUTLINE
from . import text

PAPER = "#fbf8ee"
LINE = 2.6


def _lines(content: str, size: float, width: float, style: str) -> list[str]:
    """Wrap each paragraph to `width`; a blank-line break keeps its paragraphs apart."""
    out: list[str] = []
    for para in content.split("\n"):
        out.extend(text.wrap(para, size, width, style) or [""])
    return out


def caption_svg(
    content: str,
    x: float,
    y: float,
    width: float,
    size: float = 17.0,
    style: str = "italic",
    pad: float = 11.0,
    fill: str = PAPER,
    ink: str = OUTLINE,
) -> tuple[str, float]:
    """The narrator's box, top-left at (x, y), `width` wide. Returns it and its height.

    The height follows the text, so a caller stacking captions or placing one at
    the bottom of a panel needs it back.
    """
    lines = _lines(content, size, width - 2 * pad, style)
    leading = 1.3
    height = 2 * pad + size * leading * len(lines) - size * (leading - 1) + size * 0.25
    box = (
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" '
        f'fill="{fill}" stroke="{ink}" stroke-width="{LINE}" />'
    )
    words = text.block_svg(
        lines, x + pad, y + pad + size * 0.85, size, leading=leading, style=style, fill=ink
    )
    return box + words, height


def bubble_svg(
    content: str,
    cx: float,
    cy: float,
    max_width: float,
    tail_to: tuple[float, float] | None = None,
    size: float = 19.0,
    style: str = "regular",
    pad: float = 9.0,
    fill: str = PAPER,
    ink: str = OUTLINE,
) -> str:
    """A speech bubble centred on (cx, cy), its text wrapped to `max_width`.

    The bubble is an ellipse just large enough to hold the text block. With
    `tail_to` a tail runs from the bubble's edge to that point, which is where the
    speaker is; without it the bubble floats, for a voice off the panel.
    """
    lines = _lines(content, size, max_width, style)
    leading = 1.28
    tw = max(text.measure(line, size, style) for line in lines)
    th = size * leading * len(lines) - size * (leading - 1)
    # A rectangle fits an ellipse of the same shape when each half-side is
    # stretched by the square root of two; the padding goes in before that.
    a = (tw / 2 + pad) * math.sqrt(2)
    b = (th / 2 + pad) * math.sqrt(2)
    words = text.block_svg(
        lines,
        cx,
        cy - th / 2 + size * 0.82,
        size,
        leading=leading,
        style=style,
        fill=ink,
        anchor="middle",
    )
    return _outline(cx, cy, a, b, tail_to, size, fill, ink) + words


def _ray(a: float, b: float, angle: float) -> tuple[float, float]:
    """Where a ray from an ellipse's centre at `angle` leaves it, relative to the centre."""
    ux, uy = math.cos(angle), math.sin(angle)
    k = 1.0 / math.sqrt((ux / a) ** 2 + (uy / b) ** 2)
    return ux * k, uy * k


def _outline(
    cx: float,
    cy: float,
    a: float,
    b: float,
    tail_to: tuple[float, float] | None,
    size: float,
    fill: str,
    ink: str,
) -> str:
    """The bubble's outline: the ellipse, with the tail as part of the same path.

    One path rather than a tail laid against an ellipse, so there is no seam to
    hide: the outline goes round the long way from one corner of the tail's base
    to the other, then out to the tip and back. The base is two points on the
    ellipse either side of the line to the target, a gap that grows with the type
    so a big bubble gets a firm tail.
    """
    style = f'fill="{fill}" stroke="{ink}" stroke-width="{LINE}" stroke-linejoin="miter"'
    if tail_to is not None:
        dx, dy = tail_to[0] - cx, tail_to[1] - cy
        rx, ry = _ray(a, b, math.atan2(dy, dx))
        # A target inside the ellipse has no tail to draw.
        if math.hypot(dx, dy) > math.hypot(rx, ry) + size * 0.4:
            theta = math.atan2(dy, dx)
            half = math.atan2(size * 0.5, math.hypot(rx, ry))
            x1, y1 = _ray(a, b, theta + half)
            x2, y2 = _ray(a, b, theta - half)
            # Clockwise on screen from one corner to the other, the long way round.
            d = (
                f"M {cx + x1:.2f} {cy + y1:.2f} "
                f"A {a:.2f} {b:.2f} 0 1 1 {cx + x2:.2f} {cy + y2:.2f} "
                f"L {tail_to[0]:.2f} {tail_to[1]:.2f} Z"
            )
            return f'<path d="{d}" {style} />'
    return f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{a:.2f}" ry="{b:.2f}" {style} />'
