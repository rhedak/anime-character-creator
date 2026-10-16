"""The soft finish's clumps (`Hairstyle.locks`): drawn only for the soft finish and only for a cut
that has been authored, inside the hair's own silhouette, small, deterministic, and in tones that keep
the hair's saturation. Flat output is covered by `refresh-ref-out.sh --check` and `test_soft_finish`."""

from __future__ import annotations

import colorsys
from dataclasses import replace

import pytest

from anime_character_creator import HAIRSTYLES, PRESETS, render_character
from anime_character_creator.colorutil import (
    hex_to_rgb01,
    highlight_rise,
    lit_tone,
    soft_shadow_tone,
)

AUTHORED = sorted(name for name, style in HAIRSTYLES.items() if style.locks is not None)
BYTE_BUDGET = 90_000  # per soft document, `docs/soft-hair-plan.md`


def _soft(name: str, **kw: object) -> str:
    return render_character(replace(PRESETS[name], finish="soft"), **kw)  # type: ignore[arg-type]


def test_some_cut_is_authored_and_the_flat_finish_ignores_it() -> None:
    assert "long_fringed" in AUTHORED
    flat = render_character(PRESETS["risa"])
    assert '<g clip-path="url(#hair-front)"><path' not in flat


def test_a_two_tone_cut_gets_its_clumps_again_in_the_tip_colour() -> None:
    svg = _soft("satoko")
    assert svg.count('<g clip-path="url(#hair-front)">') == 2
    assert 'clip-path="url(#hair-tips)"' in svg


def test_the_clumps_are_one_group_clipped_to_the_front_hair() -> None:
    svg = _soft("risa")
    assert svg.count('<g clip-path="url(#hair-front)">') == 1
    assert 'id="hair-front"' in svg


def test_a_cut_without_locks_draws_exactly_as_it_did(monkeypatch: pytest.MonkeyPatch) -> None:
    with_locks = _soft("risa")
    monkeypatch.setitem(HAIRSTYLES, "long_fringed", replace(HAIRSTYLES["long_fringed"], locks=None))
    without = _soft("risa")
    group_start = with_locks.index('<g clip-path="url(#hair-front)">')
    group_end = with_locks.index("</g>", group_start) + len("</g>")
    assert with_locks[:group_start] + with_locks[group_end:] == without


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_every_preset_stays_within_the_byte_budget_soft(name: str) -> None:
    assert len(_soft(name).encode()) <= BYTE_BUDGET


def test_the_clumps_are_deterministic() -> None:
    assert _soft("risa") == _soft("risa")


@pytest.mark.parametrize("cut", AUTHORED)
@pytest.mark.parametrize("fall", [1.4, 2.0, 2.8, 3.44, 4.0])
def test_every_lock_is_well_formed_and_under_the_ceiling(cut: str, fall: float) -> None:
    locks = HAIRSTYLES[cut].locks(fall)  # type: ignore[misc]
    assert locks
    for role, points, width, length in locks:
        assert role in ("shadow", "lit")
        assert len(points) >= 3 and 0 < width < 0.5 and 0 < length <= 1
        for x, y in points:
            assert abs(x) < 2.0
            # the same headroom `build_skeleton` leaves above the skull for hair ink
            assert y > -1.55


def test_an_unknown_role_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    style = replace(
        HAIRSTYLES["long_fringed"],
        locks=lambda fall: [("glow", ((0, 0), (0, 1), (0, 2)), 0.1, 1.0)],
    )
    monkeypatch.setitem(HAIRSTYLES, "long_fringed", style)
    with pytest.raises(ValueError, match="shadow or lit"):
        _soft("risa")


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_the_tones_keep_the_hair_saturation(name: str) -> None:
    hair = PRESETS[name].hair_color
    _, s0, v0 = colorsys.rgb_to_hsv(*hex_to_rgb01(hair))
    high = lit_tone(hair, highlight_rise(hair) * 0.38)
    _, s1, v1 = colorsys.rgb_to_hsv(*hex_to_rgb01(high))
    assert v1 >= v0
    if v0 < 0.7:
        assert s1 >= 0.93 * s0
    shadow = soft_shadow_tone(hair)
    _, s2, v2 = colorsys.rgb_to_hsv(*hex_to_rgb01(shadow))
    assert v2 < v0 and s2 >= 0.9 * s0
