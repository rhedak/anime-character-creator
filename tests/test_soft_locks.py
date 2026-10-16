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
from anime_character_creator.urlstate import params_from_dict

AUTHORED = sorted(name for name, style in HAIRSTYLES.items() if style.locks is not None)
# Per soft document. The plan said 90 KB and the owner raised it to 150 KB on 2026-10-16. It is a
# guard against runaway output, not a design limit: it can be raised again if more detail needs the
# room (more clumps, finer shapes, a new cut). Raise it on purpose, with the Chrome frame-time check
# (`harness/soft_hair/frametime.py`) re-run on the largest document, not to silence a failure.
BYTE_BUDGET = 150_000


def _soft(name: str, **kw: object) -> str:
    return render_character(replace(PRESETS[name], finish="soft"), **kw)  # type: ignore[arg-type]


def test_the_flat_finish_ignores_the_clumps(monkeypatch: pytest.MonkeyPatch) -> None:
    flat = render_character(PRESETS["risa"])
    monkeypatch.setitem(HAIRSTYLES, "long_fringed", replace(HAIRSTYLES["long_fringed"], locks=None))
    assert render_character(PRESETS["risa"]) == flat


def test_a_two_tone_cut_gets_its_clumps_again_in_the_tip_colour() -> None:
    svg = render_character(replace(PRESETS["satoko"], finish="soft", hair_tip_color="#33aaff"))
    assert svg.count('<g clip-path="url(#hair-front)">') == 2
    assert 'clip-path="url(#hair-tips)"' in svg


@pytest.mark.parametrize("name", ["satoko", "satoshi"])
def test_a_near_white_tip_stays_clean_with_no_clumps_in_it(name: str) -> None:
    """A shadow clump crossing from the hair's colour into a white tip read as a grey stain on
    Satoshi, so a pale tip takes none, while the hair colour above it keeps its clumps."""
    svg = _soft(name)
    assert 'clip-path="url(#hair-tips)">' not in svg  # no clump group clipped to the tip region
    assert svg.count('<g clip-path="url(#hair-front)">') == 1
    assert (
        'fill="#eceae3" clip-path="url(#hair-tips)" />' in svg
    )  # the repaint that covers the rest


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
    high = lit_tone(hair, highlight_rise(hair) * character._SOFT_LOCK_HIGH_RISE)
    _, s1, v1 = colorsys.rgb_to_hsv(*hex_to_rgb01(high))
    assert v1 >= v0
    if v0 < 0.7:
        assert s1 >= 0.93 * s0
    shadow = soft_shadow_tone(hair)
    _, s2, v2 = colorsys.rgb_to_hsv(*hex_to_rgb01(shadow))
    assert v2 < v0 and s2 >= 0.9 * s0


_STRIP = r'fill="#[0-9a-f]{6}" clip-path="url\(#hair-front\)" />'


def test_the_front_shade_strips_sit_under_the_clumps_with_and_without_a_tip_colour() -> None:
    """The tip repaint covers the strips (found by the break-it review), so they are drawn again
    between it and the tip-colour clumps; either way the clumps are the topmost of the two."""
    plain = render_character(replace(PRESETS["risa"], finish="soft"))
    group = plain.index('<g clip-path="url(#hair-front)">')
    assert len(re.findall(_STRIP, plain[:group])) == len(character._FRINGED_SHADE)
    assert not re.findall(_STRIP, plain[group:])

    tipped = render_character(replace(PRESETS["risa"], finish="soft", hair_tip_color="#33aaff"))
    repaint = tipped.rindex('fill="#33aaff" clip-path="url(#hair-tips)" />')
    group = tipped.rindex('<g clip-path="url(#hair-front)">')
    assert repaint < group
    assert len(re.findall(_STRIP, tipped[repaint:group])) == len(character._FRINGED_SHADE)
    assert not re.findall(_STRIP, tipped[group:])
    assert tipped.count('<g clip-path="url(#hair-front)">') == 1  # the tip region is the whole mass


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


def test_a_higher_strength_moves_every_tone_further_from_the_hair_colour() -> None:
    for hair in ("#e8b84b", "#e56a9c", "#b5602b", "#a9763f", "#6b1f2a"):
        value = lambda c: colorsys.rgb_to_hsv(*hex_to_rgb01(c))[2]  # noqa: E731
        shadows = [value(soft_shadow_tone(hair, g)) for g in (0.0, 0.5, 1.0)]
        assert value(hair) == pytest.approx(shadows[0], abs=0.01)
        assert shadows[0] > shadows[1] > shadows[2]
        lits = [value(lit_tone(hair, highlight_rise(hair) * g)) for g in (0.0, 0.5, 1.0)]
        assert lits[0] < lits[1] < lits[2]


def test_the_strength_changes_the_drawing() -> None:
    risa = replace(PRESETS["risa"], finish="soft")
    one, two = (render_character(replace(risa, highlight_strength=g)) for g in (1.0, 2.0))
    assert one != two
    assert render_character(replace(risa, highlight_strength=0.5)) != one


@pytest.mark.parametrize("bad", [-0.1, 2.1])
def test_a_strength_out_of_range_is_refused(bad: float) -> None:
    with pytest.raises(ValueError, match="highlight_strength"):
        render_character(replace(PRESETS["risa"], finish="soft", highlight_strength=bad))


@pytest.mark.parametrize("strength", [0.3, 9.0, -1.0])
def test_the_flat_finish_ignores_and_does_not_validate_the_strength(strength: float) -> None:
    """The check once ran before the finish was looked at, so a bad value raised on flat."""
    assert render_character(replace(PRESETS["risa"], highlight_strength=strength)) == (
        render_character(PRESETS["risa"])
    )


@pytest.mark.parametrize("bad", ["1", None, True, float("nan")])
def test_a_strength_that_is_not_a_number_is_refused_for_soft_and_in_a_link(bad: object) -> None:
    with pytest.raises(ValueError, match="highlight_strength"):
        render_character(replace(PRESETS["risa"], finish="soft", highlight_strength=bad))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="highlight_strength"):
        params_from_dict({"finish": "soft", "highlight_strength": bad})


def test_the_cli_refuses_a_strength_out_of_range(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["generate", "--preset", "risa", "--finish", "soft", "--highlight-strength", "3"],
    )
    with pytest.raises(SystemExit):
        main()


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


@pytest.mark.parametrize("cut", ["short_layered", "short_crop", "long_parted"])
def test_a_tip_colour_on_a_big_preset_stays_within_the_budget(cut: str) -> None:
    p = replace(PRESETS["katherina"], finish="soft", hairstyle=cut, hair_tip_color="#f8b890")
    assert len(render_character(p).encode()) <= BYTE_BUDGET
