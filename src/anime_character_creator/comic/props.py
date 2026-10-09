"""Things held or set down, as flat shapes in panel coordinates.

A prop is drawn where the caller puts it, usually from a hand's position
(`Placement.hand`), and in the panel's `overlay`, so it lies over the figures: the
hands that hold a tray are under it. Not a part of the character, so nothing here
touches the renderer, and a character holds nothing by default.

`scale` is the figure's canvas height over 340, so a prop sized for one figure keeps its
proportion to a figure drawn larger or smaller.
"""

from __future__ import annotations

from ..character import OUTLINE

LINE = 2.6


def tray(
    cx: float, cy: float, scale: float = 1.0, wood: str = "#8a6a45", rim: str = "#6b5136"
) -> str:
    """A serving tray seen from the front and a little above: a flat dish with a raised rim."""
    w, h = 120 * scale, 16 * scale
    return (
        f'<rect x="{cx - w / 2:.2f}" y="{cy - h / 2:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{h / 2:.2f}" '
        f'fill="{rim}" stroke="{OUTLINE}" stroke-width="{LINE}" />'
        f'<rect x="{cx - w / 2 + 6 * scale:.2f}" y="{cy - h / 2 + 3 * scale:.2f}" width="{w - 12 * scale:.2f}" '
        f'height="{4 * scale:.2f}" fill="{wood}" />'
    )


def mug(
    cx: float, base_y: float, scale: float = 1.0, body: str = "#a9794a", ink: str = OUTLINE
) -> str:
    """A mug standing with its base on `base_y`: a tapered cup and a handle on the right."""
    w, h = 26 * scale, 30 * scale
    x0, y0 = cx - w / 2, base_y - h
    handle = (
        f'<path d="M {x0 + w:.2f} {y0 + h * 0.25:.2f} q {w * 0.5:.2f} 0 {w * 0.5:.2f} {h * 0.3:.2f} '
        f'q 0 {h * 0.25:.2f} {-w * 0.5:.2f} {h * 0.25:.2f}" fill="none" stroke="{ink}" '
        f'stroke-width="{LINE * 1.6:.2f}" />'
    )
    cup = (
        f'<path d="M {x0:.2f} {y0:.2f} L {x0 + w:.2f} {y0:.2f} L {x0 + w * 0.88:.2f} {base_y:.2f} '
        f'L {x0 + w * 0.12:.2f} {base_y:.2f} Z" fill="{body}" stroke="{ink}" stroke-width="{LINE}" '
        f'stroke-linejoin="round" />'
    )
    return handle + cup
