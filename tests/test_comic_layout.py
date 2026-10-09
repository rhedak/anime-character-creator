"""The comic strip's layout: placement, clipping, namespacing and determinism."""

from __future__ import annotations

import re
from collections import Counter

import pytest

from anime_character_creator import PRESETS
from anime_character_creator.comic import Panel, Placement, Strip, render_panel, render_strip


def _strip() -> Strip:
    two = Panel(
        700,
        300,
        placements=(
            Placement(PRESETS["chiyo"], 200, 280, 260),
            Placement(PRESETS["satoshi"], 480, 280, 260, flip=True),
        ),
    )
    one = Panel(700, 200, placements=(Placement(PRESETS["satoshi"], 350, 400, 500),))
    return Strip((two, one))


def test_a_strip_is_deterministic() -> None:
    assert render_strip(_strip()) == render_strip(_strip())


def test_no_id_is_defined_twice_on_a_page() -> None:
    """Three figures and two panels, and every id on the page is its own."""
    ids = Counter(re.findall(r'\bid="([^"]+)"', render_strip(_strip())))
    assert ids, "the control needs ids to check"
    assert [i for i, n in ids.items() if n > 1] == []


def test_every_reference_has_a_definition() -> None:
    svg = render_strip(_strip())
    defined = set(re.findall(r'\bid="([^"]+)"', svg))
    assert set(re.findall(r"url\(#([^)]+)\)", svg)) <= defined


def test_a_flipped_figure_is_mirrored_and_an_unflipped_one_is_not() -> None:
    svg = render_panel(_strip().panels[0])
    scales = re.findall(r"scale\((-?[\d.]+)[ )]", svg)
    assert [s.startswith("-") for s in scales] == [False, True]


def test_a_figure_may_stand_outside_the_panel_and_is_clipped_to_it() -> None:
    svg = render_panel(_strip().panels[1])
    assert 'clip-path="url(#panel-0)"' in svg
    assert 'id="panel-0"' in svg


def test_the_strip_is_as_tall_as_its_panels_gutters_and_margins() -> None:
    s = _strip()
    expected = 2 * s.margin + sum(p.height for p in s.panels) + s.gutter
    assert f'height="{expected:.0f}"' in render_strip(s)


def test_a_panel_too_wide_for_the_strip_is_refused() -> None:
    with pytest.raises(ValueError, match="does not fit"):
        render_strip(Strip((Panel(900, 100),)))


def test_an_empty_strip_is_just_paper() -> None:
    assert "<g" not in render_strip(Strip(()))
