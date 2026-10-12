"""The open mouth and the comic's first expressions."""

from __future__ import annotations

from dataclasses import replace

from anime_character_creator import EXPRESSIONS, PRESETS, render_character
from anime_character_creator.character import skeleton_for


def test_a_shut_mouth_is_unchanged_by_the_open_mouth_existing() -> None:
    """`mouth_open` defaults to 0: the shut line, drawn exactly as before."""
    p = PRESETS["chiyo"]
    assert render_character(p) == render_character(replace(p, face=replace(p.face, mouth_open=0.0)))


def test_an_open_mouth_is_a_filled_shape_and_a_shut_one_is_a_line() -> None:
    p = PRESETS["satoshi"]
    shut = render_character(p)
    opened = render_character(replace(p, face=replace(p.face, mouth_open=0.8)))
    assert opened != shut
    assert "#6b2f2f" in opened and "#6b2f2f" not in shut


def test_startled_opens_the_mouth_and_leaves_what_it_does_not_name() -> None:
    p = PRESETS["satoshi"]
    startled = EXPRESSIONS["startled"].applied_to(p)
    assert startled.face.mouth_open > 0
    assert startled.face.eye_size == p.face.eye_size  # a mood is a delta, not a new face
    assert startled.face.scar_side == p.face.scar_side


def test_the_comic_expressions_exist_and_each_changes_the_face() -> None:
    p = PRESETS["satoshi"]
    for name in ("startled", "exasperated", "alert", "smile", "menacing", "unyielding", "at_ease"):
        assert render_character(EXPRESSIONS[name].applied_to(p)) != render_character(p), name


def test_gaze_defaults_to_straight_ahead_and_moves_only_the_eyes() -> None:
    p = PRESETS["satoshi"]
    straight = render_character(p)
    assert straight == render_character(replace(p, face=replace(p.face, gaze=0.0)))
    right = render_character(replace(p, face=replace(p.face, gaze=1.0)))
    left = render_character(replace(p, face=replace(p.face, gaze=-1.0)))
    assert len({straight, right, left}) == 3
    # Nothing but the eyes changes: the same shapes, only the iris's own circles move.
    assert straight.count("<circle") == right.count("<circle") == left.count("<circle")


def _irises(svg: str) -> list[tuple[float, float]]:
    """The iris rim of the left and then the right eye as `(cx, r)`: the first circle in each eye's clipped group."""
    import re

    out = []
    for side in ("l", "r"):
        group = svg[svg.index(f'clip-path="url(#eye-{side})"') :]
        x, r = re.search(r'<circle cx="([\d.]+)" cy="[\d.]+" r="([\d.]+)"', group).groups()
        out.append((float(x), float(r)))
    return out


def test_a_look_to_the_side_keeps_the_iris_inside_the_eye_and_moves_both_eyes_together() -> None:
    from anime_character_creator.character import _EYE_ASPECT, _eye_placement, skeleton_for

    for name in ("risa", "satoshi"):  # risa's irises start against the nose; satoshi's centred
        p = PRESETS[name]
        sk = skeleton_for(p)
        dx, _ey, er, f = _eye_placement(sk, p)
        centre = sk.head_cx
        straight = _irises(render_character(p))
        for look in (-1.0, -0.8, 0.8, 1.0):
            svg = render_character(replace(p, face=replace(p.face, gaze=look)))
            eyes = _irises(svg)
            for (cx, r), side in zip(eyes, (-1, 1), strict=True):
                room = er * f.eye_width * _EYE_ASPECT - r
                assert abs(cx - (centre + side * dx)) <= room + 0.15, (name, look, side)
            # Looking right moves both eyes right (or leaves one in the corner it is already in).
            moved = [cx - cx0 for (cx, _), (cx0, _) in zip(eyes, straight, strict=True)]
            assert all(m * look >= -0.15 for m in moved), (name, look, moved)


def test_an_opening_beyond_the_width_does_not_make_the_mouth_taller_than_wide() -> None:
    from anime_character_creator.character import _mouth_depth_share

    assert _mouth_depth_share(0.3) == 0.3 and _mouth_depth_share(0.8) == 0.8
    shares = [_mouth_depth_share(o / 10) for o in range(0, 21)]
    assert shares == sorted(shares)  # it never closes up again as the opening grows
    assert max(shares) < 1.0


def test_the_blush_sits_below_the_eye_it_is_next_to() -> None:
    import re

    from anime_character_creator.character import _eye_placement, skeleton_for

    for name in ("risa", "linnea", "satoshi"):
        p = replace(PRESETS[name], face=replace(PRESETS[name].face, blush=1.0))
        sk = skeleton_for(p)
        _dx, ey, er, f = _eye_placement(sk, p)
        top = [
            float(cy) - float(ry)
            for cy, ry in re.findall(
                r'<ellipse cx="[\d.]+" cy="([\d.]+)" rx="[\d.]+" ry="([\d.]+)"', render_character(p)
            )
        ]
        assert top, name
        assert all(t >= ey + er * f.eye_lower_lid for t in top), name


def test_the_blush_is_clipped_to_the_face_outline() -> None:
    svg = render_character(replace(PRESETS["risa"], face=replace(PRESETS["risa"].face, blush=1.0)))
    assert 'clip-path="url(#blush-clip)"' in svg and 'id="blush-clip"' in svg
    group = svg[svg.index('clip-path="url(#blush-clip)"') :]
    assert group[: group.index("</g>")].count("<ellipse") == 2
    plain = render_character(
        replace(PRESETS["risa"], face=replace(PRESETS["risa"].face, blush=0.0))
    )
    assert "blush-clip" not in plain


def test_a_raised_arm_takes_the_blazers_sleeve_with_it() -> None:
    risa = PRESETS["risa"]
    rest = render_character(risa)
    assert "sleeve-cutaway" not in rest and "sleeve-cuff" not in rest  # at rest, drawn as before
    wave = render_character(replace(risa, right_arm_out=128.0))
    # the blazer's own sleeve is clipped away on that side, and the arm is drawn in the blazer's colour
    assert 'id="sleeve-cutaway"' in wave and 'clip-path="url(#sleeve-cutaway)"' in wave
    assert 'id="sleeve-cuff-l"' in wave and "sleeve-cuff-r" not in wave
    assert wave.count('fill="#4d5159"') > rest.count('fill="#4d5159"')
    cheer = render_character(replace(risa, right_arm_out=125.0, left_arm_out=125.0))
    assert 'id="sleeve-cuff-l"' in cheer and 'id="sleeve-cuff-r"' in cheer


def test_a_coat_whose_sleeves_are_the_arms_own_is_drawn_as_before_when_the_arm_is_raised() -> None:
    p = replace(PRESETS["keiko"], right_arm_out=128.0)
    svg = render_character(p)
    assert "sleeve-cutaway" not in svg and "sleeve-cuff" not in svg


def test_a_raised_blazer_arm_turns_at_the_shoulder_not_at_the_sleeve_hem() -> None:
    import re

    risa = PRESETS["risa"]
    sk = skeleton_for(risa)
    shoulder_limit = sk.head_cy + 2.0 * sk.head_r  # the sleeve hem it hung from is at 2.26 radii
    for kw in ({"right_arm_out": 128.0}, {"right_arm_out": 125.0, "left_arm_out": 125.0}):
        svg = render_character(replace(risa, **kw))
        pivots = {
            (float(x), float(y))
            for x, y in re.findall(r'<g transform="rotate\(1\d\d\.00 ([\d.]+) ([\d.]+)\)">', svg)
        }
        assert pivots and all(y < shoulder_limit for _, y in pivots), pivots
