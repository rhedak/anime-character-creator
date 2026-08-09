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
    DISPLAY_NAMES,
    EXPRESSIONS,
    HAIRSTYLES,
    PRESETS,
    REALISTIC_REFS,
    ROSTERS,
    CharacterParams,
    build_skeleton,
    character,  # for the two private helpers the ceiling check needs
    cover,
    render_character,
    sheet,
)

REF_OUT = Path(__file__).resolve().parent.parent / "ref-out"
# Where each build's renders live under ref-out/, matching `prefix_for` in
# refresh-ref-out.sh. The chibi is the published build and sits at the top level.
PREFIX = {"chibi": "", "realistic": "real/"}


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


def _published() -> list[tuple[str, str, str]]:
    """Every (preset, build, path) `ref-out/` is supposed to hold, minus the cover.

    The chibi is published for every character; the realistic build only for
    `REALISTIC_REFS`, and under `real/`. Derived here rather than listed so the
    tests and `refresh-ref-out.sh` cannot disagree about what should exist: they
    read the same two names out of the package.
    """
    out = []
    for preset in sorted(PRESETS):
        for build in sorted(BUILDS):
            if build != "chibi" and preset not in REALISTIC_REFS:
                continue
            out.append((preset, build, f"{PREFIX[build]}{preset}"))
    return out


@pytest.mark.parametrize(("preset", "build", "rel"), _published())
def test_ref_out_matches_the_code(preset: str, build: str, rel: str) -> None:
    """The same check `./refresh-ref-out.sh --check` makes, minus the PNGs.

    `ref-out/` is committed and the README displays it, so it is stale the
    moment a shape changes without it. If this fails after a deliberate shape
    change, the fix is to run the script, not to edit the expectation.
    """
    p = PRESETS[preset]
    committed = REF_OUT / f"{rel}.svg"
    expected = render_character(p, build_skeleton(heads=BUILDS[build], frame=p.frame))
    assert committed.read_text() == expected, f"{rel}.svg is stale: ./refresh-ref-out.sh"


def test_the_deferred_builds_left_nothing_behind() -> None:
    """No `*_real` files at the old top-level paths.

    The realistic renders moved under `real/` on 2026-08-08 when they were
    deferred. A leftover at the old path is the worst kind of stale: nothing
    renders to it any more, so no comparison ever looks at it again, and it sits
    in the repository looking like current art forever. The script reports these
    rather than deleting them, since `ref-out/` is committed.
    """
    left = sorted(p.name for p in REF_OUT.rglob("*_real.*"))
    assert not left, f"realistic renders live in ref-out/real/ now; git rm {left}"


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


@pytest.mark.parametrize("name", sorted(EXPRESSIONS))
@pytest.mark.parametrize("preset", sorted(PRESETS))
def test_an_expression_changes_the_mood_and_nothing_else(name: str, preset: str) -> None:
    """The one property that makes a named mood reusable across characters.

    An expression is a delta, not a `FaceStyle`. If it ever became a whole face,
    every character wearing it would silently inherit the *stock* aperture and
    stop looking like themselves, while still rendering perfectly well and
    wearing the right mood, which is precisely the kind of break nobody spots in
    a diff. So: the fields a mood is allowed to move may move, and every field
    that says who the face is must come through untouched.
    """
    identity = ("eye_size", "eye_width", "eye_corner", "eye_tilt", "iris_size", "scar_side")
    before = PRESETS[preset]
    after = EXPRESSIONS[name].applied_to(before)
    for f in identity:
        assert getattr(after.face, f) == getattr(before.face, f), (
            f"{name} altered {f}, which is who the face is rather than what it is doing"
        )
    assert after.hairstyle == before.hairstyle and after.outfit == before.outfit
    moved = [
        f
        for f in (
            "brow_tilt",
            "brow_weight",
            "eye_openness",
            "eye_lower_lid",
            "mouth_curve",
            "mouth_width",
        )
        if getattr(after.face, f) != getattr(before.face, f)
    ]
    assert moved, f"{name} on {preset} changes nothing at all"
    ET.fromstring(render_character(after))


@pytest.mark.parametrize("preset", sorted(PRESETS))
def test_the_readme_shows_every_character(preset: str) -> None:
    """The README's table has to keep up with `PRESETS`, and nothing made it.

    `./refresh-ref-out.sh` writes a character's files the moment it is added to
    `PRESETS`, because it reads the package. The README's table is hand-written,
    so a new character arrives on disk automatically and in the table only if
    somebody remembers, which is the same silent staleness `--check` exists to
    catch one directory over. Ten more characters are planned, so this stops
    being a small gap quickly.

    Chibi only, which is the point of the deferral: the realistic renders are on
    disk under `real/` and deliberately not displayed. Checked as a link to
    `on-white/`, since that is what the table is allowed to use: the transparent
    renders lose their outline against a dark theme.
    """
    readme = (Path(__file__).resolve().parent.parent / "README.md").read_text()
    want = f"ref-out/on-white/{preset}.png"
    assert want in readme, f"{preset} renders but the README never shows it: add a row"
    assert f"ref-out/on-white/{preset}_real.png" not in readme, (
        f"{preset}: the README points at an on-white realistic copy, which is not written any more"
    )


@pytest.mark.parametrize(("before", "after"), [("kyoko", "satoko"), ("tomohiro", "satoshi")])
def test_the_disguise_changes_only_the_disguise(before: str, after: str) -> None:
    """One person, two presentations, and the same face underneath both.

    Kyoko and Satoko are the same woman before and after; so are Tomohiro and
    Satoshi. Their book calls the resemblance the single most important design
    in it, and the references it was drawn from lost it: measured inside the
    iris, `ref/satoshi.png` and `ref/satoko.png` are jade-green while
    `ref/tomohiro.png` and `ref/kyoko.png` are grey, which is drift landing on
    the one feature the disguise is documented as not touching.

    Here it cannot drift, because the pair is `replace()` on one preset rather
    than a second set of numbers, and this pins that. The failure it guards
    against is not a crash: it is somebody tuning an eye on one of the four and
    leaving the other three behind, which renders perfectly and quietly breaks
    the reveal the story is built on.
    """
    was, now = PRESETS[before], PRESETS[after]
    assert was.eye_color == now.eye_color, "the eyes are what the disguise does not touch"
    assert was.face == replace(now.face, scar_side=0), (
        "one face, minus a burn that has not happened"
    )
    assert was.frame == now.frame and was.heads == now.heads
    # Not the outfit, and not the hairstyle. A companion test used to pin both as
    # "not dressed yet" while the pair still wore their originals' clothes, and
    # it was deleted the day they were dressed, which is what it existed to
    # flag. Neither belongs here: the wardrobe is the one thing that genuinely
    # differs between the two lives, and the cut is free to change for reasons
    # that have nothing to do with the disguise.
    # And the disguise itself is present rather than merely absent from the diff.
    assert now.face.scar_side != 0 and was.face.scar_side == 0
    assert was.hair_color != now.hair_color and was.hair_tip_color is None


def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


@pytest.mark.parametrize("preset", sorted(PRESETS))
def test_an_outer_layer_is_visible_against_what_it_covers(preset: str) -> None:
    """A coat or a robe needs a tone gap, or the garment is drawn and invisible.

    Both garments are built entirely around a boundary: the coat is two panels
    with the body showing between them, and the robe is a panel with a diagonal
    edge. Neither states its own silhouette, so both vanish completely when the
    layer under them is the same tone, and they vanish *while rendering
    perfectly*, which is why nothing caught it.

    Measured on 2026-08-09 across the six characters who wear one: Keiko at a gap
    of 174 read instantly, Tomohiro at 19 and Reika at 14 read fine, Kyoko at 5
    and Haruto at 8 were invisible, and Daizen's robe was byte-identical to his
    tunic, so only the fold line was doing any work at all. 12 sits under the two
    that read and above the three that did not.
    """
    outfit = PRESETS[preset].outfit
    for field in ("coat_color", "robe_color"):
        outer = getattr(outfit, field)
        if outer is None:
            continue
        gap = abs(_luminance(outer) - _luminance(outfit.tunic_color))
        assert gap >= 12.0, (
            f"{preset}: {field} {outer} against tunic {outfit.tunic_color} is a gap of"
            f" {gap:.1f}; the garment is drawn but nothing shows"
        )


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_the_topknot_is_visible_and_still_fits(build: str) -> None:
    """A knot has to clear the cut under it and stay inside the canvas margin.

    Both halves have bitten. Drawn at -1.02 head radii it was a same-coloured
    ellipse buried in same-coloured hair and drew nothing; the shipped cuts top
    out around -1.25 to -1.28, so it has to sit above that. And the hair margin
    `build_skeleton` leaves puts the ceiling at -1.36, so there is well under a
    tenth of a radius to land in. Nothing else checks a part that is not a
    `Hairstyle`, and the failure at either end is silent: too low is invisible,
    too high is sliced flat against the canvas edge.
    """
    p = replace(PRESETS["haruto"], heads=BUILDS[build])
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    svg = character._hair_knot(sk, p)
    cy_k = float(re.search(r'cy="([-\d.]+)"', svg).group(1))
    ry = float(re.search(r'ry="([-\d.]+)"', svg).group(1))
    ink_top = (cy_k - ry - character._stroke_w(sk) / 2 - sk.head_cy) / sk.head_r
    assert ink_top > -1.36, f"the knot paints to {ink_top:.3f} head radii, past the canvas margin"
    mass_top = min(
        (float(v) - sk.head_cy) / sk.head_r
        for v in re.findall(r"[-\d.]+", character._hair_mass(sk, p).split('d="')[1].split('"')[0])[
            1::2
        ]
    )
    knot_top = (cy_k - ry - sk.head_cy) / sk.head_r
    assert knot_top < mass_top, (
        f"the knot's crown is at {knot_top:.3f} and the cut's at {mass_top:.3f}, so it is buried"
    )


@pytest.mark.parametrize("build", ["chibi", "realistic"])
def test_the_sideburn_rides_the_jaw_rather_than_chording_it(build: str) -> None:
    """The strip's outer edge holds its distance from the skull all the way down.

    The edge used to be a single quadratic from the top of the strip to the
    bottom, and a quadratic can be told where to bulge but not made to agree
    with a curve: its middle fell to 0.78 of the skull's half width while both
    of its ends sat above 0.87, so what got drawn was a straight diagonal and
    the strip between the two edges was a triangle. The owner's report was that
    it should track the face, and this is that read as a number.

    Measured as sag away from the edge's *own* two ends rather than as absolute
    distance from the skull, which is the difference between testing the shape
    and testing `_BEARD_SIDE_INSET`. That constant is a judgement about how much
    cheek to leave and has moved twice; a chord fails this at any value of it.

    Off the drawn path rather than off `_face_track`, since the bug being
    guarded lives in how the points are joined up, not in where they are. Both
    builds, because the jaw taper only exists at the tall end and an edge that
    ignores the contour goes wrong there first.

    The *inner* edge is deliberately not held to this. It carries the width
    easing, so it bows away from its own two ends by about a tenth of a head
    radius on purpose; what has to hold there is the taper, which is the next
    test.
    """
    p = PRESETS["reinhard"]
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    d = re.search(r'd="([^"]+)"', character._beard(sk, p)).group(1)
    # The path opens at the top of the left strip and runs down it, so the strip
    # is its leading run, taken until the height where the mass takes over. Bound
    # by height rather than by counting points or by splitting on the first curve:
    # both of those have already been made wrong once by a change elsewhere in the
    # path, the second when the bottom stopped being drawn as quadratics.
    nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", d.split("Q")[0])]
    pts = []
    for px, py in zip(nums[0::2], nums[1::2], strict=True):
        if (py - sk.head_cy) / sk.head_r > character._BEARD_TOP + 0.01:
            break
        pts.append((px, py))
    # This is the assert the old geometry trips: a chord has nothing between its
    # two ends, so there is no sag to measure and the sag check never runs.
    assert len(pts) > 4, (
        f"the outer edge is {len(pts)} point(s) between the top of the strip and the mass, "
        f"which is a chord across the cheek rather than a line following it"
    )
    shares = [
        (
            (sk.head_cx - px)
            / sk.head_r
            / character._head_edge_x((py - sk.head_cy) / sk.head_r, sk.build),
            (py - sk.head_cy) / sk.head_r,
        )
        for px, py in pts
    ]
    (top_share, top_y), (bot_share, bot_y) = shares[0], shares[-1]
    for share, y in shares:
        f = (y - top_y) / (bot_y - top_y)
        held = top_share + (bot_share - top_share) * f
        assert abs(share - held) < 0.02, (
            f"at {y:.2f} head radii the strip's edge is {share:.2f} of the way out to the "
            f"skull's where its own ends put it at {held:.2f}, so it is cutting across the "
            f"cheek instead of following it"
        )


@pytest.mark.parametrize("build", ["chibi", "realistic"])
def test_the_sideburn_never_narrows_on_its_way_down(build: str) -> None:
    """The strip covers more of the cheek at every step toward the jaw.

    This is the original defect stated as an invariant. The strip used to be
    0.31 head radii wide beside the eye and 0.06 at the jaw, and two edges that
    converge make a triangle, so it read as a cut-out rather than as hair. A
    reference beard runs the other way: thin in front of the ear, spreading
    where it meets the mass.

    Measured as how far the inner edge sits inside the skull's own edge, which
    is what the width looks like once it is drawn on a face that is itself
    narrowing. That makes it a check on the contour's taper and the ratio and
    the width together, not a restatement of the three constants: the realistic
    build's jaw pulls in fast enough to eat a width that only just grows.

    Computed rather than parsed, unlike its neighbour. The inner edge's points
    are buried mid-path between the chin's curves and the top edge's dive, and
    what is being asserted here is where they are, which is exactly the half a
    parse would add nothing to.
    """
    sk = build_skeleton(heads=BUILDS[build], frame=PRESETS["reinhard"].frame)
    corner = character._face_track(
        character._BEARD_SIDEBURN_Y,
        character._BEARD_TOP,
        sk.build,
        character._BEARD_SIDEBURN_OUT,
        character._BEARD_SIDE_INSET,
    )[-1]
    jaw = character._jaw_track(
        character._BEARD_TOP,
        sk.build,
        PRESETS["reinhard"].beard_length,
        character._BEARD_SIDE_INSET,
    )[0]
    assert math.dist(corner, jaw) < 1e-9, (
        f"the strip ends at {corner} and the jaw starts at {jaw}, so the outline kinks where "
        f"they meet, by an amount that moves with the build"
    )
    inner = character._face_track(
        character._BEARD_SIDEBURN_Y,
        character._BEARD_TOP + 0.14,
        sk.build,
        character._BEARD_SIDEBURN_OUT,
        character._BEARD_SIDE_INSET,
        character._BEARD_SIDEBURN_W_TOP,
        character._BEARD_SIDEBURN_W_BOT,
        character._BEARD_SIDEBURN_W_EASE,
    )
    covered = [character._head_edge_x(y, sk.build) - x for x, y in inner]
    assert covered[-1] > covered[0], (
        f"the strip covers {covered[0]:.3f} head radii of cheek at the top and "
        f"{covered[-1]:.3f} at the jaw, so it converges to a point and reads as a wedge"
    )
    for (x, y), here, nxt in zip(inner, covered, covered[1:], strict=False):
        assert nxt >= here - 1e-9, (
            f"at {y:.2f} head radii the strip pinches from {here:.3f} to {nxt:.3f}"
            f" (inner edge at {x:.3f})"
        )


@pytest.mark.parametrize("preset", ["reinhard", "daizen"])
def test_the_beard_reaches_over_the_mouth_and_the_mouth_survives_it(preset: str) -> None:
    """A moustache, and a mouth still drawn on top of it.

    Two halves of one change, and each is silent without the other. The beard
    used to top out at about 0.895 head radii in the middle with the chin at
    1.0, so it covered the last tenth of the chin and hung below, leaving bare
    skin from the lip to the jaw: a shaved face on an unshaved neck, which is
    the owner's report on 2026-08-09. Raising it fixes that and immediately
    deletes the mouth, because the beard was drawn over the face.

    So the beard has to reach above `_MOUTH_Y` somewhere near the centre, and
    the face has to be drawn after the beard. Neither shows up as an error: a
    beard that stops short still renders, and a swallowed mouth still renders.

    The centre band is read off every number in the path, controls included,
    which is looser than tracing the curve and enough here: the old shape's
    only central point was the control that dived to 1.02, well the wrong side
    of the mouth, so nothing about it could pass this by accident.

    The order check is exactly that, an order check. It says these two blocks
    are stacked the right way round, not that the mouth is visible: it would
    still pass if the mouth left `_face` for a layer of its own, or if a later
    part grew something over the lip. Both would have to be seen, not asserted.
    """
    p = PRESETS[preset]
    sk = build_skeleton(heads=p.heads, frame=p.frame)
    beard = character._beard(sk, p)
    d = re.search(r'd="([^"]+)"', beard).group(1)
    nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", d)]
    pts = list(zip(nums[0::2], nums[1::2], strict=True))
    middle = [
        (py - sk.head_cy) / sk.head_r for px, py in pts if abs(px - sk.head_cx) < sk.head_r * 0.15
    ]
    assert middle, "the beard has no point near the centre line at all"
    assert min(middle) < character._MOUTH_Y, (
        f"the beard's highest point near the centre is {min(middle):.2f} head radii and the "
        f"mouth is at {character._MOUTH_Y}, so it stops below the lip and reads as a neckbeard"
    )
    svg = render_character(p, sk)
    assert svg.index(beard) < svg.index(character._face(sk, p)), (
        "the beard is drawn over the face, so the moustache paints out the mouth"
    )


@pytest.mark.parametrize("preset", ["reinhard", "daizen"])
@pytest.mark.parametrize("build", ["chibi", "realistic"])
def test_the_moustache_is_thicker_than_the_line_that_draws_it(preset: str, build: str) -> None:
    """There has to be more hair above the lip than there is ink round it.

    The moustache is not a number anybody sets. It is what is left between the
    top edge's lobe and the top of the lip lozenge, and those are set by two
    constants that know nothing about each other, so either can close the gap
    without looking like it did anything. That is not hypothetical: shipped at
    a lobe of 0.46 it came to 0.037 head radii, which on an 88 pixel head is 3.3
    pixels of hair inside a 4 pixel outline, and the owner's report was that the
    moustache read as a single black line. It was, almost exactly.

    Stated against the stroke rather than as a fixed distance, because that is
    the actual claim and it is the one that survives a change of scale: a band
    thinner than its own outline is not a band. Twice the stroke is the floor;
    what ships is about three times it.

    There is an upper end too and it is not far away, but it is a judgement
    rather than a threshold, so it is recorded and not asserted: at a lobe of
    0.31 the shape climbs toward the nose and reads as a snout.
    """
    p = PRESETS[preset]
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    lip_top = character._MOUTH_Y - character._BEARD_LIP_H * 0.12 * p.face.mouth_width
    band = (lip_top - character._BEARD_TASH_Y) * sk.head_r
    stroke = character._stroke_w(sk)
    assert band >= stroke * 2, (
        f"{preset} at the {build} build has {band:.1f}px of moustache between the lobe and the "
        f"lip, against a {stroke:.1f}px outline, so it reads as a line above the mouth"
    )


@pytest.mark.parametrize("hairstyle", sorted(HAIRSTYLES))
@pytest.mark.parametrize("build", sorted(BUILDS))
def test_the_cap_covers_the_hair_it_is_tied_over(hairstyle: str, build: str) -> None:
    """The cloth has to be at least as wide as the cut under it.

    Sized against the skull it is a fifth of a head radius too narrow on a long
    cut, so the hair stands outside the cloth tied over it, the two outlines
    cross, and what it reads as is a shape painted on the hair rather than
    something put on. That is the owner's report on 2026-08-09 and it is the
    third part to make the same mistake: the tail and the knot were both sized
    against the bone while sitting on the hair.

    Every cut, not just the one wearer's, because a scarf is a garment and the
    whole point of it being one is that anyone can put it on. Both builds,
    because the hair and the skull do not change width together: `short_crop`
    goes 1.28 to 1.00 across the range while the skull barely moves.

    Read off the drawn arc rather than off the constant, so it fails if the
    width goes back to being taken from `_head_edge_x`, which is the specific
    regression worth catching.
    """
    p = replace(PRESETS["chiyo"], hairstyle=hairstyle)
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    d = re.search(r'd="([^"]+)"', character._headscarf(sk, p)).group(1)
    rx = float(re.search(r"A ([\d.]+) ", d).group(1)) / sk.head_r
    hair = character._hair_edge_x(character._SCARF_EDGE_Y, sk, p)
    assert rx >= hair, (
        f"the cap is {rx:.3f} head radii wide over {hairstyle} hair that is {hair:.3f} wide, "
        f"so the cut stands outside the cloth tied over it"
    )
    # And still on the canvas. The dome now grows with the hair, so a longer or
    # fuller cut moves it, and the failure at that end is a flat-sided cap.
    assert sk.head_cx + rx * sk.head_r <= 400, f"the cap runs off the canvas at {rx:.3f}"


@pytest.mark.parametrize("build", sorted(BUILDS))
@pytest.mark.parametrize(
    "face",
    [
        replace(PRESETS["keiko"].face, glasses=True),
        replace(
            PRESETS["keiko"].face, glasses=True, eye_width=1.3, eye_size=0.75, eye_openness=0.7
        ),
        replace(PRESETS["keiko"].face, glasses=True, eye_lower_lid=1.4, eye_openness=0.6),
    ],
    ids=["default", "wide-small", "asymmetric-lids"],
)
def test_the_glasses_frame_the_eye_rather_than_a_second_guess_at_it(face, build: str) -> None:
    """Every rim actually contains the aperture it is drawn over.

    `_glasses` used to carry its own copy of `_eye_placement`'s numbers, at
    different values: `eye_dx` 0.34 against the real 0.46, `eye_y` at `+0.10`
    against the real `+0.16`, a half width built from `eye_width` alone with
    neither `eye_r` nor `_EYE_ASPECT`, a half height built from `eye_size`
    where the aperture itself reads `eye_openness` and `eye_lower_lid`. None of
    that showed up as an error, since a rim in roughly the right place still
    renders; it showed up as the eye sitting outside its own glasses, which is
    the owner's report on 2026-08-09.

    Checked against the aperture's own corners rather than against
    `_eye_placement`'s numbers a second time, which would only prove the two
    functions still agree with each other and not that either agrees with what
    is drawn. Three faces because the old code happened to roughly fit one
    default aperture at one build; asymmetric lids is the case that a single
    symmetric `rh` could never have held regardless of its value.
    """
    p = replace(PRESETS["keiko"], face=face)
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    svg = character._glasses(sk, p)
    rects = re.findall(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)"', svg)
    assert len(rects) == 2, f"expected two rims, found {len(rects)}"
    eye_dx, eye_y, eye_r, f = character._eye_placement(sk, p)
    for side, (x, y, w, h) in zip((-1, 1), rects, strict=True):
        rim_left, rim_top = float(x), float(y)
        rim_right, rim_bot = rim_left + float(w), rim_top + float(h)
        ex = sk.head_cx + side * eye_dx
        half_w = eye_r * f.eye_width * character._EYE_ASPECT
        top_h = eye_r * f.eye_openness
        bot_h = eye_r * f.eye_lower_lid
        assert rim_left <= ex - half_w and rim_right >= ex + half_w, (
            f"{build} side {side}: aperture spans {ex - half_w:.1f}-{ex + half_w:.1f} but the "
            f"rim only spans {rim_left:.1f}-{rim_right:.1f}"
        )
        assert rim_top <= eye_y - top_h and rim_bot >= eye_y + bot_h, (
            f"{build} side {side}: aperture spans {eye_y - top_h:.1f}-{eye_y + bot_h:.1f} but the "
            f"rim only spans {rim_top:.1f}-{rim_bot:.1f}"
        )


@pytest.mark.parametrize("preset", ["keiko", "kyoko", "tomohiro"])
@pytest.mark.parametrize("build", sorted(BUILDS))
def test_the_coats_lapel_actually_reaches_the_neck(preset: str, build: str) -> None:
    """Each panel's top corner sits close beside the neck, not out at the shoulder.

    The panel's top used to run in one line straight from the throat point to the
    shoulder point, and that line never comes near the neck: both of its ends sit
    at or below the shoulder line, so the whole strip of shoulder next to the neck
    was bare on both sides. It rendered as two separate wedges resting on the
    chest, which is the owner's report on 2026-08-09.

    Checked as two things a coat and a floating wedge disagree on: the topmost
    point of the panel has to rise above the shoulder line by a real margin, not
    sit on it, and that point has to be close to the neck's own width rather than
    out near the shoulder's, since a peak that rises but does so out at the
    shoulder is a raised epaulette, not a lapel.
    """
    p = PRESETS[preset]
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    d = re.search(r'd="([^"]+)"', character._coat(sk, p)).group(1)
    nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", d.split("Z")[0])]
    pts = list(zip(nums[0::2], nums[1::2], strict=True))
    top_x, top_y = min(pts, key=lambda pt: pt[1])
    assert top_y < sk.shoulder_y - sk.neck_half_w, (
        f"{preset} {build}: the panel's highest point is {sk.shoulder_y - top_y:.1f}px above the "
        f"shoulder line, which is not a lapel rising to the neck"
    )
    assert abs(top_x - sk.head_cx) < sk.neck_half_w * 2.2, (
        f"{preset} {build}: the panel's peak sits {abs(top_x - sk.head_cx):.1f}px from centre, "
        f"which is out near the shoulder rather than beside the neck"
    )


@pytest.mark.parametrize("preset", ["haruto", "reika"])
@pytest.mark.parametrize("build", sorted(BUILDS))
def test_the_hakama_is_pleated_not_a_plain_panel(preset: str, build: str) -> None:
    """A comb of lines runs the full height of the panel, not just its hem.

    `_skirt` draws two folds; a hakama is defined by having many, which is what
    a plain A-line panel would be missing if `_hakama` had only reused
    `_skirt_path` and stopped there. Counted rather than eyeballed, since seven
    thin lines and two thin lines both render as "some lines" in a diff and the
    difference only shows up as a count.
    """
    p = PRESETS[preset]
    sk = build_skeleton(heads=BUILDS[build], frame=p.frame)
    svg = character._hakama(sk, p)
    lines = re.findall(r"<line ", svg)
    assert len(lines) == 7, f"{preset} {build}: {len(lines)} pleats, expected the full comb of 7"


@pytest.mark.parametrize("preset", ["haruto", "reika"])
def test_the_hakama_is_drawn_over_whatever_is_on_the_legs(preset: str) -> None:
    """The hakama's own layer comes after the legs in the stacking order.

    Haruto wears trousers under a hakama that stops short of his boots; Reika
    wears nothing under hers. Both only work if `_hakama` paints over the top
    of whatever `_legs_and_boots` already drew rather than needing to know
    which one it is, so this checks the order rather than either leg style.
    """
    p = PRESETS[preset]
    sk = build_skeleton(heads=p.heads, frame=p.frame)
    svg = render_character(p, sk)
    assert svg.index(character._legs_and_boots(sk, p)) < svg.index(character._hakama(sk, p)), (
        f"{preset}: the hakama is drawn before the legs, so the legs would paint over it"
    )


def test_the_sheet_renders_and_stays_deterministic() -> None:
    p = sheet.SheetParams()
    svg = sheet.render_sheet(p)
    assert svg == sheet.render_sheet(p)
    ET.fromstring(svg)


def test_every_roster_member_appears_once() -> None:
    """A tile per character, labelled, and nobody drawn twice or dropped.

    The failure this guards is quiet: a roster that names a character the grid
    then lays out one tile short looks like a layout choice rather than a
    missing person, which is exactly the sort of thing nobody spots on a sheet
    of fourteen.
    """
    for roster in sorted(ROSTERS):
        p = replace(sheet.SheetParams(), roster=roster)
        svg = sheet.render_sheet(p)
        members = sheet.members_of(p)
        assert len(members) == len(set(members)), f"{roster} names somebody twice"
        for preset in members:
            name = DISPLAY_NAMES[preset]
            assert svg.count(f">{name}</text>") == 1, (
                f"{roster}: {name} is not labelled exactly once"
            )


def test_every_character_has_a_display_name_and_a_roster() -> None:
    """Adding a preset has to mean adding it to the sheet, or it is invisible.

    `refresh-ref-out.sh` renders a new character's files off `PRESETS` alone, so
    without this a character can land, get committed art, and never appear on
    the one page the cast is judged on.
    """
    for preset in PRESETS:
        assert preset in DISPLAY_NAMES, f"{preset} has no display name for the sheet"
        assert any(preset in names for names in ROSTERS.values()), f"{preset} is on no roster"


def test_ref_out_sheet_matches_the_code() -> None:
    committed = REF_OUT / "sheet.svg"
    assert committed.read_text() == sheet.render_sheet(), "sheet.svg is stale: ./refresh-ref-out.sh"


def test_ref_out_sheet_satoshi_matches_the_code() -> None:
    committed = REF_OUT / "sheet_satoshi.svg"
    expected = sheet.render_sheet(replace(sheet.SheetParams(), roster="satoshi"))
    assert committed.read_text() == expected, "sheet_satoshi.svg is stale: ./refresh-ref-out.sh"


def test_the_satoshi_roster_is_satoshis_persona_not_satokos() -> None:
    """The owner's call on 2026-08-09: Satoshi leads, then alphabetical, no Satoko or Kyoko.

    This is the split `ROSTERS`'s own comment names as the two reference sheets:
    ten shared members plus Satoshi and Tomohiro on one side, Satoko and Kyoko on
    the other. `cast` carries the first; this is the second, and it is derived
    from `cast` rather than a second hand-written list so the two cannot drift
    apart the day a fifteenth character lands in one and not the other.
    """
    roster = ROSTERS["satoshi"]
    assert roster[0] == "satoshi", "Satoshi has to lead his own roster"
    assert "satoko" not in roster and "kyoko" not in roster, (
        "this is Satoshi's persona; Satoko and Kyoko belong to the other one"
    )
    assert "tomohiro" in roster, "Tomohiro is Satoshi's own before-self and stays"
    assert list(roster[1:]) == sorted(roster[1:]), "everyone after Satoshi should be alphabetical"
    # Same membership as `cast` minus the two that were swapped out, which is the
    # "share ten members" half of the split: nobody should be on one roster and
    # not the other except the two pairs that differ on purpose.
    assert set(roster) == set(ROSTERS["cast"]) - {"satoko", "kyoko"}


def test_the_sheet_scales_every_figure_the_same() -> None:
    """One body scale across the grid, so nobody reads as taller than they are.

    Each tile scales off its own skeleton, which is a fixed canvas, rather than
    off the figure's ink. Fitting to ink would quietly enlarge whoever is drawn
    smallest, and on a cast sheet a size difference reads as a height
    difference. `frame` moves the shoulders and hips, not the canvas, so every
    character comes out at one scale even though no two are the same width.
    """
    svg = sheet.render_sheet()
    scales = set(re.findall(r"scale\(([0-9.]+)\)", svg))
    assert len(scales) == 1, f"figures are at different scales: {sorted(scales)}"


def test_the_cover_wears_its_chosen_expression() -> None:
    """`hollow` is the owner's call of 2026-08-08 and is the cover's default.

    Pinned because it is a default rather than a call site: nothing else in the
    file mentions it, so it is invisible at the point the cover is rendered.
    """
    p = cover.CoverParams()
    assert p.expression == "hollow"
    sk, character, _k, _x, _y = cover._placement(p)
    assert character.face == EXPRESSIONS["hollow"].on(PRESETS["satoshi"].face)
    assert sk is not None
    # And it can be taken off, which is what `None` is for.
    _sk, plain, *_ = cover._placement(replace(p, expression=None))
    assert plain.face == PRESETS["satoshi"].face
