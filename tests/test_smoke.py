"""Enough of a test to catch a broken package, not a substitute for looking.

Whether a shape is *right* is decided by eye against `ref/`, which no assertion
can stand in for. What these do check is that the package imports, that every
named character renders at every named build, and that the four renders in
`ref-out/` are still what the code produces, which is the thing a refactor
breaks silently.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

import pytest

from anime_character_creator import (
    BUILDS,
    HAIRSTYLES,
    PRESETS,
    CharacterParams,
    build_skeleton,
    character,  # for the two private helpers the ceiling check needs
    cover,
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
def test_the_figure_is_drawn_on_transparency(preset: str) -> None:
    """No background rectangle unless one is asked for.

    The owner's call on 2026-08-07: a character is composited onto a scene, so
    an opaque white rectangle behind it is not part of the drawing, it is
    something the caller has to undo. Checked by walking the elements rather
    than by searching the text, because `fill="white"` legitimately appears in
    the drawing: it is the sclera of every eye.
    """
    for want in (None, "white", "#ff00ff"):
        root = ET.fromstring(render_character(PRESETS[preset], background=want))
        full = [
            el
            for el in root
            if el.tag.endswith("rect") and el.get("width") == "100%" and el.get("height") == "100%"
        ]
        assert [el.get("fill") for el in full] == ([] if want is None else [want])


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

    The ear is drawn under the head, so the only part of it anyone ever sees is
    the part outside the skull. Any stretch of the contour that falls inside is
    painted over and simply is not there, and an ear that has quietly lost its
    lower half still renders a perfectly good head. Nothing enforces this, and
    the skull moves under the ear whenever the jaw taper is retuned, which is
    exactly the kind of change that would break it without looking broken in the
    arithmetic.

    It was worth checking under the old z-order too, where the ear sat on top of
    the head: there a contour inside the skull cut a line across the cheek
    instead of disappearing. Same bound, different symptom.
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


@pytest.mark.parametrize("preset", sorted(PRESETS))
def test_the_ear_is_over_the_back_hair_and_under_the_face(preset: str) -> None:
    """The canon's own arrangement: back hair behind the ear, face over it.

    A z-order is one line in a list and reads as housekeeping, so it is exactly
    the kind of thing that gets moved back without anyone noticing. This one is
    not housekeeping, and both directions are wrong in a way that still renders.
    Put the ear under the hair mass and it vanishes completely, because the mass
    is a filled shape wider than the head. Put it over the head and its rim runs
    into the face's outline and joins it, so the two read as one silhouette that
    bulges rather than as an ear behind a face; the canon draws the face's line
    unbroken and the ear behind it, which is the owner's call recorded in
    `_ears`.
    """
    p = PRESETS[preset]
    sk = build_skeleton(heads=p.heads, frame=p.frame)
    svg = render_character(p, sk)
    mass, ear, head = character._hair_mass(sk, p), character._ears(sk, p), character._head(sk, p)
    assert svg.index(mass) < svg.index(ear), (
        f"{preset}: the ear is behind the hair mass, so it is gone"
    )
    assert svg.index(ear) < svg.index(head), (
        f"{preset}: the ear is over the head, so its rim joins the face's outline"
    )


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


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_a_tucked_tunic_and_its_trousers_meet_inside_the_belt(build: str) -> None:
    """Both garments have to end under the belt band, and neither may stop short.

    A tucked tunic and the trousers below it are two shapes that have to agree
    on one line, and the belt is drawn over both, so a disagreement is invisible
    until it is big enough to show past the band: then it is either a stripe of
    canvas across the waist or a stripe of tunic below the belt, and neither
    reads as a mistake in the code that caused it. This is the check that they
    keep meeting when the belt or the waist anchor moves.
    """
    base = PRESETS["satoshi"]
    # Built here rather than read off the preset, so this tests the feature and
    # not one character's use of it: flipping Satoshi untucked should change what
    # he looks like, not turn this check into a no-op.
    p = replace(base, outfit=replace(base.outfit, tunic_tucked=True))
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    belt_y, belt_h = character._belt_band(sk)
    svg = render_character(p, sk)

    def hem(svg_fragment: str) -> float:
        return max(float(v) for v in re.findall(r"[\d.]+ ([\d.]+)", svg_fragment))

    def top(svg_fragment: str) -> float:
        return min(float(v) for v in re.findall(r"[\d.]+ ([\d.]+)", svg_fragment))

    tunic_hem = hem(character._tunic(sk, p))
    trouser_top = top(character._legs_and_boots(sk, p))
    assert belt_y <= tunic_hem <= belt_y + belt_h, (
        f"{build}: the tucked tunic ends at {tunic_hem:.1f}, outside the belt band"
        f" {belt_y:.1f}..{belt_y + belt_h:.1f}, so the hem shows past the belt"
    )
    assert belt_y <= trouser_top <= belt_y + belt_h, (
        f"{build}: the trousers start at {trouser_top:.1f}, outside the belt band"
        f" {belt_y:.1f}..{belt_y + belt_h:.1f}, so there is bare canvas at the waist"
    )
    assert svg.index(character._legs_and_boots(sk, p)) < svg.index(character._belt(sk, p)), (
        f"{build}: the belt is under the trousers, so it cannot cover the join"
    )

    # And untucked, the two have to overlap the other way: the tunic hangs to the
    # hip and the trousers start there, so neither garment is drawn where the
    # other one is the only thing covering it.
    loose = replace(base, outfit=replace(base.outfit, tunic_tucked=False))
    # Both slack tolerances are the one decimal place the SVG is written to.
    assert hem(character._tunic(sk, loose)) == pytest.approx(sk.hip_y, abs=0.05)
    assert top(character._legs_and_boots(sk, loose)) == pytest.approx(sk.hip_y, abs=0.05)


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


def test_ref_out_cover_matches_the_code() -> None:
    """The cover is checked in like the characters, so it goes stale like them.

    Worse, in fact: a character moves only when its own shapes change, but the
    cover embeds one, so *any* shape edit moves the cover too. It is the file
    most likely to be left behind by a change that looks unrelated to it.
    """
    committed = REF_OUT / "cover.svg"
    assert committed.read_text() == cover.render_cover(), (
        "ref-out/cover.svg is stale: ./refresh-ref-out.sh"
    )


def test_the_byline_is_not_the_subtitle() -> None:
    """Two fields, two places, and the bottom one is the author.

    They were one field to start with, rendering at the foot of the page, which
    is how a first draft ended up looking as though the protagonist had written
    the book. Keeping them distinct is the fix, so this pins that a subtitle
    never lands in the byline's position.
    """
    p = cover.CoverParams(subtitle="BOOK ONE", author="rhedak")
    svg = cover.render_cover(p)
    ys = {
        el.text: float(el.get("y"))
        for el in ET.fromstring(svg)
        if el.tag.endswith("text") and el.text in ("BOOK ONE", "rhedak", p.title[-1])
    }
    assert ys[p.title[-1]] < ys["BOOK ONE"] < ys["rhedak"]
    assert ys["rhedak"] > p.height * 0.9, "the byline should sit at the foot of the page"
    assert ys["BOOK ONE"] < p.height * 0.5, "a subtitle belongs under the title, not at the foot"


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_the_cover_renders_and_stays_deterministic(build: str) -> None:
    """Same params, same bytes, the same contract `render_character` holds.

    The mist banks are the reason this is worth pinning: their skyline comes
    from a jitter function keyed on an index rather than an RNG, precisely so a
    cover can be compared rather than eyeballed. An RNG would pass every other
    check here and fail only this one.
    """
    p = cover.CoverParams(build=build, subtitle="BOOK ONE")
    svg = cover.render_cover(p)
    assert svg == cover.render_cover(p)
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    for line in p.title:
        assert line in svg


def test_the_cover_stays_flat() -> None:
    """No gradient, no blur, no opacity on the page furniture.

    `CLAUDE.md`'s flat-colour rule is about the figure, but the whole point of
    drawing mist as stacked hard-edged banks is that the background obeys it
    too. The easy regression is reaching for a gradient the first time a tone
    ladder looks stepped, which is the one thing that would make this stop
    matching the character it wraps.
    """
    svg = cover.render_cover(cover.CoverParams(subtitle="BOOK ONE"))
    page = svg[: svg.index("<g transform=")]
    for banned in ("Gradient", "gradient", "filter", "blur", "opacity"):
        assert banned not in page, f"the cover's own layers should not use {banned}"


def test_the_figure_stands_on_the_page() -> None:
    """The figure is inside the trim, and the mist in front is placed off it.

    A cover is composed by fractions, so the failure mode is a figure that
    renders perfectly and lands half off the page, or a mist bank keyed to the
    canvas edge rather than to the soles: the first attempt keyed it to the
    canvas and cut him across the shins, hiding the boots.
    """
    p = cover.CoverParams(subtitle="BOOK ONE")
    sk, _character, k, x, y = cover._placement(p)
    assert x > 0 and x + sk.canvas_w * k < p.width
    assert y > 0, "the figure's head runs off the top of the page"
    assert y + sk.foot_y * k == pytest.approx(p.height * p.figure_feet_y)
    assert y + sk.foot_y * k < p.height, "the soles land below the trim"
