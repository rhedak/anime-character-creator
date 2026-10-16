"""The covers, the sheets and the command line draw in the house style, whatever the soft finish does.

The soft finish is opt-in (`CharacterParams.finish`, default "flat"), and the sibling projects that
consume this repo's output (`cover.py`, `sheet.py`, `render.sh`) never ask for it. These tests pin that:
a preset, a base and a default `CharacterParams` are flat, every figure a cover or a sheet draws is
flat, and none of the soft finish's markers reach their output. Changing the default, or a preset's
finish, is a decision for the owner and has to break one of these on purpose.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from anime_character_creator import PRESETS, CharacterParams, cover, sheet
from anime_character_creator.generate import main
from anime_character_creator.presets import NEUTRAL_BASES

# What only the soft finish writes: its iris, blush and brow shadow definitions, and the hair clumps.
SOFT_MARKERS = re.compile(
    r'id="[^"]*(iris-grad|iris-glow|blush-grad|soft-face-clip)|<g clip-path="url\(#[^)]*hair-(front|mass)\)">'
)


def test_nothing_that_is_drawn_by_default_is_soft() -> None:
    assert CharacterParams().finish == "flat"
    assert all(p.finish == "flat" for p in PRESETS.values())
    assert all(p.finish == "flat" for p in NEUTRAL_BASES.values())


def _finishes_seen(monkeypatch: pytest.MonkeyPatch, module: object) -> list[str]:
    seen: list[str] = []
    real = module.render_character  # type: ignore[attr-defined]

    def spy(p: CharacterParams, *args: object, **kwargs: object) -> str:
        seen.append(p.finish)
        return real(p, *args, **kwargs)

    monkeypatch.setattr(module, "render_character", spy)
    return seen


def test_a_cover_draws_its_figure_flat(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _finishes_seen(monkeypatch, cover)
    svg = cover.render_cover()
    assert seen and set(seen) == {"flat"}
    assert not SOFT_MARKERS.search(svg)


def test_a_sheet_draws_every_tile_flat(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _finishes_seen(monkeypatch, sheet)
    svg = sheet.render_sheet()
    assert len(seen) == len(sheet.members_of(sheet.SheetParams())) and set(seen) == {"flat"}
    assert not SOFT_MARKERS.search(svg)


def test_the_command_line_is_flat_unless_asked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    out = tmp_path / "char"
    monkeypatch.setattr("sys.argv", ["generate", "--out", str(out), "--preset", "risa"])
    main()
    assert not SOFT_MARKERS.search(out.with_suffix(".svg").read_text())
