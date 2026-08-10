"""Lay the cast out on one page: a labelled grid of characters.

The answer to `ref/character_sheet_satoshi.png`, and the tool the rest of the
cast gets built against. It exists before most of the characters do, on purpose:
`CLAUDE.md` says this is an iterate-by-looking project, and the size a character
is actually looked at here is a tile about a sixth of the page wide. That is the
size a design has to survive, and it is not the size a single render is judged
at. The cover's expression pass on 2026-08-08 measured the same thing from the
other end: a brow moves under 1% of a face and a lid two to three times that, so
what reads at full height routinely vanishes when shrunk.

A sheet is also how a *cast* gets judged, which no per-character render can do.
Whether twelve people look like they come from one world is a question about the
set, and the only way to ask it is to put them side by side.

Construction follows `cover.py`: authored geometry, flat tones, no gradients, and
the figures come through `render_character` unchanged rather than being drawn a
second way. What this adds over the cover is only a grid and some text.

**Two checked-in sheets, one for each reference roster.** The references are
two rosters of twelve that share ten members and swap one slot each,
Satoshi and Tomohiro against Satoko and Kyoko: `ROSTERS["cast"]` carries all
fourteen and is what `sheet.svg` draws, `ROSTERS["satoshi"]` is Satoshi's
persona rather than Satoko's and is what `sheet_satoshi.svg` draws, derived
from `cast` rather than listed a second time. The owner's call on
2026-08-09; before that the split was deferred as not worth two artifacts
to keep fresh for no gain, which stopped being true the day somebody
wanted to look at both.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field, replace
from pathlib import Path

from .character import OUTLINE, render_character
from .presets import DISPLAY_NAMES, PRESETS, ROSTERS
from .skeleton import BUILDS, build_skeleton


@dataclass(frozen=True)
class SheetPalette:
    """Dark ground, light cards, white labels.

    Taken from the reference sheets, and worth keeping rather than inverting:
    the figures carry a `#0d0d0d` outline, so they need a light card under them
    to hold their silhouette, and a dark surround is what stops twelve light
    cards from merging into one white field.
    """

    ground: str = "#161619"
    card: str = "#f2f2f0"
    label: str = "#ffffff"
    ink: str = OUTLINE


@dataclass(frozen=True)
class SheetParams:
    """One sheet. A roster, a grid, and how big a figure sits in its tile."""

    roster: str = "cast"
    # An explicit list of preset names, overriding `roster`. This is how a
    # harness draws a set that is not a named roster without inventing one.
    members: tuple[str, ...] | None = None
    build: str = "chibi"
    # Four across, which is what both reference sheets use and what keeps a tile
    # wide enough to read at page width. The number of rows follows from the
    # roster, so a sheet never has to be re-laid-out as the cast fills in.
    columns: int = 4
    tile_w: float = 300.0
    tile_h: float = 400.0
    gap: float = 16.0
    margin: float = 20.0
    # Room above each card for its name. A band rather than an overlay: a label
    # inside the card would sit on the figure at the sizes that matter.
    label_h: float = 34.0
    label_size: float = 21.0
    label_font: str = "Helvetica, Arial, sans-serif"
    # How much of a tile's height the figure fills, and where its soles land.
    # Both fractions of the tile, so the figure keeps its place when a tile is
    # resized.
    figure_height: float = 0.86
    figure_feet_y: float = 0.94
    palette: SheetPalette = field(default_factory=SheetPalette)


def members_of(p: SheetParams) -> tuple[str, ...]:
    """Who is on this sheet, and a hard error if any of them is not a character.

    A roster naming a preset that does not exist is the failure this catches:
    the grid would simply be one tile shorter, which looks like a layout choice
    rather than a missing character.
    """
    names = p.members if p.members is not None else ROSTERS[p.roster]
    missing = [n for n in names if n not in PRESETS]
    if missing:
        raise KeyError(f"roster names {missing}, which are not in PRESETS")
    return tuple(names)


def _grid(p: SheetParams, count: int) -> tuple[float, float, int]:
    """Page size and row count for this many tiles."""
    rows = max(1, -(-count // p.columns))
    cell_h = p.label_h + p.tile_h
    w = p.margin * 2 + p.columns * p.tile_w + (p.columns - 1) * p.gap
    h = p.margin * 2 + rows * cell_h + (rows - 1) * p.gap
    return w, h, rows


def _tile_origin(p: SheetParams, i: int) -> tuple[float, float]:
    col, row = i % p.columns, i // p.columns
    x = p.margin + col * (p.tile_w + p.gap)
    y = p.margin + row * (p.label_h + p.tile_h + p.gap)
    return x, y


def _label(p: SheetParams, name: str, x: float, y: float) -> str:
    """The character's name, centred over its card.

    Plain fill, no outline. The cover's title needs a stroke because it sits on
    a picture; this sits on a flat dark ground where a stroke would only thicken
    the letters.
    """
    return (
        f'<text x="{x + p.tile_w / 2:.1f} " y="{y + p.label_h - 9:.1f}" text-anchor="middle" '
        f'font-family="{p.label_font}" font-size="{p.label_size:.1f}" font-weight="bold" '
        f'fill="{p.palette.label}">{name}</text>'
    )


def _tile(p: SheetParams, preset: str, x: float, y: float) -> str:
    """One card with one figure standing on it.

    The figure is scaled off its own skeleton rather than off the drawing's
    bounding box, so every tile puts its character at the same *body* scale.
    Fitting each figure to its own ink instead would silently enlarge whoever
    happens to be drawn smallest, which on a cast sheet reads as that character
    being taller than the others.
    """
    top = y + p.label_h
    character = PRESETS[preset]
    sk = build_skeleton(heads=BUILDS[p.build], frame=character.frame)
    k = (p.tile_h * p.figure_height) / sk.canvas_h
    fx = x + p.tile_w / 2 - sk.canvas_w * k / 2
    fy = top + p.tile_h * p.figure_feet_y - sk.foot_y * k
    doc = render_character(character, sk)
    body = re.sub(r"\A<svg[^>]*>\s*", "", doc)
    body = re.sub(r"</svg>\s*\Z", "", body).strip()
    return (
        f'<rect x="{x:.1f}" y="{top:.1f}" width="{p.tile_w:.1f}" height="{p.tile_h:.1f}" '
        f'fill="{p.palette.card}" />\n'
        f"  {_label(p, DISPLAY_NAMES[preset], x, y)}\n"
        f'  <g transform="translate({fx:.1f} {fy:.1f}) scale({k:.4f})">\n  {body}\n  </g>'
    )


def render_sheet(p: SheetParams | None = None) -> str:
    """Draw one sheet and return the whole SVG document as a string.

    Deterministic, like `render_character` and `render_cover`: same params, same
    bytes, which is what lets `ref-out/` be compared rather than eyeballed.
    """
    p = p or SheetParams()
    names = members_of(p)
    w, h, _rows = _grid(p, len(names))
    tiles = []
    for i, preset in enumerate(names):
        x, y = _tile_origin(p, i)
        tiles.append(_tile(p, preset, x, y))
    body = "\n  ".join(tiles)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
        f'viewBox="0 0 {w:.0f} {h:.0f}">\n'
        f'  <rect width="{w:.0f}" height="{h:.0f}" fill="{p.palette.ground}" />\n'
        f"  {body}\n"
        f"</svg>\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Render the cast as a labelled grid.")
    ap.add_argument("--out", default="out/sheet/sheet", help="output path prefix (no extension)")
    ap.add_argument("--roster", default="cast", choices=sorted(ROSTERS))
    ap.add_argument("--build", default="chibi", choices=sorted(BUILDS))
    ap.add_argument("--columns", type=int, default=4)
    ap.add_argument(
        "--members",
        default=None,
        help="comma-separated preset names, overrides --roster",
    )
    args = ap.parse_args()

    members = tuple(m.strip() for m in args.members.split(",")) if args.members else None
    p = replace(
        SheetParams(), roster=args.roster, build=args.build, columns=args.columns, members=members
    )
    svg = render_sheet(p)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".svg").write_text(svg)
    print(f"wrote {out.with_suffix('.svg')}")

    try:
        import cairosvg

        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(out.with_suffix(".png")), scale=2)
        print(f"wrote {out.with_suffix('.png')}")
    except ImportError:
        print("cairosvg not installed; skipping PNG export")
    except OSError as e:
        print(f"cairosvg needs the system cairo library ({e}); SVG was still written")


if __name__ == "__main__":
    main()
