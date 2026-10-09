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

from ..character import OUTLINE, CharacterParams, _hand_centre, render_character, skeleton_for


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

    def hand(self, side: str) -> tuple[float, float]:
        """Where a hand is, in panel coordinates, with its arm's swing applied.

        `side` is `"left"` or `"right"` as the **character** has it, so Satoshi's left
        hand is on the viewer's right until the figure is flipped, and then it is on the
        viewer's left. What a held prop is placed by.
        """
        sk = skeleton_for(self.character)
        k = self.height / sk.canvas_h
        left = self.x - sk.canvas_w * k / 2
        # `_hand_centre`'s own side is the viewer's, -1 the left: the character's right.
        hx, hy = _hand_centre(sk, self.character, -1 if side == "right" else 1)
        px = sk.head_cx + hx * sk.head_r
        py = sk.head_cy + hy * sk.head_r
        x = left + sk.canvas_w * k - px * k if self.flip else left + px * k
        return x, self.feet_y - sk.foot_y * k + py * k


@dataclass(frozen=True)
class Camera:
    """Where a panel looks: the point of the scene at its centre, and how far in.

    `zoom` is panel pixels per scene pixel. Everything in a panel's scene (backdrop,
    figures, foreground) is drawn in scene coordinates and seen through this, so one
    scene can be shot wide, then close, then at a detail, with nothing redrawn. A
    drawing is vector, so a closer shot costs nothing.
    """

    x: float
    y: float
    zoom: float = 1.0


# How a shot is framed on a figure, in head radii: how far below the head's centre
# the middle of the picture sits, and how many head radii tall the picture is. A
# head radius is 0.135 of the figure's canvas height, so a figure 340 px tall has a
# head radius of about 46 px and its feet 5.5 radii below the head's centre.
SHOTS: dict[str, tuple[float, float]] = {
    "full": (2.7, 7.6),  # head to boots
    "medium": (1.5, 5.4),  # to the waist
    "close": (0.55, 3.7),  # head and shoulders
    "choker": (0.15, 1.5),  # brow to mouth
}


def frame(placement: Placement, shot: str, panel_height: float) -> Camera:
    """A camera on `placement`, framed as `shot` (a key of `SHOTS`), filling `panel_height`."""
    below, span = SHOTS[shot]
    hx, hy, hr = placement.head()
    return Camera(hx, hy + below * hr, panel_height / (span * hr))


def frame_point(x: float, y: float, span: float, panel_height: float) -> Camera:
    """A camera on a point, showing `span` scene pixels from top to bottom: a detail shot."""
    return Camera(x, y, panel_height / span)


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
    # SVG drawn over the figures and under the overlay, in the scene's coordinates and
    # seen through `view` like the rest of it: a counter in front of the person behind it.
    foreground: str = ""
    # Where the panel looks. None draws the scene as it stands, one unit to a pixel from
    # the panel's top-left corner, as before. Placements, backdrop and foreground are in
    # scene coordinates; `overlay` is in the panel's own, so type stays one size.
    view: Camera | None = None
    # The gap above this panel in the strip: a number of pixels, or the name of one in
    # `Strip.gaps` ("beat", "pause", "scene"). None takes `Strip.gutter`. Ignored for the
    # first panel. The gap is the pacing: how far a reader scrolls before the next panel.
    gap_before: float | str | None = None
    # Speech bubbles and captions as objects, drawn last of all, in the panel's own
    # coordinates. Each has an `svg()` method (see `bubbles.Bubble`); kept as objects
    # rather than strings so `checks` can read where they are. Typed loosely so this
    # module does not import the text code, which needs the optional `comic` extra.
    bubbles: tuple = ()

    def heads(self) -> list[tuple[float, float, float]]:
        """Every figure's head as (x, y, radius) in the panel's own coordinates."""
        zoom = self.view.zoom if self.view else 1.0
        out = []
        for pl in self.placements:
            hx, hy, hr = pl.head()
            x, y = self.to_panel(hx, hy)
            out.append((x, y, hr * zoom))
        return out

    def to_panel(self, x: float, y: float) -> tuple[float, float]:
        """A point of the scene in the panel's own coordinates, for aiming a bubble's tail."""
        if self.view is None:
            return x, y
        v = self.view
        return self.width / 2 + (x - v.x) * v.zoom, self.height / 2 + (y - v.y) * v.zoom


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
    # The named gaps a panel can ask for with `gap_before`. Starting points to try on a
    # phone: the sources disagree on the numbers (`docs/comic/research.md`).
    gaps: dict[str, float] = field(
        default_factory=lambda: {"beat": 40.0, "pause": 200.0, "scene": 700.0}
    )
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
    scene = f"{panel.backdrop}\n{figures}\n{panel.foreground}"
    if panel.view is not None:
        v = panel.view
        move = (
            f"translate({w / 2 - v.x * v.zoom:.3f} {h / 2 - v.y * v.zoom:.3f}) scale({v.zoom:.5f})"
        )
        scene = f'<g transform="{move}">\n{scene}\n</g>'
    border = (
        f'<rect x="0" y="0" width="{w:.2f}" height="{h:.2f}" fill="none" '
        f'stroke="{ink}" stroke-width="{panel.border:.2f}" />'
        if panel.border
        else ""
    )
    return (
        f'<g transform="translate({x:.2f} {y:.2f})">\n'
        f'<clipPath id="{clip}"><rect x="0" y="0" width="{w:.2f}" height="{h:.2f}" /></clipPath>\n'
        f'<g clip-path="url(#{clip})">\n{scene}\n{panel.overlay}\n{"".join(b.svg() for b in panel.bubbles)}\n</g>\n'
        f"{border}\n</g>"
    )


def _gap(strip: Strip, panel: Panel) -> float:
    """The paper above `panel`: its own gap if it names or gives one, else the strip's gutter."""
    g = panel.gap_before
    if g is None:
        return strip.gutter
    if isinstance(g, str):
        if g not in strip.gaps:
            raise ValueError(f"no gap called {g!r}; the strip has {sorted(strip.gaps)}")
        return strip.gaps[g]
    return float(g)


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
        if i:
            y += _gap(strip, panel)
        x = strip.margin + (inner - panel.width) / 2
        parts.append(_panel(panel, i, x, y, strip.ink))
        y += panel.height
    height = y + strip.margin if strip.panels else 2 * strip.margin
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
