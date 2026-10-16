"""The mini corpus: build it from PRESETS, write it as JSON, rebuild params from the JSON.

    python harness/ts_port/cases.py write      # (re)write corpus/mini.json and check the round trip
    python harness/ts_port/cases.py check      # re-derive the cases and compare with corpus/mini.json

Each case is {"id", "params", "kwargs"}. `params` is the FULL nested dict
(dataclasses.asdict), not the urlstate diff form. `kwargs` are the render_character
keyword arguments other than sk and metadata.
"""

from __future__ import annotations

import dataclasses
import json
import re
import sys
from pathlib import Path
from typing import Any

import _bootstrap

CORPUS = _bootstrap.HERE / "corpus" / "mini.json"
SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")
EXTRA_PRESETS = ("katherina", "satoko")
ODD_PREFIXES = (("prefix_p", "p"), ("prefix_dollar_amp", "a$&b"), ("prefix_bslash_1", "x\\1"))
STRENGTHS = (("hs-0_0", 0.0), ("hs-0_001", 0.001), ("hs-0_5", 0.5), ("hs-2_0", 2.0))


def dump_json(obj: Any) -> str:
    """The one JSON spelling used everywhere: sorted keys, indent 1, ASCII, repr floats."""
    return json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=True) + "\n"


def params_to_dict(p: Any) -> dict[str, Any]:
    return dataclasses.asdict(p)


def params_from_dict(d: dict[str, Any]) -> Any:
    from anime_character_creator.character import CharacterParams, FaceStyle, Outfit

    d = dict(d)
    d["outfit"] = Outfit(**d["outfit"])
    d["face"] = FaceStyle(**d["face"])
    return CharacterParams(**d)


def build_cases() -> list[dict[str, Any]]:
    from anime_character_creator.presets import NEUTRAL_BASES, PRESETS

    named: list[tuple[str, Any]] = [(k, v) for k, v in PRESETS.items()]
    named += [(f"base_{k}", v) for k, v in NEUTRAL_BASES.items()]
    out: list[dict[str, Any]] = []

    def add(cid: str, p: Any, kwargs: dict[str, Any]) -> None:
        out.append({"id": cid, "params": params_to_dict(p), "kwargs": kwargs})

    for name, p in named:
        add(f"{name}-flat", dataclasses.replace(p, finish="flat"), {})
        add(f"{name}-soft", dataclasses.replace(p, finish="soft"), {})
    for name in EXTRA_PRESETS:
        flat = dataclasses.replace(PRESETS[name], finish="flat")
        soft = dataclasses.replace(PRESETS[name], finish="soft")
        for tag, prefix in ODD_PREFIXES:
            add(f"{name}-flat-{tag}", flat, {"id_prefix": prefix})
            add(f"{name}-soft-{tag}", soft, {"id_prefix": prefix})
        add(f"{name}-flat-bg_white", flat, {"background": "white"})
        add(f"{name}-soft-bg_white", soft, {"background": "white"})
        for tag, strength in STRENGTHS:
            add(f"{name}-soft-{tag}", dataclasses.replace(soft, highlight_strength=strength), {})
    ids = [c["id"] for c in out]
    if len(set(ids)) != len(ids):
        raise RuntimeError("duplicate case ids")
    for cid in ids:
        if not SAFE_ID.match(cid):
            raise RuntimeError(f"unsafe case id {cid!r}")
    return out


def load_cases(path: Path = CORPUS) -> list[dict[str, Any]]:
    """Cases from the JSON alone, with `p` (rebuilt CharacterParams) added to each."""
    cases = json.loads(path.read_text(encoding="utf-8"))
    for c in cases:
        c["p"] = params_from_dict(c["params"])
    return cases


def check_round_trip(cases: list[dict[str, Any]]) -> None:
    """Rebuilt params equal the originals, and the same type for every value (1 vs 1.0)."""
    from anime_character_creator.presets import NEUTRAL_BASES, PRESETS  # noqa: F401

    for c in cases:
        rebuilt = params_from_dict(json.loads(json.dumps(c["params"])))
        if dump_json(params_to_dict(rebuilt)) != dump_json(c["params"]):
            raise RuntimeError(f"{c['id']}: round trip changed the text of the params")
        if params_to_dict(rebuilt) != c["params"]:
            raise RuntimeError(f"{c['id']}: round trip changed params")


def main(argv: list[str]) -> int:
    _bootstrap.assert_package_location()
    mode = argv[1] if len(argv) > 1 else "write"
    cases = build_cases()
    text = dump_json(cases)
    check_round_trip(cases)
    # p == rebuilt, against the dataclass instances themselves
    from anime_character_creator.presets import NEUTRAL_BASES, PRESETS

    originals = {f"{k}-flat": dataclasses.replace(v, finish="flat") for k, v in PRESETS.items()}
    originals |= {f"base_{k}-soft": dataclasses.replace(v, finish="soft") for k, v in NEUTRAL_BASES.items()}
    by_id = {c["id"]: c for c in cases}
    for cid, p in originals.items():
        if params_from_dict(by_id[cid]["params"]) != p:
            raise RuntimeError(f"{cid}: rebuilt params != original")
    if mode == "write":
        CORPUS.write_text(text, encoding="utf-8")
        print(f"wrote {CORPUS} ({len(cases)} cases, {len(text)} bytes)")
    elif mode == "check":
        if CORPUS.read_text(encoding="utf-8") != text:
            print("corpus/mini.json differs from the re-derived cases")
            return 1
        print(f"corpus/mini.json matches ({len(cases)} cases)")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
