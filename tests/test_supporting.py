"""The supporting cast draws, and stays out of the presets the web tool offers."""

from __future__ import annotations

import pytest

from anime_character_creator import PRESETS, render_character
from anime_character_creator.catalogue import _base_points, _cast_points
from anime_character_creator.supporting import DISPLAY_NAMES, SUPPORTING


@pytest.mark.parametrize("name", sorted(SUPPORTING))
def test_a_supporting_character_renders(name: str) -> None:
    svg = render_character(SUPPORTING[name])
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    assert svg == render_character(SUPPORTING[name])


def test_every_supporting_character_has_a_display_name() -> None:
    assert set(DISPLAY_NAMES) == set(SUPPORTING)


def test_none_of_them_is_a_preset_or_offered_by_the_web_tool() -> None:
    """The owner's condition: there are enough starting points already."""
    assert not set(SUPPORTING) & set(PRESETS)
    assert not set(SUPPORTING) & {sp.id for sp in (*_cast_points(), *_base_points())}
