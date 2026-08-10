"""`colorutil.shade()`: the darker/more-saturated shadow-tone derivation
every part function calls instead of hand-picking a second color. CLAUDE.md
calls out testing color parametrization outside the default hue range, so
this exercises the value/saturation math directly rather than only through
full-character renders."""

from __future__ import annotations

import colorsys

import pytest

from anime_character_creator.colorutil import hex_to_rgb01, rgb01_to_hex, shade


def test_hex_rgb01_round_trip() -> None:
    for hex_color in ["#000000", "#ffffff", "#e8b84b", "#4a9c6d", "#123456"]:
        assert rgb01_to_hex(hex_to_rgb01(hex_color)) == hex_color


def test_shade_darkens_by_default() -> None:
    base = "#e8b84b"
    shaded = shade(base)
    _, _, v_base = colorsys.rgb_to_hsv(*hex_to_rgb01(base))
    _, _, v_shaded = colorsys.rgb_to_hsv(*hex_to_rgb01(shaded))
    assert v_shaded < v_base


def test_shade_black_stays_black() -> None:
    """v=0 has nothing for a value multiply to darken further."""
    assert shade("#000000") == "#000000"


def test_shade_white_saturation_boost_clamps_at_one() -> None:
    """White has s=0, so the saturation boost multiply is a no-op regardless of
    factor; this only proves the clamp doesn't error or overshoot, since a fully
    saturated, full-value input is where saturation_boost would otherwise push
    s past 1.0."""
    assert shade("#ffffff", value_factor=1.0, saturation_boost=100.0) == "#ffffff"


def test_shade_saturation_boost_clamps_on_saturated_color() -> None:
    """A fully saturated color already sits at s=1.0; an aggressive boost must
    clamp rather than raising colorsys.hsv_to_rgb's inputs out of [0, 1]."""
    saturated = "#ff0000"  # h=0, s=1.0, v=1.0
    result = shade(saturated, value_factor=1.0, saturation_boost=5.0)
    _, s, _ = colorsys.rgb_to_hsv(*hex_to_rgb01(result))
    assert s == pytest.approx(1.0)


@pytest.mark.parametrize("hex_color", ["#ff0000", "#00ff00", "#0000ff", "#7f00ff", "#ffbf00"])
def test_shade_value_factor_scales_value_directly(hex_color: str) -> None:
    _, _, v_base = colorsys.rgb_to_hsv(*hex_to_rgb01(hex_color))
    shaded = shade(hex_color, value_factor=0.5, saturation_boost=1.0)
    _, _, v_shaded = colorsys.rgb_to_hsv(*hex_to_rgb01(shaded))
    assert v_shaded == pytest.approx(v_base * 0.5, abs=1 / 255)
