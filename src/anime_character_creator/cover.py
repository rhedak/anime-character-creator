"""Compose a book cover: flat backdrop, mist banks, one character, title.

The character layers in `character.py` draw a figure on nothing. This draws the
page around one: a dark backdrop, banks of mist as flat shapes, the figure, and
the title over the top. It is the "backgrounds and text overlays as more SVG
layers" that the project has had in mind, and it obeys the same rules the figure
does. Every shape is authored geometry, nothing is composited from pre-made art,
no gradients and no blur anywhere: a mist bank is a hard-edged silhouette in one
flat tone, and depth comes from stacking several of them in a tone ladder rather
than from any softness. That is how flat vector art says "distance", and it is
the same reason the figure gets its form from outline rather than shading.

The palette ladder was sampled off `ref-local/cover_satoshi.png` rather than
picked: that reference is a painterly AI image and is not the target, but its
colour is a fair guide to the mood, and its bands run from a near-black sky
through blue-greens to a pale horizon.

**The chibi build is the design.** The owner's call on 2026-08-08, after seeing
both: `realistic` renders and is kept as a fallback, but the cover is composed
for the chibi and that is what `build` defaults to. Anything tuned here should
be judged at the chibi first.

**Simple is the design, not a stage on the way to something denser.** A ridge
and two clusters of ruined towers were built on top of this and then dropped, on
the owner's call of 2026-08-08 after seeing them: *do not try to beat the AI
generated cover on its own ground, stick to the simple style and sell it for what
it is.* They worked, in the sense that they rendered and read as ruins, and that
was the problem. They invited the comparison, and a flat cover loses a contest
about detail with a painted one while winning easily on being deliberate. So the
absence of a landscape here is a decision, and anyone adding one back is
reopening a settled question rather than finishing an unfinished job.

What is left is the composition that survived: a large centred figure standing in
mist under a stacked title, and nothing else on the page.
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass, field, replace
from pathlib import Path

from .character import OUTLINE, CharacterParams, render_character
from .presets import PRESETS
from .skeleton import BUILDS, Skeleton, build_skeleton


@dataclass(frozen=True)
class CoverPalette:
    """The flat tones the page is built from, back to front.

    A ladder rather than a pair, because that is what replaces the gradient a
    painted cover would use: each mist bank sits one rung lighter than the one
    behind it, so distance reads off the steps between flat tones.
    """

    sky: str = "#141c21"
    sky_low: str = "#1e2b30"
    # Dark to light, back to front. Five rungs rather than three because the
    # step between neighbours is what has to stay small: too few and each bank
    # reads as its own object with an edge, which is the thing mist should not
    # have.
    mist: tuple[str, ...] = ("#2b3d41", "#384b4d", "#47595a", "#586a69", "#6d7d7a")
    ink: str = OUTLINE
    title: str = "#ffffff"


@dataclass(frozen=True)
class CoverParams:
    """One cover. Everything a book needs to differ on lives here.

    `title` is a tuple of lines rather than one string because where a title
    breaks is a design decision about that specific title, not something a
    renderer should guess by measuring text it cannot measure reliably.
    """

    title: tuple[str, ...] = ("THE HERO", "OF THE MIST", "TRAGEDY")
    # Empty by default, and worth leaving that way unless there is a real
    # subtitle. A lone line under the figure reads as a **byline**, whoever it
    # names: the character's name there says he wrote the book. That is why the
    # first draft's "SATOSHI" came out, and it is a property of the position
    # rather than of the word.
    subtitle: str = ""
    preset: str = "satoshi"
    # `realistic` still renders and is the backup; the composition is tuned for
    # this one.
    build: str = "chibi"
    width: float = 1000.0
    height: float = 1500.0
    palette: CoverPalette = field(default_factory=CoverPalette)
    # A serif for the title, a sans for the name under it. These are family
    # stacks, not files: the renderer substitutes whatever the system has, so a
    # cover built on one machine can set in a different face on another. Fine
    # for a proof, worth pinning before anything goes to print.
    title_font: str = "Georgia, 'Times New Roman', serif"
    subtitle_font: str = "Helvetica, Arial, sans-serif"
    # How low each mist bump is against its width. See `_mist_band`: this is the
    # number that separates mist from foam.
    mist_flatness: float = 0.30
    # Where the figure sits, as fractions of the page.
    figure_height: float = 0.56
    figure_feet_y: float = 0.865


def _jitter(i: int) -> float:
    """A repeatable 0 to 1 from an index.

    Not an RNG: every other render in this project is byte-identical run to run,
    which is what lets output be compared rather than eyeballed, and a mist bank
    seeded from the clock would throw that away for no gain.
    """
    x = math.sin(i * 12.9898) * 43758.5453
    return x - math.floor(x)


def _mist_band(p: CoverParams, y: float, depth: float, color: str, seed: int, scale: float) -> str:
    """One bank of mist: low wide bumps along the top, flat along the bottom.

    The bumps are **elliptical, and much wider than they are tall**. Circular
    ones were tried first and are the single thing that decides whether this
    reads as mist or as a row of balloons: a semicircle is as tall as it is
    wide, so a line of them scallops, and scalloping says cloud, or bubbles, or
    foam. Flattening each bump to about a third of its width turns the same
    construction into a drifting bank. `flatness` is that ratio.

    The bumps also sit on one baseline. Varying the radius is what gives the
    bank its uneven skyline; varying the baseline as well breaks it into
    separate objects, which is what several overlapping bands are for.

    It runs off both edges of the page on purpose, so the bank is cut by the
    trim rather than ending inside the picture.
    """
    over = p.width * 0.1
    x = -over
    d = [f"M {-over:.1f} {y + depth:.1f}", f"L {-over:.1f} {y:.1f}"]
    i = seed
    while x < p.width + over:
        rx = p.width * scale * (0.5 + _jitter(i) * 1.1)
        ry = rx * p.mist_flatness
        x2 = x + rx * 2
        # Sweep 1 going right bulges the arc upward, which is the whole shape.
        d.append(f"A {rx:.1f} {ry:.1f} 0 0 1 {x2:.1f} {y:.1f}")
        x = x2
        i += 1
    d.append(f"L {x:.1f} {y + depth:.1f}")
    d.append("Z")
    return f'<path d="{" ".join(d)}" fill="{color}" />'


def _backdrop(p: CoverParams) -> str:
    """The sky, in two flat steps rather than a wash."""
    pal = p.palette
    horizon = p.height * 0.52
    return (
        f'<rect width="{p.width:.0f}" height="{p.height:.0f}" fill="{pal.sky}" />\n'
        f'  <rect y="{horizon:.1f}" width="{p.width:.0f}" '
        f'height="{p.height - horizon:.1f}" fill="{pal.sky_low}" />'
    )


def _placement(p: CoverParams) -> tuple[Skeleton, CharacterParams, float, float]:
    """Where the figure lands on the page: its skeleton, its scale, its offset.

    Split out from drawing it because the mist in front has to be positioned off
    the *body*, not off the page. `figure_feet_y` is where the soles land, and
    `sk.foot_y` is 485 on a 500-tall canvas, so anchoring the canvas edge there
    instead put every band 3% of a figure too high: the first attempt cut him
    across the shins and hid the boots entirely.
    """
    character = PRESETS[p.preset]
    sk = build_skeleton(heads=BUILDS[p.build], frame=character.frame)
    k = (p.height * p.figure_height) / sk.canvas_h
    x = p.width / 2 - sk.canvas_w * k / 2
    y = p.height * p.figure_feet_y - sk.foot_y * k
    return sk, character, k, x, y


def _figure(
    p: CoverParams, sk: Skeleton, character: CharacterParams, k: float, x: float, y: float
) -> str:
    """The character, scaled and placed.

    Rendered through `render_character` exactly as it is anywhere else, on
    transparency, which is what lets it sit on the mist with no card behind it.
    The document it returns is unwrapped and re-wrapped in a `<g>`: its own
    `<svg>` element carries a width, a height and a viewBox that would otherwise
    fight the page's.
    """
    doc = render_character(character, sk)
    body = re.sub(r"\A<svg[^>]*>\s*", "", doc)
    body = re.sub(r"</svg>\s*\Z", "", body).strip()
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.4f})">\n  {body}\n  </g>'


def _text(p: CoverParams, line: str, y: float, size: float, font: str, spacing: float) -> str:
    """One line, drawn twice: a heavy stroke underneath and the fill over it.

    The obvious single element with `paint-order="stroke"` is wrong here.
    cairosvg ignores that property silently, so the stroke lands on top of the
    fill and eats the letterforms from the inside, which at this weight leaves
    the shorter lines almost solid black. Two elements is the portable way to
    say "white letter, ink outline".
    """
    common = (
        f'x="{p.width / 2:.1f}" y="{y:.1f}" text-anchor="middle" font-family="{font}" '
        f'font-size="{size:.1f}" font-weight="bold" letter-spacing="{spacing:.1f}"'
    )
    return (
        f'<text {common} fill="none" stroke="{p.palette.ink}" '
        f'stroke-width="{size * 0.155:.1f}" stroke-linejoin="round">{line}</text>\n'
        f'  <text {common} fill="{p.palette.title}">{line}</text>'
    )


def render_cover(p: CoverParams | None = None) -> str:
    """Draw one cover and return the whole SVG document as a string.

    Deterministic, like `render_character`: same params, same bytes.
    """
    p = p or CoverParams()
    pal = p.palette
    H = p.height

    # Back to front. Three banks behind the figure and two in front of his feet,
    # which is what puts him *in* the mist rather than on top of a picture of it.
    # Each entry is (top, bump width, seed); every bank runs to the bottom edge,
    # so a nearer one always covers the one behind and the tone ladder only ever
    # steps one rung at a visible edge.
    #
    # The two in front are placed off the figure rather than off the page: the
    # first has to cross his boots and the second his soles, and those move with
    # `figure_height`. Fixed fractions had him cut at the waist.
    sk, character, k, x, y = _placement(p)
    sole = y + sk.foot_y * k
    foot_h = (sk.foot_y - sk.ankle_y) * k

    # **Feet just covered, and no more** (the owner's call). The subtlety is that
    # a bank's waterline is not its baseline: the bumps rise above it, by
    # `rx * mist_flatness`, and `rx` is the widest of a jittered range. So the
    # front banks are sized from the boot rather than positioned by eye. Put the
    # baseline on the soles and make the tallest possible bump exactly one boot
    # high, and the mist line then wanders around the top of the foot, burying it
    # where a bump peaks and leaving the heel showing between them. That wobble
    # is the point: a flat line across both ankles would read as water.
    near = foot_h / (p.width * 1.6 * p.mist_flatness)

    behind = [(0.455, 0.055, 3), (0.56, 0.07, 17), (0.655, 0.085, 41)]
    layers = [_backdrop(p)]
    for i, (top, scale, seed) in enumerate(behind):
        layers.append(_mist_band(p, H * top, H - H * top, pal.mist[i], seed, scale))
    layers.append(_figure(p, sk, character, k, x, y))
    layers.append(_mist_band(p, sole, H - sole, pal.mist[3], 59, near))
    layers.append(_mist_band(p, sole + foot_h * 0.7, H, pal.mist[4], 83, near * 1.25))

    size = H * 0.072
    top = H * 0.115
    for i, line in enumerate(p.title):
        layers.append(_text(p, line, top + i * size * 1.16, size, p.title_font, size * 0.02))
    if p.subtitle:
        layers.append(_text(p, p.subtitle, H * 0.93, H * 0.038, p.subtitle_font, H * 0.010))

    body = "\n  ".join(layer for layer in layers if layer)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{p.width:.0f}" height="{H:.0f}" '
        f'viewBox="0 0 {p.width:.0f} {H:.0f}">\n'
        f"  {body}\n"
        f"</svg>\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Render a book cover around one character.")
    ap.add_argument("--out", default="out/cover/cover", help="output path prefix (no extension)")
    ap.add_argument("--preset", default="satoshi", choices=sorted(PRESETS))
    ap.add_argument("--build", default="chibi", choices=sorted(BUILDS))
    ap.add_argument(
        "--title",
        action="append",
        help="one title line; repeat the flag, the breaks are yours to choose",
    )
    ap.add_argument("--subtitle", default="", help="smaller line under the figure")
    ap.add_argument("--width", type=float, default=1000.0)
    ap.add_argument("--height", type=float, default=1500.0)
    args = ap.parse_args()

    p = CoverParams(preset=args.preset, build=args.build, width=args.width, height=args.height)
    if args.title:
        p = replace(p, title=tuple(args.title))
    p = replace(p, subtitle=args.subtitle)

    svg = render_cover(p)
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
