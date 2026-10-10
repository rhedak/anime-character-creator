"""The lettering checks: each one finds what it is for, and a clean panel finds nothing."""

from __future__ import annotations

import pytest

pytest.importorskip("uharfbuzz", reason="the optional `comic` extra")

from anime_character_creator import PRESETS
from anime_character_creator.comic import Panel, Placement, Strip
from anime_character_creator.comic.bubbles import Bubble
from anime_character_creator.comic.checks import check_panel, check_strip


def _panel(*bubbles: Bubble, figures: bool = True) -> Panel:
    placements = (Placement(PRESETS["chiyo"], 560, 440, 300),) if figures else ()
    return Panel(752, 460, placements=placements, bubbles=tuple(bubbles))


def _says(problems: list[str], fragment: str) -> bool:
    return any(fragment in p for p in problems)


CLEAN = Bubble("Hello there.", 200, 90, 220, tail_to=(520, 190))


def test_a_clean_panel_has_nothing_to_report() -> None:
    assert check_panel(_panel(CLEAN)) == []


def test_a_bubble_over_a_face_is_found() -> None:
    head = _panel().heads()[0]
    covering = Bubble("Hello there.", head[0], head[1], 220)
    assert _says(check_panel(_panel(covering)), "covers the face")


def test_a_bubble_at_the_frame_is_found() -> None:
    assert _says(check_panel(_panel(Bubble("Hello there.", 60, 60, 220))), "edge")


def test_overlapping_bubbles_and_crossing_tails_are_found() -> None:
    a = Bubble("One thing.", 200, 90, 220, tail_to=(480, 200))
    b = Bubble("Another thing.", 230, 110, 220, tail_to=(100, 200))
    problems = check_panel(_panel(a, b, figures=False))
    assert _says(problems, "overlap")
    c = Bubble("Left.", 150, 80, 200, tail_to=(450, 320))
    d = Bubble("Right.", 450, 80, 200, tail_to=(150, 320))
    assert _says(check_panel(_panel(c, d, figures=False)), "cross")


def test_reading_order_is_top_left_first() -> None:
    first_but_lower = Bubble("Said first.", 200, 300, 200)
    second_but_higher = Bubble("Said second.", 200, 90, 200)
    assert _says(
        check_panel(_panel(first_but_lower, second_but_higher, figures=False)), "read after"
    )
    left_then_right = [Bubble("A.", 150, 100, 160), Bubble("B.", 520, 100, 160)]
    assert check_panel(_panel(*left_then_right, figures=False)) == []
    right_then_left = [Bubble("A.", 520, 100, 160), Bubble("B.", 150, 100, 160)]
    assert _says(check_panel(_panel(*right_then_left, figures=False)), "read after")


def test_too_many_bubbles_too_many_sentences_and_type_too_small_are_found() -> None:
    four = [Bubble(f"B{i}.", 100 + 170 * i, 80, 130) for i in range(4)]
    assert _says(check_panel(_panel(*four, figures=False)), "more than 3")
    long = Bubble("One. Two. Three. Four. Five.", 300, 100, 400)
    assert _says(check_panel(_panel(long, figures=False)), "5 sentences")
    small = Bubble("Tiny.", 300, 100, 200, size=12)
    assert _says(check_panel(_panel(small, figures=False)), "under")


def test_a_strip_names_the_panel() -> None:
    bad = _panel(Bubble("Hello there.", 60, 60, 220))
    problems = check_strip(Strip((_panel(CLEAN), bad)))
    assert problems and all(p.startswith("panel 2:") for p in problems)


def test_the_shape_is_the_one_the_drawing_uses() -> None:
    import re

    b = Bubble("Easy. I only wanted to know.", 300, 120, 240, tail_to=(300, 300))
    cx, cy, rx, ry = b.shape()
    # An ellipse centred on the bubble, drawn with a tail, so the path starts and ends on it.
    assert (cx, cy) == (300, 120) and rx > ry > 0
    assert re.search(r'<path d="M', b.svg())


def _two(
    h_a: float, h_b: float, feet_a: float, feet_b: float, horizon: float | None = None
) -> Panel:
    a = Placement(PRESETS["chiyo"], 200, feet_a, h_a)
    b = Placement(PRESETS["satoshi"], 500, feet_b, h_b)
    return Panel(752, 460, placements=(a, b), horizon=horizon)


def test_two_figures_at_one_depth_must_be_one_size() -> None:
    assert check_panel(_two(340, 340, 440, 440)) == []
    assert _says(check_panel(_two(300, 430, 440, 440)), "head sizes")


def test_a_figure_further_back_may_be_smaller_by_what_the_horizon_says() -> None:
    # Feet 90 and 190 below a horizon at y 250: the one at the back is 190/290 as large.
    far, near = 440, 540
    ok = _two(340 * 190 / 290, 340, 440, 540, horizon=250)
    assert far - 250 == 190 and near - 250 == 290
    assert check_panel(ok) == []
    # The same pair drawn at the back's feet but the front's size is named.
    assert _says(check_panel(_two(340, 340, 440, 540, horizon=250)), "head sizes")


def test_feet_above_the_horizon_are_named() -> None:
    assert _says(check_panel(_two(300, 340, 200, 440, horizon=250)), "above the horizon")


def test_a_lone_figure_has_nothing_to_compare() -> None:
    assert (
        check_panel(Panel(752, 460, placements=(Placement(PRESETS["chiyo"], 200, 440, 300),))) == []
    )
