"""A strip is panels stacked top to bottom; a panel is a frame with figures in it.

Everything is a pure function of the values passed in: the same strip gives the
same bytes, which is what lets a page be compared and regenerated like a sheet.

Coordinates inside a panel are the panel's own, origin at its top-left corner,
in pixels. A figure stands on `feet_y` and is `height` pixels tall measured as
its whole canvas, the way `cover.py` sizes it, so one number scales a character
and the same number gives the same size on every preset. A figure may stand
partly outside the panel: the panel clips it, which is how a close-up crops.

Each figure is rendered with its own id prefix (`render_character(id_prefix=)`)
and each panel clips under its own id, so nothing on a page shares an id.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ..character import OUTLINE, CharacterParams, render_character, skeleton_for


@dataclass(frozen=True)
class Placement:
    """One character in a panel.

    `x` is where the figure's centre line falls, `feet_y` where its soles land,
    `height` how tall its canvas is. `flip` mirrors it left to right about that
    centre line, so a character can face the other way across a conversation.
    `tone` draws the figure as a flat silhouette in that one colour, every fill and
    outline alike, which is how a figure is seen against a bright window or from the
    back without a back view being drawn.
    """

    character: CharacterParams
    x: float
    feet_y: float
    height: float
    flip: bool = False
    tone: str | None = None

    def head(self) -> tuple[float, float, float]:
        """The head's centre and radius in panel coordinates, for aiming a bubble's tail."""
        sk = skeleton_for(self.character)
        k = self.height / sk.canvas_h
        left = self.x - sk.canvas_w * k / 2
        hx = sk.head_cx * k
        hx = left + sk.canvas_w * k - hx if self.flip else left + hx
        return hx, self.feet_y - sk.foot_y * k + sk.head_cy * k, sk.head_r * k


@dataclass(frozen=True)
class Panel:
    """A frame of `width` by `height` pixels.

    `backdrop` is SVG drawn first, under the figures; `overlay` is drawn last,
    over them, for text and effects. Both are in panel coordinates and are
    clipped to the frame along with the figures. Figures are drawn in the order
    given, so a later one stands in front of an earlier one.
    """

    width: float
    height: float
    placements: tuple[Placement, ...] = ()
    backdrop: str = ""
    overlay: str = ""
    border: float = 3.0


@dataclass(frozen=True)
class Strip:
    """Panels stacked top to bottom on a sheet of `paper`.

    A panel narrower than the strip is centred. `margin` is the paper left on
    every side and `gutter` the paper between one panel and the next.
    """

    panels: tuple[Panel, ...]
    width: float = 800.0
    margin: float = 24.0
    gutter: float = 20.0
    paper: str = "#f4f1ea"
    ink: str = field(default=OUTLINE)


_PAINT = re.compile(r'(fill|stroke)="(?!none)[^"]*"')


def _silhouette(body: str, tone: str) -> str:
    """Every paint in the figure, fill and outline alike, replaced by one flat tone.

    Opacity goes too, so a faint shape does not leave a lighter patch in the figure.
    Clip paths are untouched: they decide the shape, not the colour.
    """
    body = _PAINT.sub(lambda m: f'{m.group(1)}="{tone}"', body)
    return re.sub(r'\sopacity="[^"]*"', "", body)


def _figure(pl: Placement, prefix: str) -> str:
    """The character, scaled, placed and namespaced."""
    sk = skeleton_for(pl.character)
    k = pl.height / sk.canvas_h
    left = pl.x - sk.canvas_w * k / 2
    top = pl.feet_y - sk.foot_y * k
    doc = render_character(pl.character, sk, id_prefix=prefix)
    body = re.sub(r"\A<svg[^>]*>\s*", "", doc)
    body = re.sub(r"</svg>\s*\Z", "", body).strip()
    if pl.tone:
        body = _silhouette(body, pl.tone)
    if pl.flip:
        move = f"translate({left + sk.canvas_w * k:.2f} {top:.2f}) scale({-k:.5f} {k:.5f})"
    else:
        move = f"translate({left:.2f} {top:.2f}) scale({k:.5f})"
    return f'<g transform="{move}">\n{body}\n</g>'


def _panel(panel: Panel, index: int, x: float, y: float, ink: str) -> str:
    """One panel at (x, y) on the page, clipped to its frame."""
    clip = f"panel-{index}"
    w, h = panel.width, panel.height
    figures = "\n".join(_figure(pl, f"p{index}f{j}") for j, pl in enumerate(panel.placements))
    border = (
        f'<rect x="0" y="0" width="{w:.2f}" height="{h:.2f}" fill="none" '
        f'stroke="{ink}" stroke-width="{panel.border:.2f}" />'
        if panel.border
        else ""
    )
    return (
        f'<g transform="translate({x:.2f} {y:.2f})">\n'
        f'<clipPath id="{clip}"><rect x="0" y="0" width="{w:.2f}" height="{h:.2f}" /></clipPath>\n'
        f'<g clip-path="url(#{clip})">\n{panel.backdrop}\n{figures}\n{panel.overlay}\n</g>\n'
        f"{border}\n</g>"
    )


def render_panel(panel: Panel, paper: str = "#f4f1ea", ink: str = OUTLINE) -> str:
    """One panel as a whole SVG document, for looking at it on its own."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{panel.width:.0f}" height="{panel.height:.0f}" '
        f'viewBox="0 0 {panel.width:.0f} {panel.height:.0f}">\n'
        f'<rect width="100%" height="100%" fill="{paper}" />\n'
        f"{_panel(panel, 0, 0, 0, ink)}\n</svg>\n"
    )


def render_strip(strip: Strip) -> str:
    """The whole strip as one SVG document."""
    inner = strip.width - 2 * strip.margin
    for panel in strip.panels:
        if panel.width > inner:
            raise ValueError(
                f"a {panel.width:g} px panel does not fit a strip {inner:g} px wide inside its margins"
            )
    y = strip.margin
    parts = []
    for i, panel in enumerate(strip.panels):
        x = strip.margin + (inner - panel.width) / 2
        parts.append(_panel(panel, i, x, y, strip.ink))
        y += panel.height + strip.gutter
    height = y - strip.gutter + strip.margin if strip.panels else 2 * strip.margin
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{strip.width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {strip.width:.0f} {height:.0f}">\n'
        f'<rect width="100%" height="100%" fill="{strip.paper}" />\n'
        + "\n".join(parts)
        + "\n</svg>\n"
    )


def write_strip(strip: Strip, path_prefix: str | Path) -> list[Path]:
    """Write `<prefix>.svg`, and `<prefix>.png` if cairosvg and cairo are there."""
    prefix = Path(path_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    svg = render_strip(strip)
    written = [prefix.with_suffix(".svg")]
    written[0].write_text(svg)
    try:
        import cairosvg

        png = prefix.with_suffix(".png")
        png.write_bytes(cairosvg.svg2png(bytestring=svg.encode(), scale=1))
        written.append(png)
    except (ImportError, OSError):
        pass
    return written
