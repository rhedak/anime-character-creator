"""`CharacterParams.finish`: "flat" is the house style and stays exactly as it was
(`ref-out/` is compared byte for byte by `refresh-ref-out.sh --check`), "soft" is an
opt-in experiment that adds gradients and tinted lines and moves no shape."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

import pytest

from anime_character_creator import FINISHES, PRESETS, CharacterParams, render_character
from anime_character_creator.generate import main

SVG = "{http://www.w3.org/2000/svg}"


def _soft(name: str, **kw: object) -> str:
    return render_character(replace(PRESETS[name], finish="soft"), **kw)  # type: ignore[arg-type]


def test_flat_is_the_default_and_the_two_finishes_differ() -> None:
    assert CharacterParams().finish == "flat"
    assert FINISHES == ("flat", "soft")
    flat = render_character(PRESETS["satoko"])
    assert flat == render_character(replace(PRESETS["satoko"], finish="flat"))
    assert flat != _soft("satoko")


def test_flat_has_none_of_what_soft_adds() -> None:
    flat = render_character(PRESETS["satoko"])
    for marker in (
        "linearGradient",
        "radialGradient",
        "feGaussianBlur",
        "iris-grad",
        "blush-grad",
        "soft-face-clip",
    ):
        assert marker not in flat


def test_soft_has_no_hair_gloss_depth_wash_or_face_edge_shading() -> None:
    """Removed after the owner's blind pairs (2026-10-16): the gloss arc ignored the strands, the
    depth wash chalked the hair and the face shading read as dirt."""
    svg = _soft("risa")
    for marker in ("hair-depth", "face-round", "soft-gloss", "soft-hair-clip"):
        assert marker not in svg


def test_an_unknown_finish_is_refused() -> None:
    with pytest.raises(ValueError, match="finish must be one of"):
        render_character(replace(CharacterParams(), finish="glossy"))


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_every_preset_draws_soft_as_well_formed_svg_without_blur(name: str) -> None:
    svg = _soft(name)
    ET.fromstring(svg)
    # cairosvg writes the PNGs and has no gaussian blur: the finish is gradients only.
    assert "feGaussianBlur" not in svg
    assert "linearGradient" in svg and "radialGradient" in svg


@pytest.mark.parametrize("name", ["satoko", "katherina", "risa"])
def test_what_the_soft_finish_adds_is_defined_once_and_every_reference_resolves(name: str) -> None:
    svg = _soft(name, id_prefix="f1")
    ids = re.findall(r'\bid="([^"]+)"', svg)
    ours = [i for i in ids if re.search(r"(iris-|blush-grad|soft-)", i)]
    assert ours, "the soft finish defines no ids"
    assert len(ours) == len(set(ours)), "an id the soft finish defines is defined twice"
    assert all(i.startswith("f1-") for i in ids)
    for ref in re.findall(r"url\(#([^)]+)\)", svg):
        assert ref in ids, f"{ref} is used but not defined"


def _line_widths(svg: str) -> list[float]:
    """Every stroke width in `svg`."""
    return [
        float(e.get("stroke-width"))  # type: ignore[arg-type]
        for e in ET.fromstring(svg).iter()
        if e.get("stroke-width")
    ]


def test_the_soft_lines_are_thinner_and_the_hair_has_its_own_tone() -> None:
    flat = render_character(PRESETS["satoko"])
    soft = _soft("satoko")
    assert max(_line_widths(soft)) == pytest.approx(max(_line_widths(flat)) * 0.66, abs=0.02)
    # The hair's lines are no longer the black outline colour.
    assert soft.count('stroke="#0d0d0d"') < flat.count('stroke="#0d0d0d"')


def test_the_cli_takes_a_finish(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    out = tmp_path / "char"
    monkeypatch.setattr(
        "sys.argv", ["generate", "--out", str(out), "--preset", "satoko", "--finish", "soft"]
    )
    main()
    assert "iris-grad" in out.with_suffix(".svg").read_text()
