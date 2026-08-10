"""`generate.main()`: the flag-merging logic that turns argparse's namespace
into a `CharacterParams` (COLOR_ARGS/OUTFIT_ARGS/FACE_ARGS, preset selection,
--build vs --heads, and the expression-then-explicit-override ordering)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from anime_character_creator.generate import main
from anime_character_creator.skeleton import BUILDS
from anime_character_creator.urlstate import decode_params


def _run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *args: str) -> str:
    out = tmp_path / "char"
    monkeypatch.setattr("sys.argv", ["generate", "--out", str(out), *args])
    main()
    return (out.with_suffix(".svg")).read_text()


def _heads(svg: str) -> float:
    """The `heads` value baked into the embedded character-link metadata,
    which is the most direct way to see what `main()` actually resolved
    --build/--heads to, since the rendered canvas is a fixed size regardless
    of build."""
    root = ET.fromstring(svg)
    ns = "{http://www.w3.org/2000/svg}"
    link = root.find(f"{ns}metadata").findtext(f"{ns}character")
    assert link is not None
    return decode_params(link.split("?c=", 1)[1]).heads


def test_preset_and_overrides_merge(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    svg = _run(monkeypatch, tmp_path, "--preset", "satoko", "--hair-color", "#123456")
    assert "#123456" in svg


def test_build_sets_heads_and_heads_overrides_build(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    chibi = _run(monkeypatch, tmp_path, "--build", "chibi")
    realistic = _run(monkeypatch, tmp_path, "--build", "realistic")
    assert _heads(chibi) == BUILDS["chibi"]
    assert _heads(realistic) == BUILDS["realistic"]

    # --heads is parsed after --build in COLOR_ARGS/extras merging (generate.py
    # main()); since it is applied to the same `colors` dict as a later key, it
    # must win over the preceding --build entry rather than being dropped.
    explicit = _run(monkeypatch, tmp_path, "--build", "chibi", "--heads", str(BUILDS["realistic"]))
    assert _heads(explicit) == BUILDS["realistic"]


def test_explicit_face_knob_wins_over_expression(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """generate.py applies --expression, then re-applies any explicitly passed
    face knobs on top (main(), the comment above `if args.expression:`), so an
    explicit --brow-tilt must survive rather than being clobbered by the mood."""
    expression_only = _run(monkeypatch, tmp_path, "--preset", "satoko", "--expression", "stern")
    explicit_wins = _run(
        monkeypatch,
        tmp_path,
        "--preset",
        "satoko",
        "--expression",
        "stern",
        "--brow-tilt",
        "-0.9",
    )
    assert expression_only != explicit_wins


def test_flat_disables_shading(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    shaded = _run(monkeypatch, tmp_path, "--preset", "satoko")
    flat = _run(monkeypatch, tmp_path, "--preset", "satoko", "--flat")
    assert len(flat) < len(shaded)


def test_no_metadata_flag_omits_metadata_block(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    svg = _run(monkeypatch, tmp_path, "--preset", "satoko", "--no-metadata")
    assert "<metadata>" not in svg


def test_outfit_color_alias_matches_tunic_color(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    via_flag = _run(monkeypatch, tmp_path, "--tunic-color", "#abcdef")
    via_alias = _run(monkeypatch, tmp_path, "--outfit-color", "#abcdef")
    assert via_flag == via_alias
