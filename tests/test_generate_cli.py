"""`generate.main()`: the flag-merging logic that turns argparse's namespace
into a `CharacterParams` (COLOR_ARGS/OUTFIT_ARGS/FACE_ARGS, preset selection,
--build vs --heads, and the expression-then-explicit-override ordering)."""

from __future__ import annotations

import base64
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from anime_character_creator.generate import main


def _run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *args: str) -> str:
    out = tmp_path / "char"
    monkeypatch.setattr("sys.argv", ["generate", "--out", str(out), *args])
    main()
    return (out.with_suffix(".svg")).read_text()


def _link_json(svg: str) -> dict:
    """The embedded character-link metadata's own JSON, decoded.

    Not `decode_params`: loading a link maps a retired `heads` onto the tall
    chibi (`docs/tall-chibi-plan.md`, R1), and this reads what `main()`
    resolved, which the link still records.
    """
    root = ET.fromstring(svg)
    ns = "{http://www.w3.org/2000/svg}"
    link = root.find(f"{ns}metadata").findtext(f"{ns}character")
    assert link is not None
    encoded = link.split("?c=", 1)[1]
    raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    return json.loads(raw)


def test_preset_and_overrides_merge(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    svg = _run(monkeypatch, tmp_path, "--preset", "satoko", "--hair-color", "#123456")
    assert "#123456" in svg


def test_the_retired_build_options_are_gone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`--build` and `--heads` went with the realistic build
    (`docs/tall-chibi-plan.md`, R2): the CLI renders the tall chibi only."""
    for retired in (["--build", "chibi"], ["--heads", "6"]):
        with pytest.raises(SystemExit):
            _run(monkeypatch, tmp_path, *retired)
    assert "heads" not in _link_json(_run(monkeypatch, tmp_path))


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
