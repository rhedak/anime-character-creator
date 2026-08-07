"""Enough of a test to catch a broken package, not a substitute for looking.

Whether a shape is *right* is decided by eye against `ref/`, which no assertion
can stand in for. What these do check is that the package imports, that every
named character renders at every named build, and that the four renders in
`ref-out/` are still what the code produces, which is the thing a refactor
breaks silently.
"""

from __future__ import annotations

import math
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


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_the_ear_stays_welded_to_the_skull(build: str) -> None:
    """The ear's outer contour has to stay outside the skull it grows off.

    The ear is drawn over the head and closes on a straight chord between its two
    attach points, so the skin covers the length of head outline it spans and the
    silhouette reads as one contour. That only works while the contour is outside
    the skull: let any of it fall inside and the ear's stroke cuts a line across
    the cheek and the head's own outline reappears beside it. Nothing enforces
    that, and the skull moves under the ear whenever the taper is retuned, which
    is exactly the kind of change that would break this without looking broken in
    the arithmetic.
    """
    sk = build_skeleton(heads=BUILDS[build])
    start, segments = character._ear_outer(sk.build)
    prev = start
    for ctrl, end in segments:
        for i in range(1, 21):
            t = i / 21
            x = (1 - t) ** 2 * prev[0] + 2 * (1 - t) * t * ctrl[0] + t**2 * end[0]
            y = (1 - t) ** 2 * prev[1] + 2 * (1 - t) * t * ctrl[1] + t**2 * end[1]
            skull = character._head_edge_x(y, sk.build)
            assert x >= skull - 1e-9, (
                f"the {build} ear dips {skull - x:.3f} head radii inside the skull at"
                f" y={y:.3f}; it would cut a line across the cheek"
            )
        prev = end


def _walk(start: tuple[float, float], segments: list, per: int = 24) -> list:
    """A quadratic chain as a dense point list."""
    pts = [start]
    prev = start
    for ctrl, end in segments:
        for i in range(1, per + 1):
            t = i / per
            pts.append(
                (
                    (1 - t) ** 2 * prev[0] + 2 * (1 - t) * t * ctrl[0] + t**2 * end[0],
                    (1 - t) ** 2 * prev[1] + 2 * (1 - t) * t * ctrl[1] + t**2 * end[1],
                )
            )
        prev = end
    return pts


@pytest.mark.parametrize("hairstyle", sorted(HAIRSTYLES))
@pytest.mark.parametrize("build", sorted(BUILDS))
def test_the_front_hair_adds_no_silhouette(hairstyle: str, build: str) -> None:
    """The mass carries the whole outer contour, and no other piece may cross it.

    That is the first rule of the hair contract and nothing enforced it. The
    hairline's closing edge is a fill boundary, never stroked, so when it strays
    outside the mass there is no line to give it away: the hair colour simply
    paints past its own outline, which on the traced crop came out as a smooth
    gold arc sitting outside the spikes.

    A point passes if it is inside the mass **or** within a hair's breadth of its
    outline, because most of a closing edge is a deliberate exact retrace of the
    mass and lands on the boundary rather than inside it. Two cheaper tests were
    tried and both cried wolf. Comparing radii at a shared bearing fails near a
    lock's tip, where the radius moves fast enough against the bearing that two
    samplings of the same curve disagree by more than a real leak. Shrinking each
    point 1% toward the head centre fails at a tip too: the inward direction there
    is along the lock, not toward the head, so a radial nudge walks a tip point
    out through the side of its own shape.

    The mass is sampled hard, 150 points a segment, for a third reason of the same
    kind: the polygon's chords cut the corner off every curve they stand in for,
    so a coarse sampling reports a point on the outline as outside it by the
    sagitta. At 40 a segment that came to 0.015 head radii on `short_tousled`,
    which is more than the 0.04 of a real leak has any business being near.
    """
    p = CharacterParams(hairstyle=hairstyle)
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    fall = character._hair_fall(sk, p)
    style = HAIRSTYLES[hairstyle]
    poly = _walk(*style.mass(fall), per=150)
    edges = list(zip(poly, poly[1:] + poly[:1], strict=True))

    def inside(px: float, py: float) -> bool:
        hit = False
        for (ax, ay), (bx, by) in edges:
            if (ay > py) != (by > py) and px < ax + (py - ay) / (by - ay) * (bx - ax):
                hit = not hit
        return hit

    def gap(px: float, py: float) -> float:
        best = 9.9
        for (ax, ay), (bx, by) in edges:
            dx, dy = bx - ax, by - ay
            n = dx * dx + dy * dy
            t = 0.0 if n == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / n))
            best = min(best, math.hypot(px - (ax + t * dx), py - (ay + t * dy)))
        return best

    _, line, back = style.hairline(fall)
    for x, y in _walk(line[-1][1], back, per=10):
        assert inside(x, y) or gap(x, y) <= 0.006, (
            f"{hairstyle} at {build}: the hairline's closing edge reaches"
            f" ({x:.3f}, {y:.3f}), {gap(x, y):.3f} head radii outside the mass, so"
            " the fill paints past its own outline with no stroke to show it"
        )


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
