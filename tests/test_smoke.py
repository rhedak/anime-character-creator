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
    EYESTYLES,
    HAIRSTYLES,
    NEUTRAL_BASES,
    PRESETS,
    ROSTERS,
    CharacterParams,
    FaceStyle,
    build_skeleton,
    character,  # for the two private helpers the ceiling check needs
    cover,
    render_character,
    sheet,
)

REF_OUT = Path(__file__).resolve().parent.parent / "ref-out"
# Where the renders live under ref-out/, matching `prefix_for` in
# refresh-ref-out.sh: the tall chibi, the one published build, at the top level.
PREFIX = {"chibi": ""}


@pytest.mark.parametrize("preset", sorted(PRESETS))
@pytest.mark.parametrize("build", sorted(BUILDS))
def test_named_characters_render(preset: str, build: str) -> None:
    p = PRESETS[preset]
    svg = render_character(p)
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert len(list(root)) > 10, "a character is many shapes; one or two means parts dropped out"


@pytest.mark.parametrize("hairstyle", sorted(HAIRSTYLES))
def test_every_hairstyle_renders_on_a_default_character(hairstyle: str) -> None:
    svg = render_character(CharacterParams(hairstyle=hairstyle))
    ET.fromstring(svg)


@pytest.mark.parametrize("eye_style", sorted(EYESTYLES))
@pytest.mark.parametrize("build", sorted(BUILDS))
def test_every_eyestyle_renders_on_a_default_character(eye_style: str, build: str) -> None:
    p = CharacterParams(face=FaceStyle(eye_style=eye_style))
    svg = render_character(p)
    ET.fromstring(svg)


def test_realistic_eyestyle_is_every_preset_s_own_default() -> None:
    """`eye_style` defaults to "realistic" on `FaceStyle` itself, so a preset
    that never mentions it renders exactly as it did before `EYESTYLES`
    existed; this is what keeps `ref-out/` byte-identical across that
    change."""
    for name in sorted(PRESETS):
        assert PRESETS[name].face.eye_style == "realistic"


@pytest.mark.parametrize("glow", [0.0, 0.5, 1.0])
@pytest.mark.parametrize("build", sorted(BUILDS))
def test_eye_glow_extremes_render_on_the_anime_style(glow: float, build: str) -> None:
    """`eye_glow` is only read by `EYESTYLES["anime"]`; 0 turns its two
    secondary highlights off rather than erroring, per the owner's ask."""
    p = CharacterParams(face=FaceStyle(eye_style="anime", eye_glow=glow))
    svg = render_character(p)
    ET.fromstring(svg)


@pytest.mark.parametrize("base", sorted(NEUTRAL_BASES))
def test_neutral_bases_render_and_stay_out_of_the_cast(base: str) -> None:
    """The web tool's starting points, per `docs/web-gui-plan.md`.

    They render like any preset, but they are not presets: `PRESETS` is the
    fourteen named characters the README and `ref-out/` publish, and a base has
    no design to publish there.
    """
    svg = render_character(NEUTRAL_BASES[base])
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert base not in PRESETS


@pytest.mark.parametrize("base", sorted(NEUTRAL_BASES))
def test_ref_out_bases_match_the_code(base: str) -> None:
    """`ref-out/bases/<id>.svg` is the web gallery's instant-paint art for the
    two neutral bases, committed the way ref-out/'s own SVGs are. Guarded the
    same way `refresh-ref-out.sh --check` guards those; run
    `./refresh-bases.sh` when this fails."""
    committed = (REF_OUT / "bases" / f"{base}.svg").read_text()
    assert committed == render_character(NEUTRAL_BASES[base]), (
        f"ref-out/bases/{base}.svg is stale; run ./refresh-bases.sh"
    )


def test_render_is_deterministic() -> None:
    """`ref-out/` is compared byte for byte, so two runs have to agree."""
    p = PRESETS["satoko"]
    assert render_character(p) == render_character(p)


def test_arm_out_default_leaves_the_render_unchanged() -> None:
    """`right_arm_out`/`left_arm_out` default to 0, both hanging as before.

    `render_character(CharacterParams())` and one that sets both fields to
    0.0 explicitly hold the same dataclass value, so byte-identical output is
    the trivial half of this; the check worth having is that a character
    which never touches the knob never emits the new markup at all.
    `_arms` only opens a `<g transform="rotate(...)">` and draws the joint
    cap when a swing is non-zero, so their absence here is what "the default
    leaves every existing render byte-identical" actually rests on, checked
    on a preset with long sleeves and a coat (satoko has neither), where the
    cap and the tube it would need to hide are both in play if the
    zero-guard were missing.
    """
    assert render_character(CharacterParams()) == render_character(
        replace(CharacterParams(), right_arm_out=0.0, left_arm_out=0.0)
    )
    base = replace(PRESETS["katherina"], right_arm_out=0.0, left_arm_out=0.0)
    sk = build_skeleton(heads=BUILDS["chibi"], frame=base.frame)
    assert 'transform="rotate(' not in render_character(base, sk)
    assert 'transform="rotate(' in render_character(replace(base, right_arm_out=30.0), sk)


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_arm_out_swings_the_hand_away_from_the_body(build: str) -> None:
    """A non-zero swing has to actually move the hand, not just add a cap.

    Coarse but robust: `right_arm_out` swings the character's own right arm,
    the viewer's *left*, further from the centreline (further left, i.e. a
    smaller/more negative x) and up (a smaller y) at the same time, per
    `CharacterParams.right_arm_out`'s own docstring. Reads every numeric x/y
    pair out of every path's `d` attribute rather than parsing the curves
    properly, since the exact shape is a look-and-judge call
    (`docs/gap-analysis.md`'s territory), not something a coordinate
    assertion should be pinning down.
    """
    sk = build_skeleton(heads=BUILDS[build])
    straight = render_character(CharacterParams(), sk)
    swung = render_character(CharacterParams(right_arm_out=40.0), sk)

    def min_x_max_y(svg: str) -> tuple[float, float]:
        nums = re.findall(r"(-?\d+\.\d+) (-?\d+\.\d+)", svg)
        xs = [float(x) for x, _ in nums]
        ys = [float(y) for _, y in nums]
        return min(xs), max(ys)

    straight_min_x, _ = min_x_max_y(straight)
    swung_min_x, _ = min_x_max_y(swung)
    assert swung_min_x < straight_min_x, (
        "a 40 degree right_arm_out should push some point further left than "
        "the arm ever reaches hanging straight"
    )


def test_garment_placement_is_the_identity_on_the_traced_body() -> None:
    """A traced cut lands where it was traced on the body it was traced off.

    And on the shared chibi it keeps landmark to landmark: the reference's
    waist goes to the chibi's waist, its hem to the chibi's hem, and widths
    scale with the body's own half-width there.
    """
    ref = character.skeleton_for(CharacterParams(body=character._GARMENT_REF_BODY))
    xf = character._garment_placement(ref)
    ys, ws = character._body_knots(ref)
    for y, w in zip(ys, ws, strict=True):
        for pt in ((0.0, y), (w, y), (-0.5 * w, y + 0.01), (0.3, 0.4)):
            mx, my = xf(pt)
            assert abs(mx - pt[0]) < 1e-9 and abs(my - pt[1]) < 1e-9
    chibi = build_skeleton(heads=BUILDS["chibi"])
    to_chibi = character._garment_placement(chibi)
    cys, cws = character._body_knots(chibi)
    for y, w, cy, cw in zip(ys, ws, cys, cws, strict=True):
        mx, my = to_chibi((w, y))
        assert abs(my - cy) < 1e-9 and abs(mx - cw) < 1e-9


def test_a_traced_cut_draws_at_the_chibi_build() -> None:
    """Cuts replace the shared garment only where they were traced to fit."""
    p = PRESETS["katherina"]
    banded = replace(p, outfit=replace(p.outfit, collar_cut=None))
    sk = character.skeleton_for(p)
    assert render_character(p, sk) != render_character(banded, sk)


def test_a_body_profile_applies_at_the_chibi_build() -> None:
    """A measured body replaces the chibi's lerped landmarks and nothing else.

    The figure takes the profile's height and landmarks while `build` stays
    the chibi's own, so the face is unchanged.
    """
    p = PRESETS["katherina"]
    profile = character.BODY_TYPES[p.body]
    sk = character.skeleton_for(p)
    plain = build_skeleton(heads=BUILDS["chibi"], frame=p.frame)
    assert sk.build == plain.build
    assert abs((sk.waist_y - sk.head_cy) / sk.head_r - profile.waist_y) < 1e-9
    assert abs((sk.foot_y - sk.head_cy) / sk.head_r - (2 * profile.heads - 1)) < 1e-6


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_staff_stays_in_hand_and_on_the_canvas(build: str) -> None:
    """The staff is placed off the hand and nudged inward off the canvas edge.

    Two things can silently go wrong. Its ornament reaches out past the hand,
    and a hat's headroom narrows the canvas in head radii, which at chibi put
    the outer prong on the edge the first time. And the grip has to land on the
    hand holding it at every build, or the staff floats beside the figure.
    Checks the placed wood's control polygon, which bounds the drawn curve.
    """
    p = PRESETS["katherina"]
    sk = character.skeleton_for(p)
    xf = character._staff_placement(sk, p)
    start, segs = character._STAFF_WOOD
    pts = [xf(q) for q in (start, *(q for seg in segs for q in seg))]
    half = sk.canvas_w / 2 / sk.head_r
    assert min(x for x, _ in pts) >= -half, "the staff runs off the canvas's left edge"
    hx, hy = character._hand_centre(sk, p, -1)
    gx, gy = xf(character._STAFF_GRIP)
    assert abs(gx - hx) < 0.15 and abs(gy - hy) < 1e-9, "the grip is not in the hand"
    foot = (sk.foot_y - sk.head_cy) / sk.head_r
    assert abs(max(y for _, y in pts) - foot) < 0.05, "the staff's foot is off the ground"
    assert "staff" not in render_character(
        replace(p, outfit=replace(p.outfit, staff_color=None)), sk
    )


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
    """Every (preset, build, path) `ref-out/` is supposed to hold, minus the cover:
    the tall chibi, every character. The realistic renders under `real/` went
    with the realistic build (`docs/tall-chibi-plan.md`, R2)."""
    return [(preset, "chibi", f"{PREFIX['chibi']}{preset}") for preset in sorted(PRESETS)]


@pytest.mark.parametrize(("preset", "build", "rel"), _published())
def test_ref_out_matches_the_code(preset: str, build: str, rel: str) -> None:
    """The same check `./refresh-ref-out.sh --check` makes, minus the PNGs.

    `ref-out/` is committed and the README displays it, so it is stale the
    moment a shape changes without it. If this fails after a deliberate shape
    change, the fix is to run the script, not to edit the expectation.
    """
    p = PRESETS[preset]
    committed = REF_OUT / f"{rel}.svg"
    expected = render_character(p, character.skeleton_for(p))
    assert committed.read_text() == expected, f"{rel}.svg is stale: ./refresh-ref-out.sh"


def test_the_retired_builds_left_nothing_behind() -> None:
    """No realistic renders anywhere under `ref-out/`: not the old top-level
    `*_real` files, nor `real/`, which went with the realistic build
    (`docs/tall-chibi-plan.md`, R2). A leftover is the worst kind of stale:
    nothing renders to it any more, so no comparison ever looks at it again. The
    script reports these rather than deleting them, since `ref-out/` is
    committed."""
    left = sorted(p.name for p in REF_OUT.rglob("*_real.*"))
    left += sorted(p.name for p in (REF_OUT / "real").glob("*"))
    assert not left, f"the realistic build is retired; git rm {left}"


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
    sk = character.skeleton_for(p)
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
    sk = character.skeleton_for(p)
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
def test_sleeve_under_cap_slants_the_cap_and_the_arm_top_with_it(build: str) -> None:
    """The cap's underside and the arm's top edge are one line, so they have to
    move together: a slanted cap over an arm still cut flat leaves a wedge of
    background between them. Checked on the arm's own outer top corner, which
    must land on the underside line, not on the flat hem it had before."""
    capped = PRESETS["satoshi"]
    assert capped.outfit.sleeve_under_cap, "the slanted cap is the default"
    sk = character.skeleton_for(capped)
    plain = replace(capped, outfit=replace(capped.outfit, sleeve_under_cap=False))
    plain_svg = render_character(plain, sk)
    capped_svg = render_character(capped, sk)
    assert plain_svg != capped_svg
    ET.fromstring(capped_svg)

    centre_top, _, _, _ = character._arm_line(sk)
    outer = centre_top + sk.arm_half_w
    tip_y = character._cap_tip_y(sk)
    y = character._cap_underside_y(sk, outer, tip_y)
    assert tip_y <= y < character._sleeve_hem_y(sk), (
        f"{build}: the arm's outer corner meets the underside at {y:.1f}, outside"
        f" the cap's own span {tip_y:.1f}..{character._sleeve_hem_y(sk):.1f}"
    )
    assert f"{sk.head_cx + outer:.1f} {y:.1f}" in capped_svg, (
        f"{build}: the arm's top edge does not end on the cap's underside"
    )


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_neckline_stand_raises_a_tab_either_side_of_the_neck(build: str) -> None:
    """The stand collar's tabs sit on the neck's own contour and rise above the
    shoulder line, and its V opens at the neck's width: the tunic's outline has to
    pass through the neck's edge at the shoulder line on both sides, where the
    plain V starts inside it."""
    stand = PRESETS["satoshi"]
    assert stand.outfit.neckline_stand, "the stand collar is the default"
    sk = character.skeleton_for(stand)
    base = replace(stand, outfit=replace(stand.outfit, neckline_stand=False))
    plain_svg, stand_svg = render_character(base, sk), render_character(stand, sk)
    assert plain_svg != stand_svg
    ET.fromstring(stand_svg)
    tunic = character._tunic(sk, stand)
    for side in (-1, 1):
        x = sk.head_cx + side * sk.neck_half_w
        assert f"{x:.1f} {sk.shoulder_y:.1f}" in tunic, (
            f"{build}: the V does not start on the neck's edge at the shoulder line"
        )
        assert f"{x:.1f} {sk.shoulder_y - sk.head_r * 0.06:.1f}" in tunic, (
            f"{build}: no tab rises above the shoulder line beside the neck"
        )


def test_neckline_stand_defers_to_a_collar_and_a_round_neckline() -> None:
    base = PRESETS["satoshi"]
    for change in ({"collar_color": "#c9a13b"}, {"neckline_round": True}):
        stand = replace(base, outfit=replace(base.outfit, **change))
        plain = replace(stand, outfit=replace(stand.outfit, neckline_stand=False))
        assert render_character(plain) == render_character(stand), change


@pytest.mark.parametrize("body", ["tall_chibi", "tall_chibi_long_torso"])
def test_waist_shift_moves_the_belt_line_and_nothing_above_or_below_it(body: str) -> None:
    """`waist_shift` slides the waist and hip together, in head radii, and leaves
    the shoulders, knees and soles where the build put them. It is a character
    field, so it is ignored when a skeleton is handed in."""
    base = replace(PRESETS["satoshi"], body=body, waist_shift=0.0)
    shifted = replace(base, waist_shift=0.3)
    a, b = character.skeleton_for(base), character.skeleton_for(shifted)
    assert b.waist_y == pytest.approx(a.waist_y + 0.3 * a.head_r)
    assert b.hip_y == pytest.approx(a.hip_y + 0.3 * a.head_r)
    for unchanged in ("shoulder_y", "knee_y", "ankle_y", "foot_y", "head_r", "head_cy"):
        assert getattr(b, unchanged) == getattr(a, unchanged), unchanged
    ET.fromstring(render_character(shifted))
    assert render_character(shifted, a) == render_character(base, a)


def test_tall_chibi_long_torso_is_tall_chibi_with_a_lower_belt_and_a_bigger_head() -> None:
    """The default body is Katherina's measured `tall_chibi` with the belt half a
    head radius lower and the head 1.1 times as big against the same body, and she
    keeps her own: her traced cuts were fitted to that profile's exact landmarks,
    so it must not move."""
    from dataclasses import fields

    base = character.BODY_TYPES["tall_chibi"]
    low = replace(base, waist_y=base.waist_y + 0.5, hip_y=base.hip_y + 0.5).head_scaled(
        character._LONG_TORSO_HEAD_SCALE
    )
    have = character.BODY_TYPES["tall_chibi_long_torso"]
    for f in fields(base):
        assert getattr(have, f.name) == pytest.approx(getattr(low, f.name)), f.name
    assert character._LONG_TORSO_HEAD_SCALE == 1.1
    assert CharacterParams().body == "tall_chibi_long_torso"
    assert PRESETS["katherina"].body == "tall_chibi"


def test_head_scaled_makes_the_head_bigger_against_the_same_body() -> None:
    """`heads` alone would only rescale the whole figure. A scaled profile keeps
    the body's own proportions (its landmarks against each other) and changes only
    the head against them, by exactly the scale."""
    base = character.BODY_TYPES["tall_chibi"]
    assert base.head_scaled(1.0) == base
    big = base.head_scaled(1.1)
    sk0 = build_skeleton(heads=base.heads)
    sk1 = build_skeleton(heads=big.heads)
    a = base.applied(sk0, sk0.build)
    b = big.applied(sk1, sk1.build)

    def leg_to_head(sk):
        return (sk.ankle_y - sk.hip_y) / (2 * sk.head_r)

    assert leg_to_head(b) == pytest.approx(leg_to_head(a) / 1.1)
    assert (b.ankle_y - b.waist_y) / (b.waist_y - b.shoulder_y) == pytest.approx(
        (a.ankle_y - a.waist_y) / (a.waist_y - a.shoulder_y)
    )
    assert b.waist_half_w / b.head_r == pytest.approx(a.waist_half_w / a.head_r / 1.1)


@pytest.mark.parametrize("body", ["tall_chibi", "tall_chibi_long_torso"])
def test_a_tall_boot_stops_below_the_knee_not_at_the_belt(body: str) -> None:
    """`boot_shaft` sends the shaft toward the knee. A body profile's `knee_y` can
    sit above the hip (Katherina's is under her skirt), so the shaft has to aim at
    a real knee: on the long-torso body it once came up to the belt."""
    p = replace(
        PRESETS["reinhard"], body=body, outfit=replace(PRESETS["reinhard"].outfit, boot_shaft=1.0)
    )
    sk = character.skeleton_for(p)
    boot = character._boot(sk, p, sk.head_cx, sk.leg_half_w, 1)
    top = min(float(v) for v in re.findall(r"[\d.]+ ([\d.]+)", boot))
    knee = max(sk.knee_y, sk.hip_y + (sk.ankle_y - sk.hip_y) * 0.5)
    assert top >= knee - 0.01 * sk.head_r, (
        f"{body}: the tall shaft tops out at {top:.1f}, above the real knee at {knee:.1f}"
    )


@pytest.mark.parametrize("preset", ["kyoko", "gero", "tomohiro"])
def test_a_belt_worn_with_an_open_coat_is_drawn_under_it(preset: str) -> None:
    """The coat's panels lie over the belt, which shows only in the opening: drawn
    over the panels it stopped short of the arms and read as a patch on the
    middle one. A coatless belt still goes over the tunic, after everything a
    coat would be worn over."""
    p = PRESETS[preset]
    assert p.outfit.coat_color is not None and p.outfit.belt_color is not None
    sk = character.skeleton_for(p)
    svg = render_character(p, sk)
    belt, coat = character._belt(sk, p), character._coat(sk, p)
    assert belt in svg and coat in svg
    assert svg.index(belt) < svg.index(coat), f"{preset}: the belt is over the coat"
    bare = replace(p, outfit=replace(p.outfit, coat_color=None))
    bare_svg = render_character(bare, sk)
    assert bare_svg.index(character._belt(sk, bare)) > bare_svg.index(character._tunic(sk, bare))


def test_keikos_dress_is_a_column_not_a_flared_skirt() -> None:
    """The shared parametric skirt flares from the hip and hem anchors, which on
    Keiko came to 1.153 half-widths where her reference's dress is 0.327: three
    times too wide, spilling past the coat's panels on both sides and reading as
    a second garment clipping through the first. The column stays inside the
    coat's own opening all the way down."""
    p = PRESETS["keiko"]
    assert p.outfit.skirt_cut == "column"
    column = character.SKIRT_CUTS["column"].fills[0]
    xs = [column[0]] + [e for _, e in column[1]]
    assert max(abs(x) for x, _ in xs) < 0.40, "the column is as wide as a skirt"
    sk = character.skeleton_for(p)
    flared = character._skirt_half_w(sk, sk.head_cy + 4.30 * sk.head_r) / sk.head_r
    assert flared > 1.0, "the shared skirt is no longer the wide one this replaces"
    # and the cut is what she actually draws, not the flare
    assert character._skirt(sk, p) == character._draw_cut(
        sk, character.SKIRT_CUTS["column"], p.outfit.skirt_color
    )


def test_the_lab_coats_opening_pinches_at_the_waist() -> None:
    """The one reversal that makes the front read as tailored.

    The shared `_coat` opens steadily from throat to hem (`gap_top` under
    `gap_hem`), and the reference does not: measured clear of the belt it runs
    0.580 wide at the throat, narrows to about 0.45 from y 2.0 down to the
    belt, then widens again to 0.687 by 4.75 (`harness/keiko/landmarks.py`).
    Checked on the cut's own coordinates, where those numbers live, rather than
    on a render, so it cannot be confused by the body it is mapped onto."""
    panel = character.COAT_CUTS["lab_coat"].fills[1]  # the viewer's right
    start, segs = panel
    xs = [start] + [e for _, e in segs]
    inner = [(y, x) for x, y in xs if 0 < x < 0.45]
    throat = min(inner, key=lambda t: t[0])[1]
    waist = min(x for y, x in inner if 1.8 < y < 2.6)
    hem = max(inner, key=lambda t: t[0])[1]
    assert waist < throat, f"the opening does not narrow: {throat:.3f} to {waist:.3f}"
    assert hem > waist, f"the opening does not widen again: {waist:.3f} to {hem:.3f}"


def test_the_lab_coat_leaves_the_shared_coat_alone() -> None:
    """The cut is why this campaign touches nobody else. `_coat` serves gero,
    kyoko and tomohiro as well as Keiko, so the lab coat is a registry entry and
    the shared two-panel coat is unchanged: the other three render identically
    whatever the cut does."""
    assert set(character.COAT_CUTS) >= {"open_jacket", "lab_coat"}
    for preset in ("gero", "kyoko", "tomohiro"):
        p = PRESETS[preset]
        assert p.outfit.coat_cut is None and not p.outfit.coat_sleeves
        sk = character.skeleton_for(p)
        assert character._coat(sk, p), f"{preset} lost the shared coat"


def test_a_coat_sleeve_runs_to_the_wrist_in_the_coats_colour() -> None:
    """A lab coat has full sleeves and nothing of the dress shows on the arm.

    Two things went wrong here and both are held: dropping the undersleeve left
    the arm bare, because only an undersleeve or `sleeve_long` made the sleeve
    reach the wrist; and the parametric sleeve was filled from `sleeve` while
    only the traced one read `sleeve_fill`, so the arm came out in the dress's
    charcoal under a white coat. The cuff is one line, not a filled band in a
    second tone: the reference's cuff is the same cloth turned back."""
    p = PRESETS["keiko"]
    assert p.outfit.coat_sleeves and p.outfit.undersleeve_color is None
    sk = character.skeleton_for(p)
    arms = character._arms(sk, p)
    assert f'fill="{p.outfit.coat_color}"' in arms, "the sleeve is not the coat's colour"
    assert f'fill="{p.outfit.tunic_color}"' not in arms, "the dress shows on the arm"
    assert 'stroke-linecap="round"' in arms and "<line" in arms, "no cuff line"
    bare = replace(p, outfit=replace(p.outfit, coat_sleeves=False))
    assert character._arms(sk, bare) != arms


def test_a_dress_belt_carries_a_keeper_either_side_of_the_buckle() -> None:
    """Two loops set out from the buckle and standing proud of the band, against
    the working belt's single small loop beside it. Off by default, because
    `_belt_drawn` dresses all seventeen presets: the other sixteen keep the one
    keeper, byte for byte."""
    p = PRESETS["keiko"]
    sk = character.skeleton_for(p)
    assert p.outfit.belt_keeper_pair
    _, h = character._belt_band(sk, p.outfit.belt_scale)
    pair = character._belt_drawn(sk, p)
    single = character._belt_drawn(sk, replace(p, outfit=replace(p.outfit, belt_keeper_pair=False)))
    assert pair != single
    # Above the band and above the buckle, which is 1.08 of it; the keepers are
    # 1.27. The band's own printed height rounds up past `h`, hence the margin.
    tall = [w for w in re.findall(r'height="(\d+\.\d+)"', pair) if float(w) > h * 1.15]
    # and it is flat: the band across the lower half reads as the strap's own
    # thickness on dark leather and as a grey stripe on a white belt, so a
    # dress belt does without it while the rest of the cast keeps it.
    assert f'fill="{character.shade(p.outfit.belt_color)}"' not in pair
    assert (
        f'fill="{character.shade(PRESETS["satoshi"].outfit.belt_color)}"'
        in character._belt_drawn(character.skeleton_for(PRESETS["satoshi"]), PRESETS["satoshi"])
    )
    assert len(tall) == 2, f"expected two keepers standing above the band, got {tall}"
    for other in ("satoshi", "satoko", "elara"):
        q = PRESETS[other]
        assert not q.outfit.belt_keeper_pair
        o_sk = character.skeleton_for(q)
        assert character._belt_drawn(o_sk, q) == character._belt_drawn(o_sk, q)


def test_keikos_belt_is_worn_over_her_coat_and_her_arms_over_both() -> None:
    """The reference wears a belt over the lab coat, and the cast's other open
    coats wear theirs under, so the order rides on the cut and never changes
    globally. Her coat also goes *under* the arms, unlike Katherina's jacket,
    whose armholes have to cover the tops of her sleeves: Keiko's sleeve is a
    piece in its own right and has to lie over the body carrying its own
    outline, or panel and sleeve merge into one undivided field and the belt
    looks like it stops in the middle of nothing (P4, P5). The bust plan's step
    5b put it over the arms and was reversed at the owner's call: the arm in
    front of the coat and the bust in front of the arm (step 5c)."""
    p = PRESETS["keiko"]
    sk = character.skeleton_for(p)
    assert character._traced_coat(sk, p)
    assert character._belt(sk, p) == "", "the under-coat belt still draws as well"
    svg = render_character(p, sk)
    coat = character._traced_coat_and_belt(sk, p, after_arms=False)
    assert coat and svg.index(coat) < svg.index(character._arms(sk, p)), (
        "the lab coat is not drawn under the arms"
    )
    belt = character._belt_drawn(sk, p)
    jacket = character._draw_cut(sk, character.COAT_CUTS["lab_coat"], p.outfit.coat_color)
    assert svg.index(belt) > svg.index(jacket), "the belt is not over the coat"
    # ...and it travels under the arms with the coat it is worn over, so the
    # arm's outline is what ends the band. Her belt has no end caps, so
    # something has to stop it: drawn over the arms its ends sat on the arm's
    # own outline and read as a strap laid across the front rather than a belt
    # going round the body.
    assert svg.index(belt) < svg.index(character._arms(sk, p)), (
        "the belt is drawn over the arms, so nothing ends the band"
    )
    # Katherina's jacket keeps the other order, and her cut is what says so.
    assert character.COAT_CUTS["open_jacket"].over_arms
    assert not character.COAT_CUTS["lab_coat"].over_arms
    k = PRESETS["katherina"]
    k_sk = character.skeleton_for(k)
    k_svg = render_character(k, k_sk)
    jacket = character._traced_coat_and_belt(k_sk, k)
    assert k_svg.index(jacket) > k_svg.index(character._arms(k_sk, k, hands=False))
    # Her hands are drawn after the jacket, which clipped one of them before.
    assert k_svg.index(character._arms(k_sk, k, hands=True)) > k_svg.index(jacket)


def test_a_mock_collar_hugs_the_neck_and_covers_the_tunics_v() -> None:
    """A mock neck takes the neck's own silhouette, where the standing band
    spreads to 1.70 neck half-widths and reads as a yoke. It also has to reach
    below the tunic's V, which is cut to `neck_half_w * 0.28` under the shoulder
    line whenever a collar is worn, or a sliver of throat shows under the band,
    and it carries no centre notch: there are no two halves to meet."""
    p = PRESETS["keiko"]
    assert p.outfit.collar_mock and p.outfit.collar_color is not None
    sk = character.skeleton_for(p)
    band = character._collar(sk, p)
    for side in (-1, 1):
        x = sk.head_cx + side * sk.neck_half_w * 1.03
        assert f"{x:.1f}" in band, "the band is not at the neck's own width"
    standing = replace(p, outfit=replace(p.outfit, collar_mock=False))
    assert character._collar(sk, standing) != band
    assert band.count("<path") == 2, (
        "the mock neck is a fill and an open edge, so the seam at its lower edge can "
        "be line work; either way it draws no centre notch, having no opening for one"
    )
    # That seam is thinner than an outline: the dress below the band is the same
    # cloth in the same colour, and a full-weight edge across it read as a block
    # (the owner's review, P2).
    seam = band[band.index("<line") :]
    width = float(re.search(r'stroke-width="(\d+\.\d+)"', seam).group(1))
    assert width < character._stroke_w(sk), "the seam is a full outline"
    # Skin shows between the chin and the band: drawn above the chin it was
    # covered by the head and the throat read as one dark slab.
    assert (
        min(float(t) for t in re.findall(r"\d+\.\d+", band.split('d="')[1].split('"')[0])[1::2])
        > sk.head_cy + sk.head_r
    ), "the band rises above the chin"
    v_point = sk.shoulder_y + sk.neck_half_w * 0.28
    bottom = max(
        float(t) for t in re.findall(r"\d+\.\d+", band.split('d="')[1].split('"')[0])[1::2]
    )
    assert bottom >= v_point, f"the band stops at {bottom:.1f}, above the V's {v_point:.1f}"


def test_a_mock_collar_is_worn_under_an_open_coat() -> None:
    """The lapels lie over the band's corners, which is what the reference shows.
    Drawn in the standing collar's late place the corners sat on top of the coat
    and the band read as a bib. The standing collar keeps that late place, so
    Katherina's does not move under her jacket with it."""
    p = PRESETS["keiko"]
    sk = character.skeleton_for(p)
    svg = render_character(p, sk)
    # Her coat is traced, so it is `_traced_coat_and_belt` that draws it, before
    # the arms; the band still has to come first.
    assert svg.index(character._collar(sk, p)) < svg.index(
        character._traced_coat_and_belt(sk, p, after_arms=False)
    )
    other = PRESETS["katherina"]
    o_sk = character.skeleton_for(other)
    assert not other.outfit.collar_mock
    o_svg = render_character(other, o_sk)
    assert o_svg.index(character._collar(o_sk, other)) > o_svg.index(character._tunic(o_sk, other))


@pytest.mark.parametrize("body", ["tall_chibi", "tall_chibi_long_torso"])
@pytest.mark.parametrize("preset", ["daizen", "haruto", "reika"])
def test_a_sash_stays_a_wide_flat_band_on_every_chibi_body(preset: str, body: str) -> None:
    """A sash's depth followed the waist-to-hip distance, a sliver on the shared
    chibi and most of a head radius on a body with a real waist, so it came out a
    box there. On the shared chibi the cast's sashes are 4.8 to 6 times as wide as
    they are deep; it must stay a band, and never thinner than a plain belt."""
    p = replace(PRESETS[preset], body=body)
    sk = character.skeleton_for(p)
    _, depth = character._belt_band(sk, p.outfit.belt_scale)
    width = 2 * character._belt_line_half_w(sk) * 1.03
    assert width / depth >= 3.3, f"{preset} on {body}: the sash is {width / depth:.1f}:1, a box"
    assert depth >= character._belt_band(sk)[1]


@pytest.mark.parametrize("body", ["tall_chibi", "tall_chibi_long_torso"])
@pytest.mark.parametrize("preset", ["chiyo", "satoko"])
def test_an_apron_is_no_taller_than_it_is_wide_on_every_chibi_body(preset: str, body: str) -> None:
    """On the shared chibi the apron is a short wide panel; on a body with a long
    drop to the hem it hung to the hem as a tall strip that read as a bag."""
    p = replace(PRESETS[preset], body=body)
    sk = character.skeleton_for(p)
    d = re.search(r'd="([^"]+)"', character._apron(sk, p))
    assert d is not None
    xs = [float(v) for v in re.findall(r"([\d.]+) [\d.]+", d.group(1))]
    ys = [float(v) for v in re.findall(r"[\d.]+ ([\d.]+)", d.group(1))]
    width, height = max(xs) - min(xs), max(ys) - min(ys)
    assert height <= width * 1.02, f"{preset} on {body}: {width:.0f} wide, {height:.0f} tall"


@pytest.mark.parametrize("body", ["tall_chibi", "tall_chibi_long_torso"])
def test_the_crystals_clear_the_buckle_and_stay_on_the_belt(body: str) -> None:
    """Two crystals a side with the buckle showing between the middle pair, all
    inside the belt. On a body with a narrow waist and a deep belt the old spacing
    put the middle pair on the buckle and hid it. The shared chibi keeps the
    fractions it was fitted to."""
    p = replace(PRESETS["elara"], body=body)
    sk = character.skeleton_for(p)
    _, belt_h = character._belt_band(sk)
    scale, (outer_l, inner_l, inner_r, outer_r) = character._crystal_layout(sk, belt_h)
    w = 0.58 * sk.head_r * (0.30 + 0.12 * sk.build) * scale
    assert inner_l == -inner_r and outer_l == -outer_r
    assert inner_r >= belt_h * 1.5 / 2 + w / 2, f"{body}: the middle crystals sit on the buckle"
    assert outer_r + w * 1.22 / 2 <= sk.waist_half_w * 1.03 + 0.5, (
        f"{body}: the outer strap runs past the belt's end"
    )


@pytest.mark.parametrize("body", ["tall_chibi", "tall_chibi_long_torso"])
@pytest.mark.parametrize("preset", ["satoshi", "tenno", "linnea"])
def test_the_belt_covers_the_trouser_tops(preset: str, body: str) -> None:
    """On a body with a narrow waist the trousers hang wider than the belt, and
    their square corners stood out under its rounded ends as a small step. The belt
    has to reach the trousers' outer edge; on the shared chibi it is wider than the
    legs anyway and keeps the waist's width."""
    p = replace(PRESETS[preset], body=body)
    assert p.outfit.trouser_color is not None
    sk = character.skeleton_for(p)
    m = re.search(r'<rect x="([\d.]+)" y="[\d.]+" width="([\d.]+)"', character._belt_drawn(sk, p))
    assert m is not None
    half = float(m.group(2)) / 2
    gap, w_top = character._leg_gap_and_top(sk, True)
    assert half >= gap + w_top - 0.05, f"{preset} on {body}: the trousers stand out past the belt"


def test_a_katana_is_worn_only_when_asked_for() -> None:
    """`katana_color` is the whole switch: none, no sword, and a character without
    one renders exactly as it did before the prop existed."""
    p = PRESETS["katherina"]
    assert p.outfit.katana_color is None
    sk = character.skeleton_for(p)
    assert character._katana(sk, p) == ""
    armed = replace(p, outfit=replace(p.outfit, katana_color="#3c322b"))
    assert character._katana(sk, armed) != ""
    assert PRESETS["satoshi"].outfit.katana_color == "#3c322b"
    assert PRESETS["tomohiro"].outfit.katana_color is None


@pytest.mark.parametrize("body", ["tall_chibi", "tall_chibi_long_torso"])
def test_the_katana_hangs_from_the_belt_on_the_left_and_clears_the_arm(body: str) -> None:
    """The guard sits at the belt on the character's left (the viewer's right), the
    tip stays above the soles, and the guard's outer edge stays inside the arm's
    inner edge, since the arm is drawn over the sword and would otherwise cover
    half of it."""
    p = replace(PRESETS["satoshi"], body=body)
    sk = character.skeleton_for(p)
    r = sk.head_r
    xf = character._katana_placement(sk)
    guard = xf((0.0, 0.0))
    belt_y, belt_h = character._belt_band(sk)
    assert guard[0] > 0, f"{body}: the sword is on the wrong hip"
    assert abs(guard[1] * r + sk.head_cy - (belt_y + belt_h / 2)) < 0.6 * r, (
        f"{body}: the guard is not at the belt"
    )
    tip = xf((2.4363, 0.0))
    assert sk.head_cy + tip[1] * r < sk.foot_y, f"{body}: the tip is through the floor"
    centre_top, _, centre_wrist, _ = character._arm_line(sk)
    centre_elbow = centre_top + (centre_wrist - centre_top) * 0.35
    arm_inner = (centre_elbow - sk.arm_half_w * (1.0 - 0.15 * sk.build)) / r
    edge = guard[0] + xf((0.0, character._KATANA_GUARD_HALF_V))[0] - xf((0.0, 0.0))[0]
    assert edge <= arm_inner + 0.02, f"{body}: the guard runs under the arm"


@pytest.mark.parametrize("preset", ["satoshi", "chiyo", "katherina"])
def test_a_sheet_tile_draws_the_figure_on_its_own_body(preset: str) -> None:
    """A sheet is built from the same figures as the individual renders, on the
    same body: `_tile` used `build_skeleton`, which knows no body profile, so every
    sheet, and every insert built from one, stayed on the old shared chibi after the
    default body changed. The figure the tile draws must be the one `skeleton_for`
    gives (with the hat's headroom left out, so every tile stands at one scale)."""
    from anime_character_creator import sheet

    p = PRESETS[preset]
    bare = replace(p, outfit=replace(p.outfit, hat_color=None))
    sk = character.skeleton_for(bare)
    doc = render_character(p, sk)
    body = re.sub(r"</svg>\s*\Z", "", re.sub(r"\A<svg[^>]*>\s*", "", doc)).strip()
    svg = sheet.render_sheet(sheet.SheetParams(members=(preset,), columns=1))
    assert body in svg, f"{preset}: the sheet does not draw the figure on its own body"
    old = render_character(p, build_skeleton(heads=BUILDS["chibi"], frame=p.frame))
    assert re.sub(r"\A<svg[^>]*>\s*", "", old) not in svg


def test_katana_length_stretches_the_scabbard_and_nothing_else() -> None:
    """A longer sword is a longer scabbard: the handle, guard, collar, rings and the
    end cap keep their size (the cap moves as one), and 1.0 is the traced sword."""
    grow1 = character._katana_stretched(1.0)
    for pt in ((-1.2, 0.1), (0.0, 0.2), (0.3, 0.14), (1.5, 0.15), (2.4, 0.1)):
        assert grow1(pt) == pt
    grow = character._katana_stretched(1.3)
    f = character._katana_stretch_factor(1.3)
    a, b = character._KATANA_STRETCH_FROM, character._KATANA_STRETCH_TO
    assert grow((-1.2, 0.1)) == (-1.2, 0.1)
    assert grow((a, 0.1)) == (a, 0.1)
    assert grow((b - 0.1, 0.1))[0] == pytest.approx(a + (b - 0.1 - a) * f)
    tip = grow((character._KATANA_TIP_U, 0.0))[0]
    assert tip - (-1.295) == pytest.approx(1.3 * character._KATANA_TRACED_LENGTH, abs=0.02)
    cap0, cap1 = grow((b, 0.0))[0], grow((character._KATANA_TIP_U, 0.0))[0]
    assert cap1 - cap0 == pytest.approx(character._KATANA_TIP_U - b), "the cap changed size"


@pytest.mark.parametrize("body", ["tall_chibi", "tall_chibi_long_torso"])
@pytest.mark.parametrize("length", [0.8, 1.0, 1.25, 1.4])
def test_a_longer_katana_keeps_its_tip_off_the_floor(length: float, body: str) -> None:
    """A longer sword swings out about the guard until its tip stands above the
    soles, as far as the tilt cap allows, and never comes out shorter."""
    p = replace(PRESETS["haruto"], body=body)
    p = replace(p, outfit=replace(p.outfit, katana_length=length))
    sk = character.skeleton_for(p)
    xf = character._katana_placement(sk, length)
    tip = xf(character._katana_stretched(length)((character._KATANA_TIP_U, 0.0)))
    assert sk.head_cy + tip[1] * sk.head_r <= sk.foot_y + 0.05 * sk.head_r, (
        f"{body} at {length}: the tip is through the floor"
    )
    assert character._katana(sk, p) != ""


def test_haruto_and_daizen_carry_full_length_katanas_and_satoshi_the_short_one() -> None:
    satoshi = PRESETS["satoshi"].outfit.katana_length
    assert satoshi == 0.95
    for name in ("haruto", "daizen"):
        assert PRESETS[name].outfit.katana_color is not None
        assert PRESETS[name].outfit.katana_length > satoshi + 0.2


def test_sleeve_under_cap_defers_to_a_traced_jacket() -> None:
    """A traced jacket draws its own shoulders and armholes, so the flag must not
    reshape the tunic beneath it."""
    base = PRESETS["katherina"]
    plain = replace(base, outfit=replace(base.outfit, sleeve_under_cap=False))
    assert render_character(base) == render_character(plain)


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
    # Still on the shared skeleton, not the tall chibi's: there the legs' path
    # carries the long-torso profile's knee landmark, which sits above the hip,
    # as a control point, and this check reads a garment's top as its highest
    # coordinate. Hidden under the tunic, and fixed with the real knee in R4
    # (`docs/tall-chibi-status.md`, R3).
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
    sk = character.skeleton_for(p)
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


def test_the_cover_renders_and_stays_deterministic() -> None:
    """Same params, same bytes, the same contract `render_character` holds.

    The mist banks are the reason this is worth pinning: their skyline comes
    from a jitter function keyed on an index rather than an RNG, precisely so a
    cover can be compared rather than eyeballed. An RNG would pass every other
    check here and fail only this one.
    """
    p = cover.CoverParams(subtitle="BOOK ONE")
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
    assert was.frame == now.frame
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


def test_the_topknot_is_visible_and_still_fits() -> None:
    """A knot has to clear the cut under it and stay inside the canvas margin.

    Both halves have bitten. Drawn at -1.02 head radii it was a same-coloured
    ellipse buried in same-coloured hair and drew nothing; the shipped cuts top
    out around -1.25 to -1.28, so it has to sit above that. And the hair margin
    `build_skeleton` leaves puts the ceiling at -1.36, so there is well under a
    tenth of a radius to land in. Nothing else checks a part that is not a
    `Hairstyle`, and the failure at either end is silent: too low is invisible,
    too high is sliced flat against the canvas edge.
    """
    p = PRESETS["haruto"]
    sk = character.skeleton_for(p)
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


def test_the_sideburn_rides_the_jaw_rather_than_chording_it() -> None:
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
    guarded lives in how the points are joined up, not in where they are.

    The *inner* edge is deliberately not held to this. It carries the width
    easing, so it bows away from its own two ends by about a tenth of a head
    radius on purpose; what has to hold there is the taper, which is the next
    test.
    """
    p = PRESETS["reinhard"]
    sk = character.skeleton_for(p)
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


def test_the_sideburn_never_narrows_on_its_way_down() -> None:
    """The strip covers more of the cheek at every step toward the jaw.

    This is the original defect stated as an invariant. The strip used to be
    0.31 head radii wide beside the eye and 0.06 at the jaw, and two edges that
    converge make a triangle, so it read as a cut-out rather than as hair. A
    reference beard runs the other way: thin in front of the ear, spreading
    where it meets the mass.

    Measured as how far the inner edge sits inside the skull's own edge, which
    is what the width looks like once it is drawn on a face that is itself
    narrowing. That makes it a check on the contour's taper and the ratio and
    the width together, not a restatement of the three constants.

    Computed rather than parsed, unlike its neighbour. The inner edge's points
    are buried mid-path between the chin's curves and the top edge's dive, and
    what is being asserted here is where they are, which is exactly the half a
    parse would add nothing to.
    """
    sk = character.skeleton_for(PRESETS["reinhard"])
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
    sk = character.skeleton_for(p)
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
def test_the_moustache_is_thicker_than_the_line_that_draws_it(preset: str) -> None:
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
    sk = character.skeleton_for(p)
    lip_top = character._MOUTH_Y - character._BEARD_LIP_H * 0.12 * p.face.mouth_width
    band = (lip_top - character._BEARD_TASH_Y) * sk.head_r
    stroke = character._stroke_w(sk)
    assert band >= stroke * 2, (
        f"{preset} has {band:.1f}px of moustache between the lobe and the "
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
    sk = character.skeleton_for(p)
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
    sk = character.skeleton_for(p)
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
    sk = character.skeleton_for(p)
    if character._traced_coat(sk, p):
        # Keiko wears `COAT_CUTS["lab_coat"]` at the chibi builds, which draws
        # its own notched lapel and leaves `_coat` empty; she still falls
        # through to the shared coat at the realistic build, where this holds.
        pytest.skip(f"{preset} wears a traced coat at {build}")
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
    sk = character.skeleton_for(p)
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
    sk = character.skeleton_for(p)
    svg = render_character(p, sk)
    assert svg.index(character._legs_and_boots(sk, p)) < svg.index(character._hakama(sk, p)), (
        f"{preset}: the hakama is drawn before the legs, so the legs would paint over it"
    )


def test_the_chibi_hem_pull_back_is_floored_at_half() -> None:
    """A long hem still lands noticeably lower than a short one, at chibi.

    The owner's report on #103: at the shipped `sk.build`-only blend, 0.1 at
    chibi, two lengths as far apart as 0.60 and 0.95 land within four pixels of
    each other, which is indistinguishable at this figure's size and is why
    Reika's near-floor-length hakama read as mid-thigh. `harness/hem/pullback.py`
    swept candidates against four references; the owner's pick on 2026-08-10
    was a floor at half.

    Checked as a real separation between a short and a long request rather than
    as the constant itself, so the guard survives the floor being retuned to a
    different number later without also needing to be edited.
    """
    sk = build_skeleton(heads=BUILDS["chibi"])
    short = character._skirt_hem_y(sk, 0.20)
    long = character._skirt_hem_y(sk, 0.95)
    gap = long - short
    span = sk.ankle_y - sk.hip_y
    assert gap > span * 0.3, (
        f"a 0.20 and a 0.95 hem are only {gap:.1f}px apart at chibi, {gap / span:.0%} of the "
        f"hip-to-ankle span, which reads as the same length"
    )


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_the_goggles_lift_off_the_eye_rather_than_frame_it(build: str) -> None:
    """The lenses sit well above the brow line, not over the eye.

    Pushed up onto the forehead is the one thing that tells a pair of goggles
    from a pair of glasses; a lift too small would draw a second `_glasses`
    over the same aperture instead.
    """
    p = PRESETS["krista"]
    sk = character.skeleton_for(p)
    svg = character._goggles(sk, p)
    circles = re.findall(r'<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([\d.]+)"', svg)
    _dx, eye_y, eye_r, _f = character._eye_placement(sk, p)
    brow_y = eye_y - eye_r * 1.30
    lens_ys = {float(y) for _x, y, r in circles if float(r) > eye_r * 0.5}
    assert lens_ys, f"{build}: found no lens-sized circles among {circles!r}"
    for y in lens_ys:
        assert y < brow_y - eye_r * 0.5, (
            f"{build}: a lens at y={y:.1f} is not clearly above the brow at {brow_y:.1f}"
        )


def test_the_goggles_do_not_leave_the_ponytail_tie_exposed() -> None:
    """The tie's bounding box mostly falls inside the goggle's own footprint.

    Krista is the only wearer of both a bound ponytail and goggles, and the two
    were tuned without knowledge of each other: `_tail_tie`'s original anchor,
    0.62 head radii up and 0.62 out, put 41% of the tie's own bounding box
    outside the goggle's, which painted over the tie's centre and left its
    outline poking out past the right lens, visible as a stray arc beside the
    strap. `_tail_tie` was moved out along the same high-and-back direction
    (0.78 out, 0.46 up) rather than picked to dodge the strap's exact shape.
    Checked as a fraction of the tie's own area rather than exactly zero,
    since a sliver landing right at the lens's edge reads as a strap buckle and
    is not the failure the owner reported.
    """
    p = PRESETS["krista"]
    assert p.hair_tail > 0.0 and p.outfit.goggle_color is not None, (
        "this test only means something for a character with both"
    )
    for build in sorted(BUILDS):
        sk = character.skeleton_for(p)
        eye_dx, eye_y, eye_r, _f = character._eye_placement(sk, p)
        lens_r = eye_r * character._GOGGLE_R_SCALE
        lens_dx = eye_dx * character._GOGGLE_DX_SCALE
        lens_y = eye_y - eye_r * character._GOGGLE_LIFT
        lens_cx = sk.head_cx + lens_dx
        tx, ty = character._tail_tie(sk)
        tw, th = sk.head_r * 0.20, sk.head_r * 0.13
        ox = max(0.0, min(lens_cx + lens_r, tx + tw) - max(lens_cx - lens_r, tx - tw))
        oy = max(0.0, min(lens_y + lens_r, ty + th) - max(lens_y - lens_r, ty - th))
        fraction = (ox * oy) / ((2 * tw) * (2 * th))
        assert fraction < 0.05, (
            f"{build}: {fraction:.0%} of the tie's bounding box sits outside the goggle's, "
            f"which is the strap-and-tie collision the owner reported"
        )


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_the_goggle_strap_arms_end_inside_the_hair_not_past_it(build: str) -> None:
    """Each arm's outer tip lands inside the hairstyle's own silhouette.

    `_goggles_strap` draws the arms before `_hair_front` so the hair mass
    covers their ends, the same way it already covers the ear. That only works
    if the tip is actually inside the hair's footprint: the first version ran
    the arm past `_hair_edge_x`'s own edge as a "clearance," which is right for
    the headscarf sitting over the hair but backwards here, and it put both
    tips outside the hair entirely, floating in open air on either side of the
    head, the owner's report against the first render of this fix.
    """
    p = PRESETS["krista"]
    sk = character.skeleton_for(p)
    lens_y, _lens_r, _lens_dx = character._goggle_geometry(sk, p)
    strap_y_hr = (lens_y - sk.head_cy) / sk.head_r
    hair_edge = character._hair_edge_x(strap_y_hr, sk, p) * sk.head_r
    svg = character._goggles_strap(sk, p)
    paths = re.findall(r'<path d="([^"]+)"', svg)
    assert len(paths) == 2, f"{build}: expected two arms, found {len(paths)}"
    for d in paths:
        xs = [float(v) for v in re.findall(r"-?\d+\.?\d*", d)][0::2]
        tip = max(abs(x - sk.head_cx) for x in xs)
        assert tip < hair_edge, (
            f"{build}: an arm tip sits {tip:.1f}px from centre, past the hair's own "
            f"edge at {hair_edge:.1f}px, which leaves it floating outside the hair"
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


def test_mist_band_is_the_covers_own_bank():
    from anime_character_creator.cover import CoverParams, _mist_band, mist_band

    p = CoverParams()
    assert mist_band(p.width, 700, 800, "#2b3d41", 3, 0.055) == _mist_band(
        p, 700, 800, "#2b3d41", 3, 0.055
    )
    assert mist_band(3000, 0, 10, "#000", 1, 0.02).startswith('<path d="M -300.0 10.0')


def test_closed_eyes_are_a_lash_line_spanning_the_open_aperture():
    """A shut eye draws no aperture, iris or clip, and its line starts and ends
    on the open almond's own corners, so a cut between the two reads as a blink
    rather than the eye moving."""
    from anime_character_creator.character import _eye_closed, _eye_shape

    f = PRESETS["satoshi"].face
    closed = replace(PRESETS["satoshi"], face=replace(f, eyes_closed=True))
    svg = render_character(closed)
    assert 'id="eye-l"' not in svg and 'id="eye-r"' not in svg
    assert 'id="eye-l"' in render_character(PRESETS["satoshi"])

    d_open, _ = _eye_shape(100.0, 200.0, 20.0, 1, f)
    open_x = [float(v) for v in re.findall(r"(-?\d+\.\d) -?\d+\.\d", d_open)]
    line = _eye_closed(100.0, 200.0, 20.0, 1, f, 3.0)
    ends = re.search(r"M (\S+) \S+ Q \S+ \S+ (\S+) ", line)
    assert float(ends.group(1)) == pytest.approx(min(open_x), abs=0.11)
    assert float(ends.group(2)) == pytest.approx(max(open_x), abs=0.11)


def test_a_skeleton_with_no_bust_is_the_skeleton_built_without_one():
    """`bust=0` is the default in fact, not only in intent (`docs/bust-plan.md`)."""
    for heads in BUILDS.values():
        assert build_skeleton(heads=heads, bust=0.0) == build_skeleton(heads=heads)
        assert build_skeleton(heads=heads).bust_reach == 0.0


def test_the_bust_rides_a_profiled_body_rather_than_the_one_it_replaced():
    """The bust's height is derived from the shoulder and waist a profile or a
    waist shift leaves behind, so it always lies between them. Stored, it kept
    the unprofiled body's height and went stale (`docs/bust-status.md`)."""
    for name in ("satoko", "katherina"):
        sk = character.skeleton_for(replace(PRESETS[name], bust=1.0))
        assert sk.shoulder_y < sk.bust_y < sk.waist_y
        shifted = character.skeleton_for(replace(PRESETS[name], bust=1.0, waist_shift=0.3))
        assert shifted.bust_y > sk.bust_y


def _torso_widest(p: CharacterParams) -> float:
    """The tunic path's furthest point right of centre between armpit and
    waist, in head radii, control points included."""
    sk = character.skeleton_for(p)
    d = re.search(r'd="([^"]+)"', character._tunic(sk, p)).group(1)
    nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", d)]
    top, bottom = character._sleeve_hem_y(sk), sk.waist_y
    xs = [
        x
        for x, y in zip(nums[0::2], nums[1::2], strict=False)
        if top + 0.5 < y < bottom - 0.5 and x > sk.head_cx
    ]
    return (max(xs) - sk.head_cx) / sk.head_r


def test_a_small_bust_moves_the_torso_a_small_amount():
    """The dial is continuous at zero and grows with the value. The first draft
    switched the torso 0.37 head radii out at `bust = 0.01`, because it drew a
    width of its own rather than adding to the tunic's (`docs/bust-plan.md`)."""
    base = PRESETS["satoko"]
    widths = [_torso_widest(replace(base, bust=v)) for v in (0.0, 0.01, 0.5, 1.0)]
    assert widths[1] - widths[0] <= 0.01 + 0.1 / character.skeleton_for(base).head_r
    assert widths[0] <= widths[1] < widths[2] < widths[3]


@pytest.mark.parametrize("name", ["satoko", "keiko", "katherina"])
def test_a_bust_changes_nothing_above_the_armpit(name):
    """The bust only reshapes the armpit-to-waist run, and carries the armpit out
    with it (`_armpit_x`), which tilts a slanted sleeve's underside: so nothing
    above the sleeve's tip moves. Its first version reused a name `_tunic`'s
    shoulder already read and gave every sleeve tip a horn."""

    def above_armpit(bust: float) -> list[tuple[float, float]]:
        p = replace(PRESETS[name], bust=bust)
        sk = character.skeleton_for(p)
        d = re.search(r'd="([^"]+)"', character._tunic(sk, p)).group(1)
        nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", d)]
        pts = zip(nums[0::2], nums[1::2], strict=False)
        return sorted((x, y) for x, y in pts if y < character._cap_tip_y(sk) - 0.5)

    assert above_armpit(1.0) == above_armpit(0.0)


@pytest.mark.parametrize("name", ["satoko", "keiko", "katherina", "reinhard"])
def test_the_body_reads_no_garment(name):
    """`_torso` is the body, built from the skeleton alone, so what a character
    wears cannot change it; garments go over it and have to cover it
    (`docs/bust-plan.md`, step 3)."""
    p = PRESETS[name]
    sk = character.skeleton_for(p)
    assert character._torso(sk, p) == character._torso(sk, replace(p, outfit=character.Outfit()))


def test_the_bust_comes_over_the_arms_at_the_chibi():
    """Nothing without a bust; over the arms at the chibi (`docs/bust-status.md`,
    step 5). The mask's id follows its shape, so a sheet of several figures
    cannot share one."""
    p = replace(PRESETS["satoko"], bust=0.0)
    chibi = character.skeleton_for(p)
    assert character._bust_over_arms(chibi, p, "x") == ""
    small = character._bust_over_arms(character.skeleton_for(replace(p, bust=0.5)), p, "x")
    full = character._bust_over_arms(character.skeleton_for(replace(p, bust=1.0)), p, "x")
    assert 'mask="url(#bust-' in full
    # The outline is drawn only over the arms (step 5c).
    assert 'clip-path="url(#bust-arms-' in full
    assert re.search(r'id="(bust-\w+)"', small).group(1) != re.search(
        r'id="(bust-\w+)"', full
    ).group(1)


def test_a_traced_cut_widens_at_the_bust_and_nowhere_else():
    """With a bust, a traced garment's point at the reference's bust height
    moves out, and its points at the shoulder and the waist do not; without
    one, placement is what it was (`docs/bust-plan.md`, step 6)."""
    ref = character.skeleton_for(CharacterParams(body=character._GARMENT_REF_BODY))
    ref_ys, _ = character._body_knots(ref)
    bust_y = (ref.bust_y - ref.head_cy) / ref.head_r
    flat = character._garment_placement(character.skeleton_for(PRESETS["katherina"]))
    full = character._garment_placement(
        character.skeleton_for(replace(PRESETS["katherina"], bust=1.0))
    )
    assert full((1.0, bust_y))[0] > flat((1.0, bust_y))[0] + 0.05
    shoulder, waist = ref_ys[1], ref_ys[1 + len(character._BUST_KNOTS) + 1]
    for y in (shoulder, waist):
        assert abs(full((1.0, y))[0] - flat((1.0, y))[0]) < 1e-9
        assert abs(full((1.0, y))[1] - flat((1.0, y))[1]) < 1e-9


def test_a_loose_garment_hangs_from_the_bust_where_the_body_tucks_under_it():
    """Below the fullest point the body comes back in to the under-bust tuck;
    a loose garment hangs clear of it and meets the body again only at the
    waist (`docs/bust-plan.md`, step 9b)."""
    sk = character.skeleton_for(replace(PRESETS["satoko"], bust=1.0))
    body, cloth = character._bust_shape(sk), character._bust_shape(sk, drape=True)

    def x_at(bust, y):
        return next(
            x for x in (character._quad_x_at(*pc, y) for pc in bust.pieces()) if x is not None
        )

    tuck_y = body.outline[body.lobe_pieces - 1][1][1]
    assert x_at(cloth, tuck_y) > x_at(body, tuck_y) + 0.3 * sk.bust_reach
    assert cloth.peak == body.peak
    assert cloth.outline[-1][1] == body.outline[-1][1]


def test_the_line_under_the_bust_sits_under_it_and_fades_in():
    """No line without a bust; with one, a tapered shape under each breast that
    reaches the tunic's side, stays inside the torso and below the fullest
    point, and whose thickness grows with the bust up to 0.5 rather than
    appearing whole (`docs/bust-plan.md`, step 4)."""
    p = replace(PRESETS["satoko"], bust=0.0)
    assert character._bust_lines(character.skeleton_for(p), p) == ""
    thickness = []
    for v in (0.1, 0.25, 0.5, 1.0):
        q = replace(p, bust=v)
        sk = character.skeleton_for(q)
        lines = character._bust_lines(sk, q)
        assert lines.count("<path") == 2 and 'stroke="none"' in lines
        d = re.search(r'd="([^"]+)"', lines).group(1)
        nums = [float(n) for n in re.findall(r"-?\d+\.?\d*", d)]
        xs, ys = nums[0::2], nums[1::2]
        side = sk.head_cx - character._bust_shape(sk, drape=True).peak[0]
        assert all(side - 1 < x < sk.head_cx for x in xs)
        assert min(xs) < side + 0.1 * sk.head_r, "it does not reach the side"
        assert all(y >= sk.bust_y for y in ys)
        # Thickest across the middle of the ring: its two walls' widest gap.
        half = len(xs) // 2
        thickness.append(max(abs(ys[k] - ys[-1 - k]) for k in range(half)))
    assert thickness[0] < thickness[1] < thickness[2]
    assert abs(thickness[2] - thickness[3]) < 0.25


@pytest.mark.parametrize("name", ["satoko", "satoshi"])
def test_the_bare_body_is_closed_where_it_shows(name):
    """Where nothing covers the body (`docs/bust-plan.md`, step 3c): the neck's
    lines stop at the body's shoulder line instead of running down the chest,
    and the torso runs down to the hip, meeting the legs, except for the small
    notch where they part."""
    p = PRESETS[name]
    sk = character.skeleton_for(p)
    neck = character._neck(sk, p)
    ends = [float(v) for v in re.findall(r'y2="([\d.]+)"', neck)]
    body_top = sk.shoulder_y + 2 * character._stroke_w(sk) * character._BODY_INSET
    assert ends and all(abs(e - body_top) < 0.11 for e in ends)
    d = re.search(r'd="([^"]+)"', character._torso(sk, p)).group(1)
    ys = [float(v) for v in re.findall(r"-?\d+\.?\d*", d)][1::2]
    assert max(ys) >= sk.hip_y


def _tunic_off(p: CharacterParams) -> CharacterParams:
    return replace(p, outfit=replace(p.outfit, tunic_color=None))


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_every_preset_renders_with_its_tunic_off(name):
    """The tunic is optional like every other garment (`docs/bare-body-plan.md`,
    step 2): off, it draws nothing and nothing that reads it gets a `None`."""
    p = _tunic_off(PRESETS[name])
    svg = render_character(p, character.skeleton_for(p))
    assert '"None"' not in svg


def test_the_tunic_s_own_parts_go_with_it():
    """The placket and the chest pockets are the tunic's: with it off they are
    not left on bare skin (the audit found Tenno's placket and pockets floating
    on his chest)."""
    for name in ("tenno", "krista"):
        p = _tunic_off(PRESETS[name])
        sk = character.skeleton_for(p)
        for part in (character._tunic, character._placket, character._chest_pockets):
            assert part(sk, p) == ""
    worn = PRESETS["tenno"]
    sk = character.skeleton_for(worn)
    assert character._placket(sk, worn) and character._chest_pockets(sk, worn)


def test_the_bare_breasts_are_their_own_shape_over_the_arms():
    """With nothing worn over them the breasts are drawn whole, their own filled
    shape and outline (`docs/bare-body-plan.md`, step 4b), in the tunic's
    line's place, and at the chibi the chest is redrawn over the arms masked to
    them: the bent side outline built for cloth dented bare. The outline starts
    at the arm's own inner top corner, so arm, armpit and breast are one line."""
    p = _tunic_off(PRESETS["krista"])
    sk = character.skeleton_for(p)
    breasts = character._bust_lines(sk, p)
    assert breasts == character._bare_breasts(sk, p)
    assert f'fill="{p.skin_tone}"' in breasts
    centre_top, _, _, _ = character._arm_line(sk)
    corner = centre_top - sk.arm_half_w
    start = character._bare_breast_spine(sk, p)[0]
    assert abs(start[0] - corner) < 1e-9
    over = character._bust_over_arms(sk, p, breasts)
    assert "<mask" in over and breasts in over
    flat = _tunic_off(PRESETS["satoshi"])
    sk = character.skeleton_for(flat)
    assert character._bust_over_arms(sk, flat, "") == ""
    assert character._bust_lines(sk, flat) == ""


def test_the_underwear_top_is_drawn_bare_with_a_bust_or_when_asked():
    """The base layer's top (`docs/bare-body-plan.md`, step 3): only with the
    tunic off, so no clothed figure moves; with a bust by itself, and without
    one only when `underwear_top` asks. In `underwear_color`, like the
    underpants, so the two halves agree."""
    krista = PRESETS["krista"]
    sk = character.skeleton_for(krista)
    assert character._underwear_top(sk, krista) == ""
    bare = _tunic_off(krista)
    top = character._underwear_top(sk, bare)
    assert f'fill="{bare.outfit.underwear_color}"' in top
    man = _tunic_off(PRESETS["satoshi"])
    sk = character.skeleton_for(man)
    assert character._underwear_top(sk, man) == ""
    asked = replace(man, outfit=replace(man.outfit, underwear_top=True))
    assert f'fill="{asked.outfit.underwear_color}"' in character._underwear_top(sk, asked)
    recoloured = replace(bare, outfit=replace(bare.outfit, underwear_color="#123456"))
    assert render_character(recoloured).count('fill="#123456"') >= 2


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_the_underpants_have_height_on_every_preset(name):
    """The hem reads the real knee (`_real_knee_y`): on the long-torso profile
    the knee landmark is above the hip, and the underpants came out with the
    hem above the top, gone entirely on every untucked figure. Trousers off
    too: under them there are none to draw."""
    p = _tunic_off(PRESETS[name])
    p = replace(p, outfit=replace(p.outfit, trouser_color=None))
    svg = render_character(p)
    color = p.outfit.underwear_color
    paths = re.findall(r'<path d="([^"]+)" fill="' + re.escape(color) + '"', svg)
    assert paths
    ys = [float(v) for v in re.findall(r"-?\d+\.?\d*", paths[-1])][1::2]
    assert max(ys) - min(ys) > character.skeleton_for(p).head_r * 0.1


def test_the_bare_arm_has_no_cap_and_no_line_across_its_top():
    """With the tunic off the arm takes no cap's slant and draws no line
    across its top: the shoulder rounds over it (`docs/bare-body-plan.md`,
    step 4c). A tunic keeps both."""
    no_sleeves = replace(PRESETS["gero"].outfit, coat_color=None, undersleeve_color=None)
    worn = replace(PRESETS["gero"], outfit=no_sleeves)
    bare = _tunic_off(worn)
    sk = character.skeleton_for(bare)
    assert character._sleeve_under_cap(sk, worn)
    assert not character._sleeve_under_cap(sk, bare)
    arms = character._arms(sk, bare)
    assert 'fill="none"' in arms and f'fill="{bare.skin_tone}" stroke="none"' in arms
    torso = character._torso(sk, bare)
    ys = [float(v) for v in re.findall(r"-?\d+\.?\d*", re.search(r'd="([^"]+)"', torso).group(1))][
        1::2
    ]
    cuff_y = character._sleeve_hem_y(sk)
    assert any(y > cuff_y + character._stroke_w(sk) for y in ys if y < sk.waist_y)


def test_the_bare_crotch_reads_the_real_knee():
    """With the tunic off the legs part below the hip, off the real knee
    (`docs/bare-body-plan.md`, step 4d): on the long-torso profile the knee
    landmark is above the hip and the legs parted at the hip itself. Clothed,
    the landmark as before."""
    worn = PRESETS["satoko"]
    sk = character.skeleton_for(worn)
    assert character._crotch_y(sk, worn) < sk.hip_y
    bare = _tunic_off(worn)
    assert character._crotch_y(sk, bare) > sk.hip_y + character._stroke_w(sk) * 4


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_every_preset_renders_barefoot(name):
    """The boots are optional (`docs/bare-body-plan.md`, step 5): off, each
    foot is bare, in the skin tone, and nothing reads a `None`."""
    p = PRESETS[name]
    p = replace(p, outfit=replace(p.outfit, boot_color=None))
    sk = character.skeleton_for(p)
    svg = render_character(p, sk)
    assert '"None"' not in svg
    foot = character._boot(sk, p, sk.head_cx, sk.leg_half_w, 1)
    assert f'fill="{p.skin_tone}"' in foot and "laces" not in foot


def test_the_chest_lines_and_the_navel_are_bare_only():
    """The chest's line work and the navel (`docs/bare-body-plan.md`, step 6):
    both only with the tunic off; the chest lines only with no bust, which
    replaces them, and only with a chest to draw; the navel on every bare
    figure."""
    man = PRESETS["gero"]
    sk = character.skeleton_for(man)
    assert man.chest > 0
    assert character._chest_lines(sk, man) == "" and character._navel(sk, man) == ""
    bare = _tunic_off(man)
    assert character._chest_lines(sk, bare) and character._navel(sk, bare)
    flat = replace(bare, chest=0.0)
    assert character._chest_lines(sk, flat) == ""
    woman = _tunic_off(PRESETS["krista"])
    sk = character.skeleton_for(woman)
    assert character._chest_lines(sk, replace(woman, chest=1.0)) == ""
    assert character._navel(sk, woman)


def test_the_blush_warms_on_dark_skin_and_holds_on_the_cast():
    """The blush follows the skin (`docs/bare-body-plan.md`, step 7): the fixed
    pink on light skin, every preset's included, and a warmer, stronger rose
    reached gradually on dark skin, where the fixed pink read as a bruise."""
    for p in PRESETS.values():
        assert character._blush(p.skin_tone) == (character._BLUSH, character._BLUSH_OPACITY)
    assert character._blush("#442617") == (character._BLUSH_DARK, character._BLUSH_DARK_OPACITY)
    mid, opacity = character._blush("#a8704a")
    assert mid not in (character._BLUSH, character._BLUSH_DARK)
    assert character._BLUSH_OPACITY < opacity < character._BLUSH_DARK_OPACITY


def test_the_tunic_s_line_follows_the_bare_breast():
    """The tunic's line under the bust is drawn on the bare breast's own
    ellipse (`docs/tunic-bust-plan.md`, T2), so the bust reads the same with
    the tunic on or off: its lowest point is the ellipse's, and its outer end
    starts at the fullest point, where the bare outline is widest."""
    p = PRESETS["krista"]
    sk = character.skeleton_for(p)
    _, _, yp, ry = character._breast_ellipse(sk, 0.0)
    line = character._bust_lines(sk, p)
    ys = [float(v) for v in re.findall(r"-?\d+\.?\d*", re.search(r'd="([^"]+)"', line).group(1))][
        1::2
    ]
    sw = character._stroke_w(sk)
    assert abs(max(ys) - (yp + ry)) < sw
    assert abs(min(ys) - yp) < sw


def test_the_outer_layers_answer_the_bust():
    """An open coat's front edges bow out over a bust and a robe front carries
    the tunic's line, lighter, under the breast it covers
    (`docs/tunic-bust-plan.md`, outer layers). Without a bust neither changes."""
    reika = PRESETS["reika"]
    sk = character.skeleton_for(reika)
    fold = character._bust_fold(sk, character._ROBE_BUST_LINE, sides=(-1,))
    assert fold and fold in character._robe_front(sk, reika)
    assert character._bust_fold(sk, 1.0, sides=(-1,)) != fold
    flat = replace(reika, bust=0.0)
    sk_flat = character.skeleton_for(flat)
    assert character._bust_fold(sk_flat) == ""
    kyoko = PRESETS["kyoko"]
    sk = character.skeleton_for(kyoko)
    flat = replace(kyoko, bust=0.0)
    assert character._coat(sk, kyoko) != character._coat(character.skeleton_for(flat), flat)


def test_an_open_coat_carries_the_line_on_its_panels_only():
    """An open coat over a bust carries the tunic's line, lighter, masked to
    its panels (`docs/tunic-bust-plan.md`, outer layers): drawn before the
    lab coat's lapels so they lie over it, and never in the opening. Without a
    bust, nothing."""
    keiko = PRESETS["keiko"]
    sk = character.skeleton_for(keiko)
    coat = character._draw_cut(sk, character.COAT_CUTS["lab_coat"], keiko.outfit.coat_color)
    line = coat.index('mask="url(#coat-bust-')
    paths = [
        m.start()
        for m in re.finditer(r'<path d="[^"]+" fill="' + re.escape(keiko.outfit.coat_color), coat)
    ]
    assert len(paths) == 4 and paths[1] < line < paths[2]
    flat = replace(keiko, bust=0.0)
    sk_flat = character.skeleton_for(flat)
    assert "coat-bust-" not in character._draw_cut(
        sk_flat, character.COAT_CUTS["lab_coat"], "#ffffff"
    )
    kyoko = PRESETS["kyoko"]
    assert "coat-bust-" in character._coat(character.skeleton_for(kyoko), kyoko)


def test_an_old_link_loads_as_the_tall_chibi():
    """A link from before the realistic build and the compressed chibi were
    retired (`docs/tall-chibi-plan.md`, R1), carrying another `heads` or
    `body: null`, loads as the default tall chibi rather than failing."""
    from anime_character_creator.urlstate import params_from_dict, params_to_dict

    old = params_to_dict(PRESETS["satoko"])
    old["heads"] = 6.0
    old["body"] = None
    p = params_from_dict(old)
    assert p.body == CharacterParams().body
    assert render_character(p) == render_character(PRESETS["satoko"])
