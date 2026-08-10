"""`urlstate` (a character as a URL) and `attribution` (the metadata block
`render_character(metadata=True)` can embed), and the guarantee the plan's
licensing section rests on: a downloaded file can prove where it came from.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import replace

import pytest

from anime_character_creator import NEUTRAL_BASES, PRESETS, CharacterParams, render_character
from anime_character_creator.attribution import NOVEL_URL, REPOSITORY_URL, TOOL_URL
from anime_character_creator.urlstate import character_url, decode_params, encode_params


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_presets_round_trip_through_a_url(name: str) -> None:
    p = PRESETS[name]
    assert decode_params(encode_params(p)) == p


@pytest.mark.parametrize("name", sorted(NEUTRAL_BASES))
def test_neutral_bases_round_trip_through_a_url(name: str) -> None:
    p = NEUTRAL_BASES[name]
    assert decode_params(encode_params(p)) == p


def test_encoding_is_deterministic() -> None:
    p = PRESETS["satoko"]
    assert encode_params(p) == encode_params(replace(p))


@pytest.mark.parametrize(
    "garbage",
    [
        "not-valid-base64!!!",
        "",
        "eyJub3RfYV9maWVsZCI6MX0",  # valid base64/JSON, not a CharacterParams field
    ],
)
def test_decode_rejects_what_it_did_not_encode(garbage: str) -> None:
    with pytest.raises(ValueError):
        decode_params(garbage)


def test_character_url_carries_the_base_and_the_encoding() -> None:
    p = PRESETS["krista"]
    url = character_url(p, TOOL_URL)
    assert url.startswith(f"{TOOL_URL}?c=")
    assert decode_params(url.split("?c=", 1)[1]) == p


def test_metadata_is_off_by_default_and_does_not_change_the_document() -> None:
    p = PRESETS["krista"]
    assert render_character(p) == render_character(p, metadata=False)
    assert "<metadata>" not in render_character(p)


def test_metadata_embeds_a_working_character_link() -> None:
    p = PRESETS["krista"]
    svg = render_character(p, metadata=True)
    root = ET.fromstring(svg)
    ns = "{http://www.w3.org/2000/svg}"
    md = root.find(f"{ns}metadata")
    assert md is not None
    link = md.findtext(f"{ns}character")
    assert link is not None and link.startswith(TOOL_URL)
    assert decode_params(link.split("?c=", 1)[1]) == p
    assert md.findtext(f"{ns}source") == TOOL_URL
    assert md.findtext(f"{ns}repository") == REPOSITORY_URL
    assert md.findtext(f"{ns}novel") == NOVEL_URL


def test_metadata_survives_a_character_with_no_optional_layers() -> None:
    """The bare-minimum character, nothing set that could break the escaping."""
    svg = render_character(CharacterParams(), metadata=True)
    ET.fromstring(svg)
