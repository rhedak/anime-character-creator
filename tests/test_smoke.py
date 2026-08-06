"""Enough of a test to catch a broken package, not a substitute for looking.

Whether a shape is *right* is decided by eye against `ref/`, which no assertion
can stand in for. What these do check is that the package imports, that every
named character renders at every named build, and that the four renders in
`ref-out/` are still what the code produces, which is the thing a refactor
breaks silently.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from anime_character_creator import (
    BUILDS,
    HAIRSTYLES,
    PRESETS,
    CharacterParams,
    build_skeleton,
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
