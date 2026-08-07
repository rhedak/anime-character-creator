"""Enough of a test to catch a broken package, not a substitute for looking.

Whether a shape is *right* is decided by eye against `ref/`, which no assertion
can stand in for. What these do check is that the package imports, that every
named character renders at every named build, and that the four renders in
`ref-out/` are still what the code produces, which is the thing a refactor
breaks silently.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from anime_character_creator import (
    BUILDS,
    HAIRSTYLES,
    PRESETS,
    CharacterParams,
    build_skeleton,
    character,  # for the two private helpers the ceiling check needs
    render_character,
)

REF_OUT = Path(__file__).resolve().parent.parent / "ref-out"
SUFFIX = {"chibi": "", "realistic": "_real"}


@pytest.mark.parametrize("preset", sorted(PRESETS))
@pytest.mark.parametrize("build", sorted(BUILDS))
def test_named_characters_render(preset: str, build: str) -> None:
    p = PRESETS[preset]
    svg = render_character(p, build_skeleton(heads=BUILDS[build], frame=p.frame))
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert len(list(root)) > 10, "a character is many shapes; one or two means parts dropped out"


@pytest.mark.parametrize("hairstyle", sorted(HAIRSTYLES))
def test_every_hairstyle_renders_on_a_default_character(hairstyle: str) -> None:
    svg = render_character(CharacterParams(hairstyle=hairstyle))
    ET.fromstring(svg)


def test_render_is_deterministic() -> None:
    """`ref-out/` is compared byte for byte, so two runs have to agree."""
    p = PRESETS["satoko"]
    assert render_character(p) == render_character(p)


@pytest.mark.parametrize("preset", sorted(PRESETS))
@pytest.mark.parametrize("build", sorted(BUILDS))
def test_ref_out_matches_the_code(preset: str, build: str) -> None:
    """The same check `./refresh-ref-out.sh --check` makes, minus the PNGs.

    `ref-out/` is committed and the README displays it, so it is stale the
    moment a shape changes without it. If this fails after a deliberate shape
    change, the fix is to run the script, not to edit the expectation.
    """
    p = PRESETS[preset]
    committed = REF_OUT / f"{preset}{SUFFIX[build]}.svg"
    expected = render_character(p, build_skeleton(heads=BUILDS[build], frame=p.frame))
    assert committed.read_text() == expected, f"{committed.name} is stale: ./refresh-ref-out.sh"


def _highest_ink(start: tuple[float, float], segments: list) -> float:
    """The topmost y a quadratic chain reaches, in the units it is given in.

    Not the topmost anchor and not the topmost control point. A control point
    lies outside its curve, so taking the minimum over the raw point data says a
    crown is taller than it paints, and taking it over the anchors alone says a
    crown that peaks between two anchors is shorter than it paints. Only the
    second of those is dangerous, but both make the number useless as a bound, so
    this solves each segment for its own extremum.
    """
    ys = [start[1]]
    prev = start
    for ctrl, end in segments:
        ys.append(end[1])
        a, b, c = prev[1], ctrl[1], end[1]
        denom = a - 2 * b + c
        if denom != 0:
            t = (a - b) / denom
            if 0 < t < 1:
                ys.append((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t**2 * c)
        prev = end
    return min(ys)


@pytest.mark.parametrize("hairstyle", sorted(HAIRSTYLES))
@pytest.mark.parametrize("build", sorted(BUILDS))
def test_hair_stays_under_the_canvas_ceiling(hairstyle: str, build: str) -> None:
    """A crown taller than the headroom comes out sliced flat, silently.

    `build_skeleton`'s `hair_margin` is the only thing holding the top of the
    canvas off the hair, and nothing in the shape code knows about it, so a cut
    with a peak or a spike on it can exceed the bound and still render, just with
    a straight edge across the top. Both chibis shipped that way once. This is
    the check that stops it happening again: a new hairstyle that fails here
    wants `hair_margin` raised with it, not its crown flattened to fit.
    """
    p = CharacterParams(hairstyle=hairstyle)
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    top_units = _highest_ink(*HAIRSTYLES[hairstyle].mass(character._hair_fall(sk, p)))
    # The stroke straddles the path, so half of it paints above the curve.
    ink_y = sk.head_cy + sk.head_r * top_units - character._stroke_w(sk) / 2
    assert ink_y >= 0, (
        f"{hairstyle} at {build} paints {-ink_y:.1f}px above the canvas and is being"
        " sliced flat; raise hair_margin in build_skeleton"
    )
