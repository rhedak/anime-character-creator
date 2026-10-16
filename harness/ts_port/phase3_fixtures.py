"""Phase 3 fixtures: presets, supporting cast, URL state and the metadata block, as CPython computes them.

    PYTHONPATH=src PY harness/ts_port/phase3_fixtures.py

Writes into `ts/fixtures/` (committed, each file well under 1.5 MB):

  presets.json    every PRESETS / NEUTRAL_BASES / SUPPORTING character as `asdict` and as the compact key-sorted
                  JSON text (`json.dumps(asdict(p), sort_keys=True, separators=(",", ":"))`, which is what
                  `encode_params` encodes: it tells an int from a float in every field), EXPRESSIONS, ROSTERS,
                  DISPLAY_NAMES.
  model.json      `aged_face`, `Expression.on` / `applied_to`, constructor and `replace` errors, and
                  `validate_finish` on the finish and `highlight_strength` values the port must tell apart.
  urlstate.json   encode / decode / character_url of 300 and more characters, and MALFORMED inputs with Python's
                  exact outcome (a result, or the exception class and message).
  metadata.json   `metadata_block(p)` and the head of `render_character(p, metadata=True)` for 60 characters.

Everything is seeded; running it twice writes the same bytes. A number is written with `repr`, so `1` and `1.0`
stay distinct; values the TS test must rebuild exactly are carried as JSON *text* (the TS side parses them with its
own `json.loads` port, which keeps the difference).
"""

from __future__ import annotations

import base64
import dataclasses
import hashlib
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness" / "ts_port"))
import _bootstrap  # noqa: E402

_bootstrap.assert_package_location()

import anime_character_creator  # noqa: E402
from anime_character_creator import attribution, character, presets, supporting, urlstate  # noqa: E402
from anime_character_creator.character import CharacterParams, Expression, FaceStyle, Outfit  # noqa: E402

assert str(ROOT / "src") in str(anime_character_creator.__file__)

OUT = ROOT / "ts" / "fixtures"
NAN = float("nan")
INF = float("inf")

# ---------------------------------------------------------------------------------------------------------
# helpers


def compact(obj) -> str:
    """`json.dumps` as the port's `dumps(..., {sortKeys, compact})` must write it."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def params_text(p: CharacterParams) -> str:
    return compact(dataclasses.asdict(p))


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _same(a, b) -> bool:
    return type(a) is type(b) and repr(a) == repr(b)  # repr: 0.0 and -0.0 are equal but not the same


def diff_text(p: CharacterParams) -> str:
    """What differs from `CharacterParams()`, as compact JSON text, with each number spelt as the character holds it
    (an int stays an int): the TS test rebuilds the character from it, so the committed file need not carry all 134
    fields of every one of the 300 characters."""
    base = dataclasses.asdict(CharacterParams())
    now = dataclasses.asdict(p)
    out: dict = {}
    for k, v in now.items():
        if isinstance(base[k], dict):
            sub = {k2: v2 for k2, v2 in v.items() if not _same(v2, base[k][k2])}
            if sub:
                out[k] = sub
        elif not _same(v, base[k]):
            out[k] = v
    return compact(out)


def outcome(fn, *args):
    """{"ok": ...} or {"err": class name, "msg": text} for `fn(*args)`; the result is the compact text of its dict."""
    try:
        r = fn(*args)
    except BaseException as e:  # noqa: BLE001 - the oracle records whatever Python raises
        return {"err": type(e).__name__, "msg": str(e)}
    if isinstance(r, CharacterParams):
        # The full text is 4 KB a character; its sha256 proves it and the diff from the defaults shows what it was.
        text = params_text(r)
        return {"ok_sha256": sha256(text), "ok_diff": diff_text(r)}
    return {"ok": r}


def b64(text: str | bytes) -> str:
    raw = text.encode("utf-8") if isinstance(text, str) else text
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def write(name: str, data: dict) -> None:
    path = OUT / name
    text = json.dumps(data, ensure_ascii=True, indent=1, allow_nan=True)
    path.write_text(text + "\n", encoding="ascii")
    size = path.stat().st_size
    assert size < 1_500_000, f"{name} is {size} bytes"
    print(f"wrote {path.relative_to(ROOT)} ({size} bytes)")


# ---------------------------------------------------------------------------------------------------------
# presets.json


def presets_fixture() -> dict:
    def block(table: dict) -> dict:
        return {name: {"dict": dataclasses.asdict(p), "json": params_text(p)} for name, p in table.items()}

    return {
        "presets": block(presets.PRESETS),
        "neutral_bases": block(presets.NEUTRAL_BASES),
        "supporting": block(supporting.SUPPORTING),
        "expressions": {
            name: {"dict": dataclasses.asdict(e), "json": compact(dataclasses.asdict(e))}
            for name, e in presets.EXPRESSIONS.items()
        },
        "rosters": {k: list(v) for k, v in presets.ROSTERS.items()},
        "display_names": dict(presets.DISPLAY_NAMES),
        "supporting_display_names": dict(supporting.DISPLAY_NAMES),
        "defaults": {
            "CharacterParams": params_text(CharacterParams()),
            "Outfit": compact(dataclasses.asdict(Outfit())),
            "FaceStyle": compact(dataclasses.asdict(FaceStyle())),
            "Expression": compact(dataclasses.asdict(Expression())),
        },
        "constants": {
            "MAN_LASH": presets.MAN_LASH,
            "BLACK_HAIR": presets.BLACK_HAIR,
            "HAIR": presets.HAIR,
            "UNIFORM": presets.UNIFORM,
            "CRYSTAL_KIT": list(presets.CRYSTAL_KIT),
            "ADULT_FACE_AGE": character.ADULT_FACE_AGE,
            "FINISHES": list(character.FINISHES),
        },
        # The key order of each table (Python dicts keep insertion order, and a sheet reads it).
        "orders": {
            "PRESETS": list(presets.PRESETS),
            "NEUTRAL_BASES": list(presets.NEUTRAL_BASES),
            "EXPRESSIONS": list(presets.EXPRESSIONS),
            "ROSTERS": list(presets.ROSTERS),
            "SUPPORTING": list(supporting.SUPPORTING),
        },
    }


# ---------------------------------------------------------------------------------------------------------
# Random characters, driven by the dataclass fields


COLOURS = ["#000000", "#ffffff", "#f2c9a1", "#E8B84B", "#4a9c6d", "#0d0d0d", "#abcdef", "#ABCDEF", "#7f7f7f", "#123"]
WORDS = ["long_traced", "short_crop", "short_layered", "long_blunt", "a_line", "open_jacket", "mitten", "tall_chibi", "x", ""]
TEXTS = ["", "A", "hello world", "café", "テスト", "\U0001f600 ok", 'say "hi"', "back\\slash", "tab\there", "</tag> & more"]


def field_types(cls) -> dict[str, str]:
    return {f.name: str(f.type) for f in dataclasses.fields(cls)}


def rand_float(rng: random.Random) -> float:
    k = rng.random()
    if k < 0.25:
        return float(rng.randint(-3, 4))
    if k < 0.45:
        return round(rng.uniform(-2.0, 3.0), rng.randint(0, 4))
    if k < 0.6:
        return rng.uniform(-2.0, 3.0)
    if k < 0.7:
        return rng.choice([0.1 + 0.2, 1e-05, 1.5e-07, 123456789.125, 1e16, 1e22, 0.30000000000000004, 5e-324])
    if k < 0.78:
        return rng.choice([-0.0, 0.0, 1.0, 0.5, 0.25, 2.0])
    return round(rng.uniform(0.0, 1.5), 2)


def rand_value(rng: random.Random, name: str, ty: str, specials: bool):
    """A value for one field, spelt as Python would hold it; sometimes in the wrong numeric spelling on purpose."""
    nullable = "None" in ty
    if nullable and rng.random() < 0.4:
        return None
    base = ty.replace(" | None", "")
    if base == "bool":
        return rng.random() < 0.5
    if base == "int":
        v = rng.randint(-3, 5)
        return float(v) if rng.random() < 0.08 else v
    if base == "float":
        v = rand_float(rng)
        if rng.random() < 0.12 and v == int(v) and abs(v) < 1e15:
            return int(v)  # the int spelling of a float field, as a link built in JavaScript carries it
        if specials and rng.random() < 0.03:
            return rng.choice([NAN, INF, -INF])
        return v
    if base == "str":
        if name == "finish":
            return rng.choice(["flat", "flat", "soft"])
        if name.endswith("_color") or name.endswith("tone"):
            return rng.choice(COLOURS)
        if name.endswith("_text") or name == "wristband_text":
            return rng.choice(TEXTS)
        return rng.choice(WORDS)
    raise AssertionError((name, ty))


def rand_params(rng: random.Random, specials: bool = True) -> CharacterParams:
    def fill(cls, skip=()):
        kw = {}
        for name, ty in field_types(cls).items():
            if name in skip or rng.random() < 0.45:
                continue  # leave the default, as a preset does for most fields
            kw[name] = rand_value(rng, name, ty, specials)
        return kw

    kw = fill(CharacterParams, skip=("outfit", "face"))
    face_age = rng.choice([0.9, 1.0, 1.0, 1.5, 2.0, 0.95, 3.0])
    kw["face_age"] = face_age
    if kw.get("finish") == "soft":
        kw["highlight_strength"] = rng.choice([0.0, 0.5, 1.0, 1.0, 2.0, 1.25, 0, 1, 2])
    kw["outfit"] = Outfit(**fill(Outfit))
    kw["face"] = FaceStyle(**fill(FaceStyle))
    return CharacterParams(**kw)


def sane_params(rng: random.Random) -> CharacterParams:
    """Characters the renderer can draw, for the metadata fixture (no nan, no wild ranges)."""
    base = rng.choice(list(presets.PRESETS.values()) + list(presets.NEUTRAL_BASES.values()))
    kw = {
        "hair_color": rng.choice(COLOURS[:9]),
        "skin_tone": rng.choice(COLOURS[:9]),
        "eye_color": rng.choice(COLOURS[:9]),
        "height": round(rng.uniform(0.85, 1.2), 2),
        "frame": round(rng.uniform(-0.5, 1.0), 2),
        "chest": round(rng.uniform(0.0, 1.0), 2),
        "bust": round(rng.uniform(0.0, 0.8), 2),
        "face_age": rng.choice([0.9, 1.0, 1.5, 2.0]),
        "hair_length": round(rng.uniform(0.1, 0.9), 2),
    }
    if rng.random() < 0.5:
        kw["finish"] = "soft"
        kw["highlight_strength"] = rng.choice([0.0, 0.5, 1.0, 1.5, 2.0, 1, 0.25])
    return dataclasses.replace(base, **kw)


# ---------------------------------------------------------------------------------------------------------
# urlstate.json


def url_fixture() -> dict:
    rng = random.Random(20261016)
    encode = []

    def add(label: str, p: CharacterParams) -> None:
        enc = urlstate.encode_params(p)
        text = params_text(p)
        decoded = outcome(urlstate.decode_params, enc)
        entry = {
            "label": label,
            "diff": diff_text(p),
            # The encoded string is 4 to 8 KB; its sha256 and length prove it, and the first 25 carry it whole.
            "encoded_sha256": sha256(enc),
            "encoded_len": len(enc),
            "url_sha256": sha256(urlstate.character_url(p, attribution.TOOL_URL)),
            "decoded": "same" if decoded.get("ok_sha256") == sha256(text) else decoded,
            "params_sha256": sha256(text),
        }
        if len(encode) < 25:
            entry["encoded"] = enc
            entry["params"] = text
        encode.append(entry)

    for name, p in presets.PRESETS.items():
        add(f"preset {name}", p)
    for name, p in presets.NEUTRAL_BASES.items():
        add(f"base {name}", p)
    for name, p in supporting.SUPPORTING.items():
        add(f"supporting {name}", p)
    for name, p in presets.PRESETS.items():
        add(f"preset {name} soft", dataclasses.replace(p, finish="soft", highlight_strength=1.0))
        add(f"preset {name} soft 0.35", dataclasses.replace(p, finish="soft", highlight_strength=0.35))
    for strength in (0, 1, 2, 0.0, 2.0, 1e-09, 0.1 + 0.2, 1.9999999999999998):
        add(f"soft strength {strength!r}", CharacterParams(face_age=1.0, finish="soft", highlight_strength=strength))
    for i in range(300):
        add(f"random {i}", rand_params(rng))
    assert len(encode) >= 300

    # base urls for character_url: whatever text, since it is an f-string
    urls = []
    p0 = presets.PRESETS["satoko"]
    for base in ("", "https://example.org/", "https://example.org/a b?x=1", "é€", "#", "http://x/?c", attribution.TOOL_URL):
        urls.append({"base": base, "url": urlstate.character_url(p0, base)})

    return {"encode": encode, "base_urls": {"params": params_text(p0), "cases": urls}, "malformed": malformed(rng)}


def malformed(rng: random.Random) -> list[dict]:
    cases: list[dict] = []

    def add(label: str, encoded: str) -> None:
        cases.append({"label": label, "input": encoded, **{"want": outcome(urlstate.decode_params, encoded)}})

    def payload(label: str, text: str | bytes) -> None:
        add(label, b64(text))

    valid = urlstate.encode_params(presets.PRESETS["satoko"])
    short = urlstate.encode_params(CharacterParams())

    # --- base64 level
    add("empty string", "")
    add("one char", "A")
    add("two chars", "Ab")
    add("three chars", "Abc")
    add("not base64 at all", "!!!!")
    add("punctuation", "%%%%%%%%")
    add("one stray data char", valid + "A")
    add("valid with one char cut", valid[:-1])
    add("valid with two chars cut", valid[:-2])
    add("valid with three chars cut", valid[:-3])
    add("valid with an equals appended", valid + "=")
    add("valid with padding appended", valid + "====")
    add("valid with a space inside", valid[:20] + " " + valid[20:])
    add("valid with a newline inside", valid[:20] + "\n" + valid[20:])
    add("valid with a bang inside", valid[:20] + "!" + valid[20:])
    add("valid with a non-ascii char", valid + "é")
    add("valid with an astral char", valid[:10] + "\U0001f600" + valid[10:])
    add("two adjacent non-ascii chars", valid[:10] + "é€" + valid[10:])
    add("padding in the middle", valid[:8] + "==" + valid[8:])
    add("leading padding", "==" + valid)
    add("whitespace only", "   ")
    add("the plus/slash alphabet", valid.replace("-", "+").replace("_", "/"))
    add("a link whose json uses plus and slash", b64('{"face_age":1,"hair_color":"?>>>?>>>~~~"}').replace("-", "+").replace("_", "/"))
    add("the same, url-safe", b64('{"face_age":1,"hair_color":"?>>>?>>>~~~"}'))
    add("a query string pasted whole", "?c=" + valid)
    add("a url pasted whole", "https://x.org/?c=" + valid)
    add("crlf at the end", valid + "\r\n")

    # --- the payload is not an object
    for label, text in [
        ("array", "[]"),
        ("array of one", "[1]"),
        ("int", "1"),
        ("float", "1.5"),
        ("string", '"abc"'),
        ("null", "null"),
        ("true", "true"),
        ("nan", "NaN"),
        ("infinity", "Infinity"),
        ("empty object", "{}"),
    ]:
        payload(f"json {label}", text)

    # --- json that does not parse
    for label, text in [
        ("empty", ""),
        ("blank", "  \n "),
        ("truncated", '{"face_age":1.0'),
        ("truncated at colon", '{"face_age":'),
        ("truncated key", '{"face_a'),
        ("trailing comma", '{"face_age":1.0,}'),
        ("single quotes", "{'face_age':1.0}"),
        ("unquoted key", "{face_age:1.0}"),
        ("comment", '{"face_age":1.0} // x'),
        ("two objects", '{"face_age":1.0}{"x":1}'),
        ("leading zero", '{"face_age":01}'),
        ("lone minus", '{"face_age":-}'),
        ("bad escape", '{"hair_color":"\\q"}'),
        ("bad unicode escape", '{"hair_color":"\\u12"}'),
        ("control char in string", '{"hair_color":"a\nb"}'),
        ("unterminated string", '{"hair_color":"abc'),
        ("duplicate keys last wins", '{"height":1.0,"height":2.0}'),
        ("array trailing comma", '{"hair_tail":[1,]}'),
        ("missing colon", '{"face_age" 1}'),
        ("missing comma", '{"face_age":1 "height":2}'),
        ("nan constant spellings", '{"face_age":nan}'),
        ("lowercase true", '{"hair_knot":True}'),
    ]:
        payload(f"bad json: {label}", text)
    payload("bad json: utf-8 bom", b"\xef\xbb\xbf" + b'{"height":1.5}')
    payload("bad json: utf-8 bom then junk", b"\xef\xbb\xbf" + b"\xff")
    payload("bad json: utf-16 with bom", '{"height":1.5}'.encode("utf-16"))
    payload("bad json: utf-16-le", '{"height":1.5}'.encode("utf-16-le"))
    payload("bad json: invalid utf-8 start byte", b"\xff\xfe\xfd")
    payload("bad json: invalid utf-8 continuation", b'{"hair_color":"\xc3("}')
    payload("bad json: truncated utf-8", b'{"hair_color":"\xe2\x82')
    payload("bad json: lone surrogate bytes", b'{"hair_color":"\xed\xa0\x80"}')
    payload("bad json: nul bytes", b"\x00\x00\x00")
    payload("bad json: nested arrays 9998", "[" * 9998 + "]" * 9998)
    payload("bad json: nested arrays 9999", "[" * 9999 + "]" * 9999)
    payload("bad json: nested objects 9999", '{"a":' * 9999 + "1" + "}" * 9999)
    payload("bad json: deep array inside a field", '{"hair_tail":' + "[" * 200 + "]" * 200 + "}")

    # --- valid json, wrong shape
    for label, text in [
        ("unknown key", '{"zzz":1}'),
        ("two unknown keys", '{"zzz":1,"yyy":2}'),
        ("unknown key after a known one", '{"height":1.0,"zzz":1}'),
        ("key self", '{"self":1}'),
        ("unknown outfit key", '{"outfit":{"zzz":1}}'),
        ("unknown face key", '{"face":{"zzz":1}}'),
        ("retired face keys with an unknown", '{"face":{"eye_style":1,"eye_glow":2,"zzz":1}}'),
        ("retired face keys alone", '{"face":{"eye_style":"anime","eye_glow":0.5}}'),
        ("retired heads", '{"heads":3}'),
        ("retired body null", '{"body":null}'),
        ("body null with heads", '{"heads":3,"body":null,"height":1.0}'),
        ("body set", '{"body":"tall_chibi"}'),
        ("long_traced_real", '{"hairstyle":"long_traced_real"}'),
        ("outfit string", '{"outfit":"abc"}'),
        ("outfit number", '{"outfit":5}'),
        ("outfit null", '{"outfit":null}'),
        ("outfit list", '{"outfit":[]}'),
        ("face string", '{"face":"abc"}'),
        ("face empty string", '{"face":""}'),
        ("face number", '{"face":5}'),
        ("face float", '{"face":1.5}'),
        ("face true", '{"face":true}'),
        ("face null", '{"face":null}'),
        ("face list of pairs", '{"face":[["blush",0.5]]}'),
        ("face list of two-char strings", '{"face":["ab"]}'),
        ("face list of numbers", '{"face":[5]}'),
        ("face list of short lists", '{"face":[[1]]}'),
        ("face list of long lists", '{"face":[["a",1,2]]}'),
        ("face list with a numeric key", '{"face":[[1,2]]}'),
        ("face list with an unhashable key", '{"face":[[[1],2]]}'),
        ("face list with a dict element", '{"face":[{"a":1,"b":2}]}'),
        ("face list with a dict element of three", '{"face":[{"a":1,"b":2,"c":3}]}'),
        ("face empty list", '{"face":[]}'),
        ("face_age string", '{"face_age":"x"}'),
        ("face_age null", '{"face_age":null}'),
        ("face_age list", '{"face_age":[1]}'),
        ("face_age dict", '{"face_age":{}}'),
        ("face_age true", '{"face_age":true}'),
        ("face_age false", '{"face_age":false}'),
        ("face_age low int", '{"face_age":0}'),
        ("face_age low float", '{"face_age":0.5}'),
        ("face_age negative", '{"face_age":-5}'),
        ("face_age at the floor", '{"face_age":0.9}'),
        ("face_age nan", '{"face_age":NaN}'),
        ("face_age -infinity", '{"face_age":-Infinity}'),
        ("face_age infinity", '{"face_age":Infinity}'),
        ("face_age huge", '{"face_age":1e999}'),
        ("face_age negative huge", '{"face_age":-1e999}'),
        ("face_age big int", '{"face_age":123456789012345678901234567890}'),
        ("face_age negative big int", '{"face_age":-123456789012345678901234567890}'),
    ]:
        payload(f"shape: {label}", text)

    # --- finish and strength
    for label, finish in [
        ("x", '"x"'),
        ("empty", '""'),
        ("capital", '"Soft"'),
        ("int", "1"),
        ("float", "1.5"),
        ("null", "null"),
        ("true", "true"),
        ("list", "[1]"),
        ("dict", '{"a":1.5}'),
        ("quote", "\"it's\""),
        ("both quotes", "\"it's \\\"x\\\"\""),
        ("unicode", '"caf\\u00e9"'),
        ("nbsp", '"a\\u00a0b"'),
        ("control", '"a\\u0001b"'),
        ("emoji", '"\\ud83d\\ude00"'),
        ("lone surrogate", '"\\ud800"'),
        ("backslash", '"a\\\\b"'),
        ("newline", '"a\\nb"'),
        ("flat", '"flat"'),
    ]:
        payload(f"finish {label}", '{"finish":%s}' % finish)
    for label, s in [
        ("minus one", "-1"),
        ("two and a half", "2.5"),
        ("nan", "NaN"),
        ("infinity", "Infinity"),
        ("minus infinity", "-Infinity"),
        ("true", "true"),
        ("false", "false"),
        ("string one", '"1"'),
        ("zero", "0"),
        ("zero float", "0.0"),
        ("negative zero float", "-0.0"),
        ("negative zero int", "-0"),
        ("two", "2"),
        ("two float", "2.0"),
        ("three", "3"),
        ("three float", "3.0"),
        ("just over two", "2.0000000000000004"),
        ("just under zero", "-1e-300"),
        ("null", "null"),
        ("list", "[1]"),
        ("dict", "{}"),
        ("huge int", "123456789012345678901234567890"),
        ("huge float", "1e999"),
        ("tiny", "5e-324"),
        ("one", "1"),
        ("one float", "1.0"),
        ("exp form", "1E0"),
    ]:
        payload(f"soft strength {label}", '{"finish":"soft","highlight_strength":%s}' % s)
        payload(f"flat strength {label}", '{"finish":"flat","highlight_strength":%s}' % s)
    payload("soft without a strength", '{"finish":"soft"}')

    # --- numbers where the registry says otherwise
    for label, text in [
        ("float field as int", '{"height":2,"hair_length":1}'),
        ("int field as float", '{"face":{"scar_side":1.0}}'),
        ("int field fractional", '{"face":{"scar_side":1.5}}'),
        ("int field zero float", '{"face":{"scar_side":0.0}}'),
        ("int field exp", '{"face":{"scar_side":1e0}}'),
        ("int field negative zero float", '{"face":{"scar_side":-0.0}}'),
        ("int field bool", '{"face":{"scar_side":true}}'),
        ("int field string", '{"face":{"scar_side":"1"}}'),
        ("int field huge", '{"face":{"scar_side":123456789012345678901234567890}}'),
        ("int field 2**53", '{"face":{"scar_side":9007199254740992}}'),
        ("int field 2**53+1", '{"face":{"scar_side":9007199254740993}}'),
        ("float field huge int", '{"height":123456789012345678901234567890}'),
        ("float field negative huge int", '{"height":-123456789012345678901234567890}'),
        ("float field huge exp", '{"height":1e999}'),
        ("float field big exp", '{"height":1e308}'),
        ("float field nan", '{"height":NaN}'),
        ("float field string", '{"height":"tall"}'),
        ("float field list", '{"height":[1,2.0,"a",null,true]}'),
        ("float field dict", '{"height":{"b":1,"a":2.0}}'),
        ("float field bool", '{"height":true}'),
        ("float field null", '{"height":null}'),
        ("float field negative zero", '{"height":-0.0}'),
        ("float field negative zero int", '{"height":-0}'),
        ("float field tiny", '{"height":5e-324}'),
        ("float field 1e16", '{"height":1e16}'),
        ("float field 1e22", '{"height":1e22}'),
        ("float field exp upper", '{"height":1E5}'),
        ("float field long mantissa", '{"height":0.30000000000000004}'),
        ("string field number", '{"hair_color":5}'),
        ("string field null", '{"hair_color":null}'),
        ("string field list", '{"hair_color":["a"]}'),
        ("string with unicode", '{"hair_color":"caf\\u00e9 \\ud83d\\ude00"}'),
        ("string with lone surrogate", '{"hair_color":"\\ud800x"}'),
        ("string with control", '{"hair_color":"\\u0000\\u001f\\u007f\\u0080"}'),
        ("string with slash", '{"hair_color":"a\\/b"}'),
        ("bool field number", '{"hair_knot":1}'),
        ("bool field float", '{"hair_knot":0.0}'),
        ("bool field string", '{"hair_knot":"yes"}'),
        ("bool field null", '{"hair_knot":null}'),
        ("key with unicode", '{"h\\u00e9":1}'),
        ("proto key", '{"__proto__":1}'),
        ("constructor key", '{"constructor":1}'),
        ("integer-like key", '{"1":1}'),
        ("ten thousand digits", '{"height":%s}' % ("1" * 5000)),
        ("4300 digits", '{"height":%s}' % ("1" * 4300)),
        ("4301 digits", '{"height":%s}' % ("1" * 4301)),
        ("4301 digits negative", '{"height":-%s}' % ("1" * 4301)),
        ("4301 digits then fraction", '{"height":%s.5}' % ("1" * 4301)),
    ]:
        payload(f"number: {label}", text)

    # --- a good link and what a client might do to it
    add("the short default link", short)
    add("upper-cased link", valid.upper())
    add("lower-cased link", valid.lower())
    add("reversed link", valid[::-1])

    labels = [c["label"] for c in cases]
    assert len(labels) == len(set(labels)), "duplicate labels"
    assert len(cases) >= 60
    return cases


# ---------------------------------------------------------------------------------------------------------
# metadata.json


def metadata_fixture() -> dict:
    rng = random.Random(777)
    pool: list[tuple[str, CharacterParams]] = [(f"preset {n}", p) for n, p in list(presets.PRESETS.items())[:8]]
    pool += [(f"base {n}", p) for n, p in presets.NEUTRAL_BASES.items()]
    pool += [("supporting kenzo", supporting.SUPPORTING["kenzo"])]
    pool += [("risa soft", dataclasses.replace(presets.PRESETS["risa"], finish="soft", highlight_strength=1.0))]
    pool += [(f"sane {i}", sane_params(rng)) for i in range(80)]
    cases = []
    for label, p in pool:
        try:
            doc = character.render_character(p, metadata=True)
        except Exception:  # noqa: BLE001 - a random combination the renderer refuses is simply not used
            continue
        end = doc.index("</metadata>\n") + len("</metadata>\n")
        head = doc[:end]
        block = attribution.metadata_block(p)
        assert head.split("\n", 1)[1] == "  " + block + "\n"
        cases.append({"label": label, "diff": diff_text(p), "block": block, "svg_line": head.split("\n", 1)[0]})
        if len(cases) == 70:
            break
    assert len(cases) >= 60
    from xml.sax.saxutils import escape

    escapes = []
    for text in ["", "plain", "a & b", "<tag>", "&amp;", "&&&", ">>><<<", 'say "hi"', "it's", "caf\u00e9 \U0001f600", "a\nb\tc", "&lt;&gt;&amp;", "x]]>y"]:
        escapes.append({"text": text, "plain": escape(text), "quot": escape(text, {'"': "&quot;"}), "two": escape(text, {'"': "&quot;", "'": "&apos;"})})
    return {
        "escapes": escapes,
        "constants": {
            "TOOL_URL": attribution.TOOL_URL,
            "REPOSITORY_URL": attribution.REPOSITORY_URL,
            "LICENSE_STATEMENT": attribution.LICENSE_STATEMENT,
            "NOVEL_TITLE": attribution.NOVEL_TITLE,
            "NOVEL_URL": attribution.NOVEL_URL,
            "header": attribution._metadata_header(),
        },
        "cases": cases,
    }


# ---------------------------------------------------------------------------------------------------------
# model.json


def tagged(v):
    """A Python value as the TS test rebuilds it: {"t": "int" | "float" | "bool" | "str" | "none" | "list" | "dict", "v": ...}."""
    if v is None:
        return {"t": "none"}
    if isinstance(v, bool):
        return {"t": "bool", "v": v}
    if isinstance(v, int):
        return {"t": "int", "v": str(v)}
    if isinstance(v, float):
        return {"t": "float", "v": "nan" if math.isnan(v) else "inf" if v == INF else "-inf" if v == -INF else repr(v)}
    if isinstance(v, str):
        return {"t": "str", "v": v}
    if isinstance(v, list):
        return {"t": "list", "v": [tagged(x) for x in v]}
    if isinstance(v, dict):
        return {"t": "dict", "v": {k: tagged(x) for k, x in v.items()}}
    raise AssertionError(type(v))


def model_fixture() -> dict:
    rng = random.Random(4242)
    # aged_face
    faces = [FaceStyle()] + [FaceStyle(**{n: rand_value(rng, n, t, False) for n, t in field_types(FaceStyle).items() if t in ("float",) and rng.random() < 0.8}) for _ in range(20)]
    faces += [p.face for p in presets.PRESETS.values()]
    aged = []
    for face in faces:
        for years in (0.0, 1.0, 0.5, 2.0, 1 / 3, -1.0, 1e-9, 7.77, 0.1 + 0.2):
            aged.append({"face": compact(dataclasses.asdict(face)), "years": repr(years), "want": compact(dataclasses.asdict(character.aged_face(face, years)))})
    presets_aged = [{"face": compact(dataclasses.asdict(face)), "years": repr(y), "want": compact(dataclasses.asdict(presets.aged(face, y)))} for face in faces[:8] for y in (1.0, 0.7)]
    default_years = {"face": compact(dataclasses.asdict(faces[1])), "want": compact(dataclasses.asdict(presets.aged(faces[1])))}

    # Expression
    exprs = []
    for ename, e in presets.EXPRESSIONS.items():
        for pname, p in list(presets.PRESETS.items())[:6]:
            exprs.append({"expression": ename, "preset": pname, "face": compact(dataclasses.asdict(e.on(p.face))), "params_sha256": sha256(params_text(e.applied_to(p)))})

    # constructor and replace errors
    errors = []

    def err(label, fn):
        errors.append({"label": label, **outcome(lambda: fn())})

    p = CharacterParams()
    err("replace unknown on params", lambda: dataclasses.replace(p, zzz=1))
    err("replace unknown on face", lambda: dataclasses.replace(p.face, zzz=1))
    err("replace unknown on outfit", lambda: dataclasses.replace(p.outfit, zzz=1))
    err("replace unknown on expression", lambda: dataclasses.replace(Expression(), zzz=1))
    err("replace two unknown", lambda: dataclasses.replace(p, zzz=1, yyy=2))
    err("replace self", lambda: dataclasses.replace(p, self=1))
    err("construct unknown", lambda: CharacterParams(zzz=1))
    err("construct outfit unknown", lambda: Outfit(zzz=1))
    err("construct face unknown", lambda: FaceStyle(zzz=1))
    err("construct expression unknown", lambda: Expression(zzz=1))
    err("construct self", lambda: CharacterParams(self=1))
    errors = [{"label": e["label"], "want": {k: v for k, v in e.items() if k != "label"}} for e in errors]

    # validate_finish on every spelling the port must tell apart
    finishes = [("flat", None), ("soft", None), ("x", None), ("", None), ("Soft", None), (1, None), (None, None), (True, None), ([1], None), ({"a": 1.5}, None), ("it's", None), ('a"b', None), ("café", None), ("a b", None), ("\U0001f600", None), ("a\x01b", None), ("a\\b", None), ("\ud800", None)]
    strengths = [-1, -1.0, 2.5, NAN, INF, -INF, True, False, "1", None, 0, 0.0, -0.0, 1, 1.0, 2, 2.0, 3, 3.0, 2.0000000000000004, -1e-300, 5e-324, [1], {}, 10**30, -(10**30), 1e300, 0.1 + 0.2, 1e-05]
    validate = []
    for finish, _ in finishes:
        validate.append({"finish": tagged(finish), "strength": tagged(1.0), "want": outcome(character.validate_finish, dataclasses.replace(p, finish=finish))})
    for s in strengths:
        for finish in ("soft", "flat"):
            q = dataclasses.replace(p, finish=finish, highlight_strength=s)
            validate.append({"finish": tagged(finish), "strength": tagged(s), "want": outcome(lambda q=q: (character.validate_finish(q), "ok")[1])})
    # validate_finish returns None: record "ok" as the marker
    for v in validate:
        if "ok" in v["want"] and v["want"]["ok"] is None:
            v["want"]["ok"] = "ok"
    return {"aged_face": aged, "presets_aged": presets_aged, "presets_aged_default": default_years, "expressions": exprs, "errors": errors, "validate_finish": validate, "adult_face_age": character.ADULT_FACE_AGE}


def codecs_fixture() -> dict:
    """`json.loads(bytes)` and `urlsafe_b64decode` on seeded valid, mutated and random input, for the TS ports of
    both (`pyjsonload.ts`, `pycodecs.ts`). A result is the compact JSON text of the loaded value (ints and floats
    spelt as Python holds them), or the exception class and message."""
    rng = random.Random(12345)

    def loaded(b: bytes) -> dict:
        try:
            v = json.loads(b)
        except BaseException as e:  # noqa: BLE001
            return {"err": type(e).__name__, "msg": str(e)}
        return {"ok": json.dumps(v, separators=(",", ":"), ensure_ascii=True)}

    def rand_json(d: int = 0):
        k = rng.random()
        if d > 3 or k < 0.4:
            c = rng.choice(["int", "float", "str", "bool", "null", "nan", "big"])
            if c == "int":
                return rng.choice([0, 1, -1, 5, 100, 2**53, 2**53 + 1, -(2**60)])
            if c == "float":
                return rng.choice([0.0, -0.0, 1.5, 1e-5, 1e22, 3.0, 0.1, -2.5e10, 1e300])
            if c == "str":
                return rng.choice(["", "a", "h\u00e9llo", "\u20ac", "\U0001f600", 'a"b', "\\", "\n", "tab\t", "\x01", "\ud800"])
            if c == "bool":
                return rng.random() < 0.5
            if c == "null":
                return None
            if c == "nan":
                return rng.choice([NAN, INF, -INF])
            return 10 ** rng.randint(16, 40)
        if k < 0.7:
            return [rand_json(d + 1) for _ in range(rng.randint(0, 4))]
        return {rng.choice(["a", "b", "c", "hair", "x y", "\u00e9"]): rand_json(d + 1) for _ in range(rng.randint(0, 4))}

    def mutate(b: bytes) -> bytes:
        s = bytearray(b)
        for _ in range(rng.randint(1, 3)):
            op = rng.random()
            if not s:
                s.append(rng.randrange(256))
                continue
            i = rng.randrange(len(s))
            if op < 0.3:
                del s[i]
            elif op < 0.6:
                s.insert(i, rng.choice(b'{}[],:"\\ \n\tnulltrue-+.eE0123456789NaIfy\x00\x1f\x7f\x80\xc3\xe2\xff'))
            elif op < 0.8:
                s[i] = rng.randrange(256)
            else:
                s = s[:i]
        return bytes(s)

    inputs: list[bytes] = []
    for _ in range(2200):
        v = rand_json()
        kw = rng.choice([{}, {"separators": (",", ":")}, {"indent": 2}, {"ensure_ascii": False}])
        try:
            txt = json.dumps(v, **kw).encode("utf-8", "surrogatepass")
        except Exception:  # noqa: BLE001
            continue
        inputs.append(mutate(txt) if rng.random() < 0.7 else txt)
    inputs += [bytes(rng.randrange(256) for _ in range(rng.randint(0, 12))) for _ in range(500)]
    for t in ["", " ", "[", "{", '{"a"', '{"a":', '{"a":1', '{"a":1,', '{"a":1,}', "[1,]", "[,]", '"abc', '"\\u12', '"\\u123', '"\\u1234', '"\\ud83d\\ude00"', '"\\ud83d"', '"\\ud83dx"', "-", "-a", "01", "1.", "1.e1", "1e", "1e+", "-Infinity", "-Infinit", "NaN", "Nan", "Infinity", "nul", "true", "tru", "\ufeff{}", '{"a":1}{', "[]]", "1 2", "\n\n  x", "[\n1,\n  x]", '"a\nb"', '{"a" 1}', "{'a':1}", "{1:2}", "[1 2]", "1e999", "-1e999", "123456789012345678901234567890", "-0", "-0.0", "0e0", "1E5", "[" * 999 + "]" * 999, "[" * 5000, '{"a":' * 500 + "1" + "}" * 500, "[" * 9998 + "]" * 9998, "[" * 9999 + "]" * 9999, "1" * 4300, "1" * 4301, "-" + "1" * 4301]:
        inputs.append(t.encode("utf-8", "surrogatepass"))
    for enc in ["utf-16", "utf-16-le", "utf-16-be", "utf-32", "utf-32-le", "utf-32-be", "utf-8-sig"]:
        for t in ['{"a":1}', "[1,2]", "1", "[]", '{"a":"\u00e9\U0001f600"}']:
            b = t.encode(enc)
            inputs += [b, b[:-1], b[:-2], b[:3] + b"\xff" + b[4:]]
    # keep the file small: an input over 2000 bytes is dropped here (the long ones that matter are recipes below)
    json_cases = [{"hex": b.hex(), **loaded(b)} for b in inputs if len(b) <= 2000]

    # Long inputs as recipes: the bytes are the parts, each a text repeated n times, joined.
    recipes = [
        [("[", 999), ("]", 999)],
        [("[", 5000)],
        [("[", 9998), ("]", 9998)],
        [("[", 9999), ("]", 9999)],
        [('{"a":', 9998), ("1", 1), ("}", 9998)],
        [('{"a":', 9999), ("1", 1), ("}", 9999)],
        [('{"a":[', 5000), ("1", 1), ("]}", 5000)],
        [("1", 4300)],
        [("1", 4301)],
        [("-", 1), ("1", 4301)],
        [("1", 4301), (".5", 1)],
        [("[", 1), ("1,", 3000), ("1]", 1)],
        [('"', 1), ("a", 5000), ('"', 1)],
        [('"', 1), ("\\u00e9", 1500), ('"', 1)],
        [("[", 1), ("{},", 2000), ("{}]", 1)],
    ]
    long_cases = []
    for parts in recipes:
        b = "".join(unit * n for unit, n in parts).encode("utf-8")
        long_cases.append({"parts": [[u, n] for u, n in parts], **loaded(b)})

    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_+/= !\n\u00e9\u20ac\U0001f600%#"
    b64s = ["".join(rng.choice(alphabet) for _ in range(rng.randint(0, 14))) for _ in range(2500)]
    for _ in range(800):
        raw = bytes(rng.randrange(256) for _ in range(rng.randint(0, 10)))
        t = base64.urlsafe_b64encode(raw).decode().rstrip("=")
        if rng.random() < 0.5:
            chars = list(t)
            chars.insert(rng.randrange(len(chars) + 1), rng.choice("=+/ -\u00e9"))
            t = "".join(chars)
        b64s.append(t)

    def decoded(t: str) -> dict:
        try:
            padded = t + "=" * (-len(t) % 4)
            return {"ok": base64.urlsafe_b64decode(padded.encode("ascii")).hex()}
        except BaseException as e:  # noqa: BLE001
            return {"err": type(e).__name__, "msg": str(e)}

    return {"json": json_cases, "json_long": long_cases, "base64": [{"s": t, **decoded(t)} for t in b64s]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write("presets.json", presets_fixture())
    write("urlstate.json", url_fixture())
    write("metadata.json", metadata_fixture())
    write("model.json", model_fixture())
    write("codecs.json", codecs_fixture())


if __name__ == "__main__":
    main()
