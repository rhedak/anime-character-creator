"""Every id a drawing defines is defined once, and every reference to one resolves, in both finishes."""

from __future__ import annotations

import collections
import re
from dataclasses import replace

import pytest

from anime_character_creator import PRESETS, render_character
from anime_character_creator.presets import NEUTRAL_BASES

EVERYONE = {**PRESETS, **NEUTRAL_BASES}


@pytest.mark.parametrize("finish", ["flat", "soft"])
@pytest.mark.parametrize("name", sorted(EVERYONE))
def test_ids_are_defined_once_and_every_reference_resolves(name: str, finish: str) -> None:
    svg = render_character(replace(EVERYONE[name], finish=finish))
    ids = re.findall(r'\bid="([^"]+)"', svg)
    assert [i for i, n in collections.Counter(ids).items() if n > 1] == []
    refs = re.findall(r"url\(#([^)]+)\)", svg) + re.findall(r'href="#([^"]+)"', svg)
    assert [r for r in refs if r not in ids] == []
