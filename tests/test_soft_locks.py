"""The soft finish's clumps (`Hairstyle.locks`): drawn only for the soft finish and only for a cut
that has been authored, inside the hair's own silhouette, small, deterministic, and in tones that keep
the hair's saturation. Flat output is covered by `refresh-ref-out.sh --check` and `test_soft_finish`."""

from __future__ import annotations

import colorsys
import re
from dataclasses import replace
from pathlib import Path

import pytest

from anime_character_creator import (
    HAIRSTYLES,
    PRESETS,
    CharacterParams,
    character,
    render_character,
)
from anime_character_creator.colorutil import (
    hex_to_rgb01,
    highlight_rise,
    lit_tone,
    soft_shadow_tone,
)
from anime_character_creator.generate import main

AUTHORED = sorted(name for name, style in HAIRSTYLES.items() if style.locks is not None)
# Per soft document. The plan said 90 KB and the owner raised it to 150 KB on 2026-10-16. It is a
# guard against runaway output, not a design limit: it can be raised again if more detail needs the
# room (more clumps, finer shapes, a new cut). Raise it on purpose, with the Chrome frame-time check
# (`harness/soft_hair/frametime.py`) re-run on the largest document, not to silence a failure.
BYTE_BUDGET = 150_000


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


def test_a_tip_colour_on_risa_keeps_the_front_shade_strips_and_the_byte_budget() -> None:
    """Found by the break-it review: the tip repaint covered the `front_shade` strips, and the
    clumps went in twice although the tip region is the whole mass, past 90 KB."""
    p = replace(PRESETS["risa"], finish="soft", hair_tip_color="#33aaff")
    svg = render_character(p)
    assert len(svg.encode()) <= BYTE_BUDGET
    repaint = svg.rindex('clip-path="url(#hair-tips)"')
    drawn_after = re.findall(
        r'fill="#[0-9a-f]{6}" clip-path="url\(#hair-front\)" />', svg[repaint:]
    )
    assert len(drawn_after) == len(character._FRINGED_SHADE), (
        "the strips are drawn again after the repaint"
    )
    assert svg.count('<g clip-path="url(#hair-front)">') == 1


@pytest.mark.parametrize("name", ["satoko", "risa"])
def test_the_byte_budget_holds_with_a_tip_colour_on_each_authored_cut(name: str) -> None:
    p = replace(PRESETS[name], finish="soft", hair_tip_color="#33aaff")
    assert len(render_character(p).encode()) <= BYTE_BUDGET


def test_a_clump_too_short_to_draw_is_skipped_not_a_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    style = replace(
        HAIRSTYLES["long_fringed"],
        locks=lambda fall: [
            ("shadow", ((0, -1), (0, 0), (0, 1)), 0.1, 0.05),
            ("lit", ((0, -1), (0, 0), (0, 1)), 0.1, 0.02),
        ],
    )
    monkeypatch.setitem(HAIRSTYLES, "long_fringed", style)
    assert _soft("risa")


def test_a_yellow_green_colour_is_not_nudged_toward_green() -> None:
    h0 = colorsys.rgb_to_hsv(*hex_to_rgb01("#fff700"))[0]
    h1 = colorsys.rgb_to_hsv(*hex_to_rgb01(lit_tone("#fff700", 0.0)))[0]
    assert h1 == pytest.approx(h0, abs=0.002)


def test_the_default_strength_is_the_authored_look_and_zero_draws_no_clumps() -> None:
    assert CharacterParams().highlight_strength == 1.0
    base = PRESETS["risa"]
    soft = render_character(replace(base, finish="soft"))
    assert soft == render_character(replace(base, finish="soft", highlight_strength=1.0))
    assert '<g clip-path="url(#hair-front)">' not in render_character(
        replace(base, finish="soft", highlight_strength=0.0)
    )


def test_a_lower_strength_moves_every_tone_toward_the_hair_colour() -> None:
    for hair in ("#e8b84b", "#e56a9c", "#b5602b", "#a9763f", "#6b1f2a"):
        full, half = soft_shadow_tone(hair, 1.0), soft_shadow_tone(hair, 0.5)
        v = [colorsys.rgb_to_hsv(*hex_to_rgb01(c))[2] for c in (hair, half, full)]
        assert v[0] >= v[1] >= v[2]
        lit_full = lit_tone(hair, highlight_rise(hair))
        lit_half = lit_tone(hair, highlight_rise(hair) * 0.5)
        lv = [colorsys.rgb_to_hsv(*hex_to_rgb01(c))[2] for c in (hair, lit_half, lit_full)]
        assert lv[0] <= lv[1] <= lv[2]


@pytest.mark.parametrize("bad", [-0.1, 2.1])
def test_a_strength_out_of_range_is_refused(bad: float) -> None:
    with pytest.raises(ValueError, match="highlight_strength"):
        render_character(replace(PRESETS["risa"], finish="soft", highlight_strength=bad))


def test_the_flat_finish_ignores_the_strength() -> None:
    assert render_character(replace(PRESETS["risa"], highlight_strength=0.3)) == render_character(
        PRESETS["risa"]
    )


def test_the_cli_takes_a_strength(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    out = tmp_path / "char"
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate",
            "--out",
            str(out),
            "--preset",
            "risa",
            "--finish",
            "soft",
            "--highlight-strength",
            "0",
        ],
    )
    main()
    assert '<g clip-path="url(#hair-front)">' not in out.with_suffix(".svg").read_text()


def test_the_flat_finish_does_not_validate_the_strength() -> None:
    """Found by the break-it review: the check ran before the finish was looked at, so a bad value
    raised on the flat finish, which the docs say ignores the field."""
    assert render_character(replace(PRESETS["risa"], highlight_strength=9.0)) == render_character(
        PRESETS["risa"]
    )


@pytest.mark.parametrize("cut", ["short_layered", "short_crop", "long_parted"])
def test_a_tip_colour_on_a_big_preset_stays_within_the_budget(cut: str) -> None:
    p = replace(PRESETS["katherina"], finish="soft", hairstyle=cut, hair_tip_color="#f8b890")
    assert len(render_character(p).encode()) <= BYTE_BUDGET
