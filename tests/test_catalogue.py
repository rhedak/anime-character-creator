"""Guards for `catalogue.py`, so the web tool's list of what is public cannot
silently drift from what `CharacterParams`, `Outfit` and `HAIRSTYLES` actually
are.

Most of this is already enforced at import time, by the asserts next to
`GARMENTS` and `COLORS` in `catalogue.py` itself: a field name that stops
existing fails every test in this file just by collection. What is here on
top of that is the checklist `docs/web-gui-plan.md` sets out for this module:
every range actually renders, every starting point is real, and the
committed JSON is current.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import fields, replace

import pytest

from anime_character_creator import (
    BUILDS,
    NEUTRAL_BASES,
    PRESETS,
    CharacterParams,
    FaceStyle,
    Outfit,
    build_skeleton,
    render_character,
)
from anime_character_creator.catalogue import (
    BUILD,
    COLORS,
    FACE_BOOLS,
    FACE_RANGES,
    FACE_SCAR,
    FACE_SELECTS,
    GARMENTS,
    HAIR_KNOT,
    HAIR_LENGTH,
    HAIR_TAIL,
    HAIRSTYLE_LABELS,
    build_catalogue,
    to_json,
)


def test_every_color_field_exists_on_character_params() -> None:
    names = {f.name for f in fields(CharacterParams)}
    for c in COLORS:
        assert c.field in names


def test_every_garment_field_exists_on_outfit() -> None:
    names = {f.name for f in fields(Outfit)}
    for g in GARMENTS:
        assert g.color.field in names
        for r in g.ranges:
            assert r.field in names
        for b in g.bools:
            assert b.field in names


def test_every_face_field_exists_on_facestyle() -> None:
    names = {f.name for f in fields(FaceStyle)}
    for r in FACE_RANGES:
        assert r.field in names
    for b in FACE_BOOLS:
        assert b.field in names
    for s in FACE_SELECTS:
        assert s.field in names


def test_every_face_select_option_is_a_real_eye_style_or_scar() -> None:
    """A select's values have to be values the generator actually reads.

    The eye-style select's values come from `EYESTYLES` itself, so this is
    mainly guarding the scar side: it can only offer what `_scar` accepts.
    """
    from anime_character_creator import EYESTYLES

    eye_style = next(s for s in FACE_SELECTS if s.field == "eye_style")
    assert {v for v, _l in eye_style.options} == set(EYESTYLES)
    scar = next(s for s in FACE_SELECTS if s.field == "scar_side")
    assert {v for v, _l in scar.options} == {0, -1, 1}


def test_hair_tail_and_knot_fields_exist_on_character_params() -> None:
    names = {f.name for f in fields(CharacterParams)}
    assert HAIR_TAIL.field in names
    assert HAIR_KNOT.field in names


def test_build_field_exists_on_character_params() -> None:
    names = {f.name for f in fields(CharacterParams)}
    assert BUILD.field in names


def test_build_options_are_exactly_the_named_builds() -> None:
    """`BUILD` offers the two entries in `BUILDS` and nothing else: never the
    continuous slider `docs/web-gui-plan.md`'s "Knobs that are traps" warns
    against."""
    assert {value for value, _label in BUILD.options} == set(BUILDS.values())


@pytest.mark.parametrize("value,_label", BUILD.options)
def test_build_options_render(value: float, _label: str) -> None:
    p = replace(CharacterParams(), heads=value)
    svg = render_character(p, build_skeleton(heads=value, frame=p.frame))
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")


def test_every_hairstyle_label_is_a_real_hairstyle() -> None:
    from anime_character_creator import HAIRSTYLES

    assert set(HAIRSTYLE_LABELS) == set(HAIRSTYLES)


def test_every_cast_starting_point_is_in_presets() -> None:
    cat = build_catalogue()
    for entry in cat["starting_points"]["cast"]:
        assert entry["id"] in PRESETS


def test_every_base_starting_point_is_a_neutral_base() -> None:
    cat = build_catalogue()
    for entry in cat["starting_points"]["bases"]:
        assert entry["id"] in NEUTRAL_BASES
    # And the reverse: nothing in NEUTRAL_BASES is missing from the catalogue,
    # which is the direction a forgotten export would fail silently in.
    listed = {entry["id"] for entry in cat["starting_points"]["bases"]}
    assert listed == set(NEUTRAL_BASES)


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_hair_length_extremes_render(build: str) -> None:
    for value in (HAIR_LENGTH.lo, HAIR_LENGTH.hi):
        p = replace(CharacterParams(), hair_length=value)
        svg = render_character(p, build_skeleton(heads=BUILDS[build], frame=p.frame))
        ET.fromstring(svg)


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_hair_tail_extremes_render(build: str) -> None:
    for value in (HAIR_TAIL.lo, HAIR_TAIL.hi):
        p = replace(CharacterParams(), hair_tail=value)
        svg = render_character(p, build_skeleton(heads=BUILDS[build], frame=p.frame))
        ET.fromstring(svg)


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_hair_knot_renders(build: str) -> None:
    p = replace(CharacterParams(), hair_knot=True)
    svg = render_character(p, build_skeleton(heads=BUILDS[build], frame=p.frame))
    ET.fromstring(svg)


def _turned_on(base: Outfit, field: str) -> Outfit:
    """`base` with one more optional color set, so a companion range on that
    slot actually draws something rather than being silently skipped."""
    if getattr(base, field) is not None:
        return base
    return replace(base, **{field: "#5a5a5a"})


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_every_garment_range_extreme_renders(build: str) -> None:
    sk_args = {"heads": BUILDS[build]}
    for g in GARMENTS:
        if not g.ranges:
            continue
        outfit = _turned_on(Outfit(), g.color.field)
        for r in g.ranges:
            for value in (r.lo, r.hi):
                outfit_at = replace(outfit, **{r.field: value})
                p = CharacterParams(outfit=outfit_at)
                svg = render_character(p, build_skeleton(frame=p.frame, **sk_args))
                root = ET.fromstring(svg)
                assert root.tag.endswith("svg")


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_face_range_extremes_render(build: str) -> None:
    sk = build_skeleton(heads=BUILDS[build])
    for r in FACE_RANGES:
        for value in (r.lo, r.hi):
            p = CharacterParams(face=replace(FaceStyle(), **{r.field: value}))
            svg = render_character(p, sk)
            root = ET.fromstring(svg)
            assert root.tag.endswith("svg")


@pytest.mark.parametrize("build", sorted(BUILDS))
def test_face_scar_options_render(build: str) -> None:
    sk = build_skeleton(heads=BUILDS[build])
    for value, _label in FACE_SCAR.options:
        p = CharacterParams(face=replace(FaceStyle(), scar_side=value))
        svg = render_character(p, sk)
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg")


def test_catalogue_json_matches_ref_out() -> None:
    """`ref-out/catalogue.json` is committed the way the SVGs are: current on
    disk rather than regenerated only when something happens to read it.
    Guarded the same way `refresh-ref-out.sh --check` guards those, run
    `./refresh-catalogue.sh` when this fails."""
    from pathlib import Path

    committed = (Path(__file__).resolve().parent.parent / "ref-out" / "catalogue.json").read_text()
    assert committed == to_json(), "ref-out/catalogue.json is stale; run ./refresh-catalogue.sh"
