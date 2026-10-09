"""Set text in the bundled font as SVG outlines.

Copied from `../valley_of_mist`'s trailer (`valley_of_mist_tools/trailer/text.py`),
which wrote it first; the trailer is to switch to this copy, and nothing here is
specific to it. Needs the optional `comic` extra (`uharfbuzz`, `fonttools`). The font
is Gelasio, under the SIL Open Font License (`fonts/OFL.txt`).

cairosvg draws `<text>` through whatever fonts the system has, so a font-family
stack renders differently on another machine (the cover's own docstring says
as much). Shaping with HarfBuzz and drawing each glyph's outline as a path takes
the system out of it: same font file, same bytes, anywhere. It also keeps
kerning, which a hand-rolled advance-width layout would lose.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache, lru_cache
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

FONT_DIR = Path(__file__).parent / "fonts"
FONTS = {
    "regular": FONT_DIR / "Gelasio-Regular.ttf",
    "italic": FONT_DIR / "Gelasio-Italic.ttf",
    "bold": FONT_DIR / "Gelasio-Bold.ttf",
}


@dataclass(frozen=True)
class _Face:
    hb_font: hb.Font
    glyph_set: object
    glyph_order: list[str]
    upem: int


@cache
def _face(style: str) -> _Face:
    path = FONTS[style]
    blob = hb.Blob.from_file_path(str(path))
    face = hb.Face(blob)
    tt = TTFont(str(path))
    return _Face(hb.Font(face), tt.getGlyphSet(), tt.getGlyphOrder(), face.upem)


@cache
def _glyph_path(style: str, gid: int) -> str:
    f = _face(style)
    pen = SVGPathPen(f.glyph_set)
    f.glyph_set[f.glyph_order[gid]].draw(pen)
    return pen.getCommands()


@lru_cache(maxsize=4096)
def _shape(style: str, text: str) -> tuple[tuple[int, float, float], ...]:
    """(glyph id, x, y) per glyph in font units, plus the total advance last."""
    f = _face(style)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(f.hb_font, buf, {"kern": True, "liga": True})
    out = []
    x = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions, strict=True):
        out.append((info.codepoint, x + pos.x_offset, float(pos.y_offset)))
        x += pos.x_advance
    out.append((-1, x, 0.0))
    return tuple(out)


def measure(text: str, size: float, style: str = "regular", spacing: float = 0.0) -> float:
    """Width of one line at `size` px, with `spacing` px added between glyphs."""
    glyphs = _shape(style, text)
    upem = _face(style).upem
    return glyphs[-1][1] * size / upem + spacing * max(len(glyphs) - 2, 0)


def wrap(text: str, size: float, max_width: float, style: str = "regular") -> list[str]:
    """Greedy word wrap to `max_width` px."""
    lines: list[str] = []
    line = ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and measure(trial, size, style) > max_width:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def line_svg(
    text: str,
    x: float,
    y: float,
    size: float,
    style: str = "regular",
    fill: str = "#ffffff",
    anchor: str = "start",
    spacing: float = 0.0,
    stroke: str | None = None,
    stroke_width: float = 0.0,
) -> str:
    """One line of text as paths, baseline at `y`.

    With `stroke`, each glyph is drawn twice, a heavy outline underneath and
    the fill on top, which is the cover's white-letter-ink-outline title look
    (`cover.py`'s `_text`, for the same reason: a stroke drawn over the fill
    eats the letterform from inside).
    """
    glyphs = _shape(style, text)
    upem = _face(style).upem
    s = size / upem
    width = measure(text, size, style, spacing)
    x0 = {"start": x, "middle": x - width / 2, "end": x - width}[anchor]
    under: list[str] = []
    over: list[str] = []
    for i, (gid, gx, gy) in enumerate(glyphs[:-1]):
        d = _glyph_path(style, gid)
        if not d:
            continue
        tx = x0 + gx * s + spacing * i
        ty = y - gy * s
        t = f'transform="translate({tx:.2f} {ty:.2f}) scale({s:.5f} {-s:.5f})"'
        if stroke:
            under.append(
                f'<path {t} d="{d}" fill="none" stroke="{stroke}" '
                f'stroke-width="{stroke_width / s:.1f}" stroke-linejoin="round" />'
            )
        over.append(f'<path {t} d="{d}" fill="{fill}" />')
    return "".join(under + over)


def block_svg(
    lines: list[str],
    x: float,
    y: float,
    size: float,
    leading: float = 1.3,
    **kw,
) -> str:
    """Several lines, the first baseline at `y`."""
    return "".join(
        line_svg(line, x, y + i * size * leading, size, **kw) for i, line in enumerate(lines)
    )
