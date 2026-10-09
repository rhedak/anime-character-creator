"""The open mouth and the comic's first expressions."""

from __future__ import annotations

from dataclasses import replace

from anime_character_creator import EXPRESSIONS, PRESETS, render_character


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
    for name in ("startled", "exasperated", "alert", "smile"):
        assert render_character(EXPRESSIONS[name].applied_to(p)) != render_character(p), name
