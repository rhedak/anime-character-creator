"""Outline text, captions and speech bubbles."""

from __future__ import annotations

import re

import pytest

pytest.importorskip("uharfbuzz", reason="the optional `comic` extra")

from anime_character_creator import PRESETS
from anime_character_creator.comic import Panel, Placement, render_panel, text
from anime_character_creator.comic.bubbles import bubble_svg, caption_svg


def test_a_longer_line_measures_wider_and_a_bigger_size_scales_it() -> None:
    assert text.measure("Bread's what there is.", 20) > text.measure("Bread", 20)
    assert text.measure("Bread", 40) == pytest.approx(2 * text.measure("Bread", 20))


def test_wrap_keeps_every_line_inside_the_width_and_loses_no_word() -> None:
    sentence = "Easy. I only wanted to know if the kitchen had anything besides bread going."
    lines = text.wrap(sentence, 19, 200)
    assert len(lines) > 1
    assert all(text.measure(line, 19) <= 200 for line in lines)
    assert " ".join(lines) == sentence


def test_text_is_drawn_as_paths_not_as_text_elements() -> None:
    """The point of outlines: the same bytes whatever fonts the machine has."""
    svg = text.line_svg("There you are", 10, 40, 20)
    assert "<path" in svg and "<text" not in svg
    assert svg == text.line_svg("There you are", 10, 40, 20)


def test_a_caption_grows_with_its_text_and_reports_its_height() -> None:
    short_svg, short_h = caption_svg("A year.", 0, 0, 300)
    _, long_h = caption_svg("It had been very close to a year. " * 4, 0, 0, 300)
    assert long_h > short_h
    assert f'height="{short_h:.2f}"' in short_svg


def test_a_bubble_with_a_tail_is_one_closed_path_reaching_the_target() -> None:
    svg = bubble_svg("Sorry.", 200, 100, 200, tail_to=(260, 260))
    path = re.search(r'<path d="([^"]+)"', svg)
    assert path, "a tail is part of the outline, not a second shape"
    assert path.group(1).rstrip().endswith("Z")
    assert "260.00 260.00" in path.group(1)


def test_a_bubble_without_a_tail_or_aimed_inside_itself_is_a_plain_ellipse() -> None:
    assert "<ellipse" in bubble_svg("Sorry.", 200, 100, 200)
    assert "<ellipse" in bubble_svg("Sorry.", 200, 100, 200, tail_to=(200, 100))


def test_a_bubble_fits_its_words_inside_the_ellipse() -> None:
    svg = bubble_svg("Bread's what there is, if that suits you.", 300, 100, 260)
    rx = float(re.search(r'rx="([\d.]+)"', svg).group(1))
    assert rx * 2 >= max(
        text.measure(line, 19)
        for line in text.wrap("Bread's what there is, if that suits you.", 19, 260)
    )


def test_head_gives_the_head_where_the_figure_is_placed_and_mirrors_with_a_flip() -> None:
    plain = Placement(PRESETS["chiyo"], 300, 400, 300)
    flipped = Placement(PRESETS["chiyo"], 300, 400, 300, flip=True)
    x, y, r = plain.head()
    fx, fy, fr = flipped.head()
    assert (fy, fr) == (y, r)
    assert abs((x + fx) / 2 - 300) < 1.0  # mirrored about the centre line
    assert 0 < y < 400 and r > 0


def test_a_panel_with_bubbles_still_has_no_repeated_id() -> None:
    from collections import Counter

    chiyo = Placement(PRESETS["chiyo"], 300, 380, 300)
    hx, hy, hr = chiyo.head()
    panel = Panel(
        600,
        400,
        placements=(chiyo,),
        overlay=bubble_svg("Hello.", 150, 80, 200, tail_to=(hx, hy - hr)),
    )
    ids = Counter(re.findall(r'\bid="([^"]+)"', render_panel(panel)))
    assert [i for i, n in ids.items() if n > 1] == []
