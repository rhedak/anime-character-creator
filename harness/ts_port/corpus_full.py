"""The full corpus: cases built from the dataclass FIELDS, not from the web catalogue.

    python harness/ts_port/corpus_full.py write    # regenerate corpus/full.json and corpus/errors.json
    python harness/ts_port/corpus_full.py check    # re-derive and compare with the committed files
    python harness/ts_port/corpus_full.py stats    # counts per category, sizes

Why not the catalogue: the catalogue is the web-exposed middle tier. A corpus drawn from it
never ran `_eye_closed` (needs `eyes_closed`), `_bare_foot` (boots off) or `_straight`. Here every
field of `CharacterParams`, `Outfit` and `FaceStyle` is swept, including the ones no control sets.

Files
  corpus/full.json    a list of {"id", "p", "kw"}. `p` is the params as a DIFF from the defaults:
                      top-level fields that differ, plus nested "outfit" and "face" dicts holding
                      only the fields that differ. A field "differs" by type and repr, so 1 and
                      1.0 are different values, and 0.0 and -0.0 are. The JSON text keeps the
                      difference (`1` and `1.0`; `-0.0`). A non-finite float is the object
                      {"$float": "nan" | "inf" | "-inf"}, because JSON has no spelling for it.
                      `kw` holds only the render keyword arguments that are set (`id_prefix`,
                      `background`, `metadata`). Every case renders without raising.
  corpus/errors.json  a list of cases that RAISE, each with the exact exception class name and
                      message. `op` is "render" (default: `render_character(p, **kw)`),
                      "params_from_dict" (urlstate, `arg` is the dict) or "decode_params"
                      (urlstate, `arg` is the string). An entry with "exc": null in a non-render
                      op succeeded; `result_sha` is then the sha256 of `encode_params` of it.

A consumer in another language must read the JSON text so that `1` and `1.0` stay distinct (in
Node 22: `JSON.parse(text, (k, v, ctx) => ...)` with `ctx.source`, or a small tokenizer).

Everything is drawn from `random.Random(20261016)` in a fixed order, so the files are the same on
every run. Case ids are `[A-Za-z0-9_-]+`. Cases whose params and kwargs are identical to an earlier
case are dropped (the first one keeps the id).
"""

from __future__ import annotations

import dataclasses
import hashlib
import itertools
import json
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import _bootstrap

SEED = 20261016
CORPUS_DIR = _bootstrap.HERE / "corpus"
FULL = CORPUS_DIR / "full.json"
ERRORS = CORPUS_DIR / "errors.json"
SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")

N_RANDOM = 1500
ODD_PREFIXES = (("empty", ""), ("p", "p"), ("dollar_amp", "a$&b"), ("bslash_1", "x\\1"), ("g1z", "\\g<1>z"), ("eacute", "é"), ("dot", "a.b"))

# Valid colour strings used by the sweeps. They were picked to reach every branch of colorutil:
# grey and pale (saturation under 0.35), a yellow-green (hue 55 to 90 degrees), a yellow (hue 30
# to 70), a magenta (hue near 1), white and black, and a light colour that pushes value past 1.
PALETTE = (
    "#c0392b",
    "#f5f0e6",
    "#1b1b1b",
    "#2e86c1",
    "#c8d84a",
    "#808080",
    "#ffffff",
    "#000000",
    "#e56a9c",
    "#ff00cc",
    "#e8b84b",
    "#f4e04d",
    "#ff2255",
    "#d9d9a0",
)
# Strings colorutil's `int(.., 16)` accepts although they are not `#rrggbb`: upper case, no `#`,
# several `#`, longer than six digits, padded with blanks, signed, and Arabic-Indic digits.
ODD_COLOURS = ("#FFAA00", "ff8800", "##ff0000", "#abcdef12", "# f0 f0 f0", "#+f+f+f", "#١٢٣٤٥٦")
TEXTS = (None, "", "A", "1272", "0000", "12345678901234567890", '<&>"\'', "é", "日本語", "a😀b", "é", " x ", "i" * 40)

# fields that need the setting of another garment (catalogue `requires`) or have a special meaning
ENUM_EXTRA_VALID = {"hand_style": ("grip",)}
INT_POOL = (0, 1, -1, 2, 3, 4, 5, 7, 20, -20, 0.5, 1.0, 2.5)


# --------------------------------------------------------------------------
# JSON encoding of values and params
# --------------------------------------------------------------------------
def dumps_compact(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def enc(v: Any) -> Any:
    if isinstance(v, float) and not math.isfinite(v):
        return {"$float": "nan" if v != v else ("inf" if v > 0 else "-inf")}
    return v


def dec(v: Any) -> Any:
    if isinstance(v, dict) and set(v) == {"$float"}:
        return float(v["$float"])
    return v


def same(a: Any, b: Any) -> bool:
    """Equal in type and in spelling: 1 is not 1.0, 0.0 is not -0.0, nan is nan."""
    if type(a) is not type(b):
        return False
    if type(a) is float:
        return repr(a) == repr(b)
    return bool(a == b)


class Types:
    """The package's dataclasses and tables, imported on first use (after any hook is installed)."""

    def __init__(self) -> None:
        from anime_character_creator import character as ch
        from anime_character_creator import catalogue, presets

        self.ch = ch
        self.CharacterParams = ch.CharacterParams
        self.Outfit = ch.Outfit
        self.FaceStyle = ch.FaceStyle
        self.defaults = ch.CharacterParams()
        self.presets = presets
        cat = catalogue.build_catalogue()
        self.cat = cat
        # catalogue ranges by field
        self.ranges: dict[str, tuple[float, float]] = {}
        for k in ("height", "face_age", "hair_length", "hair_tail", "waist_shift", "bust", "chest", "highlight_strength"):
            self.ranges[k] = (cat[k]["min"], cat[k]["max"])
        for r in cat["face"]["ranges"]:
            self.ranges[r["field"]] = (r["min"], r["max"])
        self.garments = cat["garments"]
        self.group_of: dict[str, dict[str, Any]] = {}
        for g in self.garments:
            for r in g.get("ranges", []):
                self.ranges[r["field"]] = (r["min"], r["max"])
            for key in ("ranges", "bools", "selects"):
                for r in g.get(key, []):
                    self.group_of[r["field"]] = g
            self.group_of[g["color"]["field"]] = g
        self.enums: dict[str, tuple[Any, ...]] = {
            "hairstyle": tuple(ch.HAIRSTYLES),
            "body": tuple(ch.BODY_TYPES),
            "finish": tuple(ch.FINISHES),
            "hand_style": (*ch.HAND_STYLES, "grip"),
            "grip_style": tuple(ch.GRIP_STYLES),
            "belt_cut": tuple(ch.BELT_CUTS),
            "skirt_cut": tuple(ch.SKIRT_CUTS),
            "sleeve_cut": tuple(ch.SLEEVE_CUTS),
            "collar_cut": tuple(ch.COLLAR_CUTS),
            "boot_cut": tuple(ch.BOOT_CUTS),
            "coat_cut": tuple(ch.COAT_CUTS),
            "hair_clip": tuple(ch.HAIR_CLIPS),
        }
        self.fields = self._inventory()

    def _inventory(self) -> list[dict[str, Any]]:
        inv: list[dict[str, Any]] = []
        for section, cls in (("top", self.CharacterParams), ("outfit", self.Outfit), ("face", self.FaceStyle)):
            for f in dataclasses.fields(cls):
                if section == "top" and f.name in ("outfit", "face"):
                    continue
                t = str(f.type)
                opt = "None" in t
                base = t.replace(" | None", "")
                default = getattr(self.defaults if section == "top" else getattr(self.defaults, section), f.name)
                if f.name in self.enums:
                    kind = "enum"
                elif base == "str" and re.search(r"(_color(_\d)?|_tone)$", f.name):
                    kind = "colour"
                elif f.name == "wristband_text":
                    kind = "text"
                elif base == "bool":
                    kind = "bool"
                elif base == "int":
                    kind = "int"
                elif base == "float":
                    kind = "float"
                else:
                    raise RuntimeError(f"unclassified field {section}.{f.name}: {t}")
                inv.append({"section": section, "name": f.name, "kind": kind, "opt": opt, "default": default})
        names = [f["name"] for f in inv]
        if len(set(names)) != len(names):
            raise RuntimeError("field names are not unique across the dataclasses")
        return inv

    def field(self, name: str) -> dict[str, Any]:
        for f in self.fields:
            if f["name"] == name:
                return f
        raise KeyError(name)

    # --- building params ------------------------------------------------
    def rep(self, p: Any, top: dict[str, Any] | None = None, outfit: dict[str, Any] | None = None, face: dict[str, Any] | None = None) -> Any:
        kw = dict(top or {})
        if outfit:
            kw["outfit"] = dataclasses.replace(p.outfit, **outfit)
        if face:
            kw["face"] = dataclasses.replace(p.face, **face)
        return dataclasses.replace(p, **kw) if kw else p

    def setf(self, p: Any, name: str, value: Any) -> Any:
        sec = self.field(name)["section"]
        if sec == "top":
            return self.rep(p, top={name: value})
        return self.rep(p, **{sec: {name: value}})

    def getf(self, p: Any, name: str) -> Any:
        sec = self.field(name)["section"]
        return getattr(p if sec == "top" else getattr(p, sec), name)

    def diff_of(self, p: Any) -> dict[str, Any]:
        d = self.defaults
        out: dict[str, Any] = {}
        for f in dataclasses.fields(p):
            if f.name in ("outfit", "face"):
                continue
            if not same(getattr(p, f.name), getattr(d, f.name)):
                out[f.name] = enc(getattr(p, f.name))
        for nm in ("outfit", "face"):
            sub = {}
            for f in dataclasses.fields(getattr(p, nm)):
                if not same(getattr(getattr(p, nm), f.name), getattr(getattr(d, nm), f.name)):
                    sub[f.name] = enc(getattr(getattr(p, nm), f.name))
            if sub:
                out[nm] = sub
        return out


_TYPES: Types | None = None


def types() -> Types:
    global _TYPES
    if _TYPES is None:
        _bootstrap.assert_package_location()
        _TYPES = Types()
    return _TYPES


def load_full_case(entry: dict[str, Any]) -> Any:
    """The CharacterParams a corpus entry stands for (the render kwargs are `entry["kw"]`)."""
    import cases

    t = types()
    full = dataclasses.asdict(t.defaults)
    for k, v in entry["p"].items():
        if k in ("outfit", "face"):
            for kk, vv in v.items():
                if kk not in full[k]:
                    raise KeyError(f"{entry['id']}: unknown {k} field {kk!r}")
                full[k][kk] = dec(vv)
        else:
            if k not in full:
                raise KeyError(f"{entry['id']}: unknown field {k!r}")
            full[k] = dec(v)
    return cases.params_from_dict(full)


def strictly_equal(a: Any, b: Any) -> bool:
    """Field by field, `same` on every value (so 1 against 1.0 and 0.0 against -0.0 count)."""
    for f in dataclasses.fields(a):
        x, y = getattr(a, f.name), getattr(b, f.name)
        if f.name in ("outfit", "face"):
            if not strictly_equal(x, y):
                return False
        elif not same(x, y):
            return False
    return True


# --------------------------------------------------------------------------
# ids
# --------------------------------------------------------------------------
def tok(v: Any) -> str:
    """A filesystem-safe, stable spelling of a value for a case id."""
    if v is None:
        return "null"
    if v is True:
        return "on"
    if v is False:
        return "off"
    if isinstance(v, dict):
        return {"nan": "nan", "inf": "inf", "-inf": "minf"}[v["$float"]]
    if isinstance(v, int):
        return "i" + str(v).replace("-", "m")
    if isinstance(v, float):
        if not math.isfinite(v):
            return "nan" if v != v else ("inf" if v > 0 else "minf")
        s = repr(v).replace("-", "m").replace(".", "p").replace("+", "")
        return s
    if isinstance(v, str):
        if re.fullmatch(r"#[0-9a-f]{6}", v):
            return v[1:]
        if re.fullmatch(r"[A-Za-z0-9_]{1,24}", v):
            return v
        return "s" + hashlib.sha1(v.encode("utf-8")).hexdigest()[:6]
    raise TypeError(type(v))


class Sink:
    """Collects (id, params, kwargs); drops a case whose params and kwargs repeat an earlier one."""

    def __init__(self, t: Types) -> None:
        self.t = t
        self.items: list[tuple[str, Any, dict[str, Any]]] = []
        self.seen: dict[str, str] = {}
        self.ids: set[str] = set()
        self.dropped: Counter[str] = Counter()

    def add(self, cid: str, p: Any, kw: dict[str, Any] | None = None) -> None:
        if not SAFE_ID.match(cid):
            raise RuntimeError(f"unsafe case id {cid!r}")
        if cid in self.ids:
            raise RuntimeError(f"duplicate case id {cid!r}")
        kw = dict(kw or {})
        key = dumps_compact([self.t.diff_of(p), kw])
        if key in self.seen:
            self.dropped[cid.split("-")[0]] += 1
            return
        self.seen[key] = cid
        self.ids.add(cid)
        self.items.append((cid, p, kw))


# --------------------------------------------------------------------------
# the three base characters (and a kitted one with every garment on)
# --------------------------------------------------------------------------
def bases(t: Types) -> dict[str, Any]:
    CP, O, F = t.CharacterParams, t.Outfit, t.FaceStyle
    a = CP(
        face_age=1.0,
        hairstyle="long_traced",
        hair_color="#6b2c5e",
        hair_length=0.7,
        eye_color="#c98a3e",
        bust=0.4,
        outfit=O(coat_color="#12152a", coat_length=0.7, belt_color="#31281e"),
    )
    b = CP(
        face_age=1.2,
        hairstyle="short_crop",
        hair_color="#313538",
        hair_length=0.65,
        chest=1.0,
        frame=0.5,
        outfit=O(skirt_color=None, trouser_color="#2b2d34", tunic_tucked=True),
        face=F(lash=0.4),
    )
    c = t.presets.NEUTRAL_BASES["female"]
    return {"A": a, "B": b, "C": c}


def kitted(t: Types) -> Any:
    """Every optional colour set, every cut named, every flag on: a character nobody would design."""
    ch = t.ch
    o: dict[str, Any] = {}
    i = 0
    for f in t.fields:
        if f["section"] == "outfit" and f["kind"] == "colour" and f["opt"]:
            o[f["name"]] = PALETTE[i % len(PALETTE)]
            i += 1
    o.update(
        belt_cut="buckled",
        skirt_cut="a_line",
        sleeve_cut="wide",
        collar_cut="pointed",
        boot_cut="loafer",
        coat_cut="open_jacket",
        hair_clip="crescent",
        belt_keeper_pair=True,
        tunic_tucked=True,
        sleeve_long=True,
        coat_sleeves=True,
        crystal_tongs=True,
        wristband_text="1272",
        skirt_length=0.7,
        skirt_length_chibi=0.5,
        hakama_length=0.6,
        hakama_length_chibi=0.45,
        neckline_notch=0.3,
        sleeve_drop=0.4,
    )
    top = dict(
        hair_tip_color="#eceae3",
        beard_color="#6b6459",
        familiar_color="#33303a",
        familiar_eye_color="#e09a3c",
        familiar_smile=True,
        hair_knot=True,
        hair_tail=0.7,
        face_age=1.0,
        bust=0.5,
        hairstyle="long_parted",
        hair_length=0.8,
        right_arm_out=36.0,
        left_arm_out=20.0,
    )
    return t.rep(t.CharacterParams(), top=top, outfit=o, face=dict(glasses=True, scar_side=1, chin_shadow=True, nose_dot=True, brows_over_hair=True, lid_shadow=0.15, iris_aspect=1.3))


# --------------------------------------------------------------------------
# value pools
# --------------------------------------------------------------------------
def dedup(vals: list[Any]) -> list[Any]:
    out: list[Any] = []
    for v in vals:
        if not any(same(v, w) for w in out):
            out.append(v)
    return out


def float_pool(t: Types, f: dict[str, Any], level: str) -> list[Any]:
    """Default, zero (float and int), one (float and int), ties, the catalogue's min, max and
    midpoint, a value just outside either end, negatives and plus or minus 20."""
    name, d = f["name"], f["default"]
    rng = t.ranges.get(name)
    vals: list[Any] = [0.0, 1.0, -1.0, 20.0, -20.0]
    if level == "full":
        vals += [d if d is not None else 0.0, 0, 1, 0.5, 2.0, 0.25, 0.125, 0.375, 1e-9, -0.5]
    if rng is not None:
        lo, hi = rng
        span = hi - lo
        vals += [lo, hi, (lo + hi) / 2]
        if level == "full":
            vals += [lo - 0.5 * span, hi + 0.5 * span]
    return dedup(vals)


def values_for(t: Types, f: dict[str, Any], level: str) -> list[Any]:
    """The values to try for one field, one at a time. `level` is "full" (neutral base) or "lite"."""
    k, d = f["kind"], f["default"]
    if k == "bool":
        return [not d] if level == "lite" else [True, False, 1, 0]
    if k == "enum":
        vals = list(t.enums[f["name"]])
        if f["opt"]:
            vals.append(None)
        return vals
    if k == "colour":
        n = 7 if level == "full" else 3
        vals = list(PALETTE[:n])
        if level == "full":
            vals += list(ODD_COLOURS[:3])
        if f["opt"]:
            vals.append(None)
        return vals
    if k == "text":
        return list(TEXTS if level == "full" else TEXTS[:5])
    if k == "int":
        return list(INT_POOL if level == "full" else INT_POOL[:7])
    if k == "float":
        vals = float_pool(t, f, level)
        if f["opt"]:
            vals.append(None)
        return vals
    raise RuntimeError(k)


def non_finite_values() -> list[float]:
    return [float("nan"), float("inf"), float("-inf"), -0.0]


# --------------------------------------------------------------------------
# categories
# --------------------------------------------------------------------------
def cat_presets(t: Types, s: Sink) -> None:
    """(a) every preset, neutral base, roster member and supporting character, flat and soft."""
    from anime_character_creator.supporting import SUPPORTING

    named: list[tuple[str, Any]] = [(f"pre-{k}", v) for k, v in t.presets.PRESETS.items()]
    named += [(f"pre-base_{k}", v) for k, v in t.presets.NEUTRAL_BASES.items()]
    named += [(f"pre-sup_{k}", v) for k, v in SUPPORTING.items()]
    # roster members are presets; the roster names are listed so the corpus says so
    for roster, members in t.presets.ROSTERS.items():
        for m in members:
            if m not in t.presets.PRESETS:
                raise RuntimeError(f"roster {roster} names {m}, not a preset")
    for name, p in named:
        for fin in ("flat", "soft"):
            s.add(f"{name}-{fin}", dataclasses.replace(p, finish=fin))


def cat_expressions(t: Types, s: Sink, base: dict[str, Any], kit: Any) -> None:
    """(c) each of the 13 expressions applied, flat and soft, eyes open and closed."""
    for bname, p in base.items():
        for en, ex in t.presets.EXPRESSIONS.items():
            for fin in ("flat", "soft"):
                q = dataclasses.replace(ex.applied_to(p), finish=fin)
                s.add(f"exp-{bname}-{en}-{fin}", q)
                if fin == "flat":
                    s.add(f"exp-{bname}-{en}-{fin}-shut", t.rep(q, face={"eyes_closed": True}))


def sweep_one(t: Types, s: Sink, tag: str, p: Any, level: str, only: set[str] | None = None) -> None:
    for f in t.fields:
        if only is not None and f["name"] not in only:
            continue
        for v in values_for(t, f, level):
            s.add(f"sw-{tag}-{f['name']}-{tok(v)}", t.setf(p, f["name"], v))


def cat_sweeps(t: Types, s: Sink, base: dict[str, Any]) -> None:
    """(b) one field at a time on three bases: a long-haired woman in a coat (flat), a short-haired
    man (soft) and the neutral base (flat, with the fullest value pools)."""
    a, b, c = base["A"], dataclasses.replace(base["B"], finish="soft"), base["C"]
    s.add("sw-A-base", a)
    s.add("sw-B-base", b)
    sweep_one(t, s, "C", c, "full")
    sweep_one(t, s, "A", a, "lite")
    sweep_one(t, s, "B", b, "lite")
    # non-finite floats and negative zero, on the neutral base
    for f in t.fields:
        if f["kind"] == "float":
            for v in non_finite_values():
                s.add(f"sw-C-{f['name']}-{tok(v)}", t.setf(c, f["name"], v))


def cat_garments(t: Types, s: Sink, base: dict[str, Any], kit: Any) -> None:
    """(b) garment on, then its own knobs one at a time (a belt reach means nothing without a
    belt), and every optional colour of the kitted base set to None one at a time."""
    c = base["C"]
    for gi, g in enumerate(t.garments):
        cf = g["color"]["field"]
        if cf == "underwear_color":
            on = c
        else:
            on = t.setf(c, cf, PALETTE[gi % len(PALETTE)])
            req = g.get("requires")
            if req:
                rf = next(x for x in t.garments if x["id"] == req)["color"]["field"]
                on = t.setf(on, rf, PALETTE[(gi + 3) % len(PALETTE)])
        s.add(f"act-{g['id']}-on", on)
        s.add(f"act-{g['id']}-on-soft", dataclasses.replace(on, finish="soft"))
        for key in ("ranges", "bools", "selects"):
            for r in g.get(key, []):
                f = t.field(r["field"])
                level = "full" if f["kind"] in ("float", "enum", "text", "int") else "lite"
                for v in values_for(t, f, level):
                    s.add(f"act-{g['id']}-{f['name']}-{tok(v)}", t.setf(on, f["name"], v))
        # the garment on a tunic-less, a trousered and a coated body
        for tag, variant in (
            ("notunic", t.setf(on, "tunic_color", None)),
            ("trousers", t.rep(on, outfit={"trouser_color": "#55574c", "skirt_color": None})),
            ("coat", t.rep(on, outfit={"coat_color": "#4a5442"})),
        ):
            if cf not in ("tunic_color", "trouser_color", "coat_color"):
                s.add(f"act-{g['id']}-{tag}", variant)
    for f in t.fields:
        if f["opt"] and f["kind"] in ("colour", "enum", "float") and t.getf(kit, f["name"]) is not None:
            s.add(f"act-K-{f['name']}-none", t.setf(kit, f["name"], None))
    # each garment of the kitted base alone off, soft finish
    s.add("act-K-base", kit)
    s.add("act-K-base-soft", dataclasses.replace(kit, finish="soft"))
    for bn in t.enums["body"]:
        s.add(f"act-K-body-{bn}", t.setf(kit, "body", bn))
        s.add(f"act-K-body-{bn}-soft", dataclasses.replace(t.setf(kit, "body", bn), finish="soft"))
    for hs in t.enums["hairstyle"]:
        s.add(f"act-K-hair-{hs}", t.setf(kit, "hairstyle", hs))
    # the traced cuts on each body, with and without the hat that changes the headroom
    gate = {"coat_cut": "coat_color", "skirt_cut": "skirt_color", "collar_cut": "collar_color", "boot_cut": "boot_color", "belt_cut": "belt_color", "sleeve_cut": "tunic_color"}
    for cut_field, gate_field in gate.items():
        for cut in t.enums[cut_field]:
            for bn in t.enums["body"]:
                q = t.rep(c, top={"body": bn}, outfit={gate_field: "#4a5442", cut_field: cut})
                s.add(f"act-cut-{cut_field}-{cut}-{bn}", q)
                s.add(f"act-cut-{cut_field}-{cut}-{bn}-hat", t.rep(q, outfit={"hat_color": "#201e29"}))
                s.add(f"act-cut-{cut_field}-{cut}-{bn}-soft", t.rep(q, top={"finish": "soft"}))


def cat_removal(t: Types, s: Sink, base: dict[str, Any], kit: Any) -> None:
    """(c) the base-layer code: tunic off, boots off, both, with and without trousers, skirt and
    coat, with a bust and without, on each body, closed eyes."""
    a, b, c = base["A"], dataclasses.replace(base["B"], finish="soft"), base["C"]
    for bn, p in (("A", a), ("B", b), ("C", c)):
        for tun, boot, low, coat in itertools.product(("tun", "notun"), ("boot", "noboot"), ("skirt", "trou", "both", "neither"), ("nocoat", "coat", "cutcoat")):
            o: dict[str, Any] = {}
            if tun == "notun":
                o["tunic_color"] = None
            if boot == "noboot":
                o["boot_color"] = None
            o["skirt_color"] = "#53654b" if low in ("skirt", "both") else None
            o["trouser_color"] = "#2b2d34" if low in ("trou", "both") else None
            if coat == "coat":
                o["coat_color"] = "#4a5442"
            elif coat == "cutcoat":
                o["coat_color"] = "#4a5442"
                o["coat_cut"] = "open_jacket"
            s.add(f"rm-{bn}-{tun}-{boot}-{low}-{coat}", t.rep(p, outfit=o))
    # tunic off with every body, bust, chest, underwear top, sleeves and arm position
    for bn in t.enums["body"]:
        for bust, chest in itertools.product((0.0, 0.3, 1.0), (0.0, 1.0)):
            for top in (False, True):
                for boots in (True, False):
                    q = t.rep(c, top={"body": bn, "bust": bust, "chest": chest}, outfit={"tunic_color": None, "underwear_top": top, "boot_color": None if not boots else c.outfit.boot_color})
                    s.add(f"rm-body-{bn}-b{tok(bust)}-c{tok(chest)}-{'ut' if top else 'nout'}-{'boot' if boots else 'noboot'}", q)
    for arm in (0.0, 36.0, -36.0, 90.0):
        for sl in (False, True):
            q = t.rep(c, top={"right_arm_out": arm, "left_arm_out": -arm}, outfit={"tunic_color": None, "sleeve_long": sl, "boot_color": None})
            s.add(f"rm-arms-{tok(arm)}-{'long' if sl else 'short'}", q)
    for fin in ("flat", "soft"):
        for bn in t.enums["body"]:
            q = dataclasses.replace(t.rep(kit, top={"body": bn}, outfit={"tunic_color": None, "boot_color": None}), finish=fin)
            s.add(f"rm-K-{bn}-{fin}", q)
            q2 = dataclasses.replace(t.rep(kit, top={"body": bn}, outfit={"tunic_color": None, "boot_color": None, "coat_color": None, "skirt_color": None, "robe_color": None, "hakama_color": None}), finish=fin)
            s.add(f"rm-K-{bn}-{fin}-bare", q2)
    # closed eyes beside other eye settings
    for bn, p in (("A", a), ("B", b), ("C", c)):
        s.add(f"rm-{bn}-shut", t.rep(p, face={"eyes_closed": True}))
        for fld, v in (("glasses", True), ("scar_side", 1), ("scar_side", -1), ("lash", 0.0), ("lash", 1.7), ("eye_openness", 0.0), ("gaze", 1.0), ("blush", 0.0), ("mouth_open", 1.0), ("mouth_curve", -1.0), ("eye_tilt", -0.1), ("eye_size", 1.1), ("brow_tilt", 0.6), ("lid_shadow", 0.25), ("nose_dot", True)):
            s.add(f"rm-{bn}-shut-{fld}-{tok(v)}", t.rep(p, face={"eyes_closed": True, fld: v}))
        for fa in (0.9, 1.5, 2.0):
            s.add(f"rm-{bn}-shut-age-{tok(fa)}", t.rep(p, top={"face_age": fa}, face={"eyes_closed": True}))


def cat_hair(t: Types, s: Sink, base: dict[str, Any]) -> None:
    """(d) every hairstyle x finish x hair_length extremes x hair_tip_color x highlight_strength."""
    lengths = (0.0, 0.2, 0.45, 1.0, 1.5)
    tips = (("none", None), ("pale", "#eceae3"), ("dark", "#1b1b1b"))
    strengths = (0.0, 0.001, 0.5, 1.0, 2.0)
    hair_colours = ("#e8b84b", "#16131a", "#6b1f2a", "#9a9a9a", "#4f7a52")
    i = 0
    c = base["C"]
    for hs in t.enums["hairstyle"]:
        for fin in ("flat", "soft"):
            for ln in lengths:
                for tn, tip in tips:
                    for st in strengths if fin == "soft" else (1.0, 0.5):
                        hc = hair_colours[i % len(hair_colours)]
                        i += 1
                        q = t.rep(c, top={"hairstyle": hs, "finish": fin, "hair_length": ln, "hair_tip_color": tip, "highlight_strength": st, "hair_color": hc})
                        s.add(f"hr-{hs}-{fin}-l{tok(ln)}-{tn}-s{tok(st)}", q)
    # the same grid's corners with the tail, the knot and a bust, which the cuts react to
    for hs in t.enums["hairstyle"]:
        for fin in ("flat", "soft"):
            for tail, knot in ((0.0, True), (1.0, False), (0.5, True)):
                q = t.rep(c, top={"hairstyle": hs, "finish": fin, "hair_tail": tail, "hair_knot": knot, "bust": 0.5, "hair_length": 0.8})
                s.add(f"hr-{hs}-{fin}-tail{tok(tail)}-knot{tok(knot)}", q)
    # soft finish with a hat, a scarf, goggles, a blindfold and a clip, on every cut
    for hs in t.enums["hairstyle"]:
        for gear, o in (("hat", {"hat_color": "#201e29"}), ("scarf", {"headscarf_color": "#8d8064"}), ("goggles", {"goggle_color": "#2f2b28"}), ("blind", {"blindfold_color": "#2a2628"}), ("clip", {"hair_clip_color": "#c4903c"})):
            q = t.rep(c, top={"hairstyle": hs, "finish": "soft", "hair_length": 0.8}, outfit=o)
            s.add(f"hr-{hs}-gear-{gear}", q)


def cat_skeleton(t: Types, s: Sink, base: dict[str, Any], rnd: random.Random) -> None:
    """(f) body x height x frame x bust x waist_shift x face_age, a seeded subset of the product."""
    bodies = t.enums["body"]
    grid = list(itertools.product(bodies, (0.5, 0.8, 1.0, 1.3, 1.6), (-1.5, -1.0, 0.0, 1.0), (0.0, 0.5, 1.0), (-1.0, 0.0, 1.5), (0.0, 0.9, 2.0)))
    rnd.shuffle(grid)
    picks = grid[:360]
    names = ("A", "B", "C")
    for i, (bn, h, fr, bu, sh, fa) in enumerate(picks):
        p = base[names[i % 3]]
        o: dict[str, Any] = {}
        if i % 4 == 0:
            o["hat_color"] = "#201e29"
        q = t.rep(p, top={"body": bn, "height": h, "frame": fr, "bust": bu, "waist_shift": sh, "face_age": fa}, outfit=o)
        s.add(f"sk-{names[i % 3]}-{bn}-h{tok(h)}-fr{tok(fr)}-bu{tok(bu)}-ws{tok(sh)}-fa{tok(fa)}", q)
    # the corners of the sweep, each axis on its own
    c = base["C"]
    for h in (0.3, 0.5, 0.8, 0.9, 1.0, 1.1, 1.3, 1.6, 2.0, 3.0, -1.0, 0.0):
        for bn in bodies:
            s.add(f"sk-axis-{bn}-h{tok(h)}", t.rep(c, top={"body": bn, "height": h}))
    for fr in (-3.0, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 3.0):
        s.add(f"sk-axis-fr{tok(fr)}", t.rep(c, top={"frame": fr}))
    for hat in (None, "#201e29"):
        for bn in bodies:
            for h in (0.8, 1.0, 1.3):
                s.add(f"sk-hat-{tok(hat)}-{bn}-h{tok(h)}", t.rep(c, top={"body": bn, "height": h}, outfit={"hat_color": hat}))


def random_drawer(t: Types, base: dict[str, Any], kit: Any, rnd: random.Random, fields_per_case: tuple[int, int] = (2, 14), weights: tuple[float, float, float] = (0.62, 0.28, 0.10), from_presets: float = 0.12):
    """A function that draws one random CharacterParams per call; each field comes from a pool
    with in-range, extreme and out-of-range values."""
    from anime_character_creator.supporting import SUPPORTING

    others = [kit, *t.presets.PRESETS.values(), *SUPPORTING.values()]
    fields = t.fields

    def colour() -> str:
        return "#%02x%02x%02x" % (rnd.randrange(256), rnd.randrange(256), rnd.randrange(256))

    def flt(f: dict[str, Any], wild: str) -> Any:
        rng = t.ranges.get(f["name"])
        d = f["default"] if f["default"] is not None else 0.0
        lo, hi = rng if rng else (min(0.0, d - 1.0), max(1.0, 2 * abs(d)))
        span = hi - lo
        if wild == "in":
            x = lo + (hi - lo) * rnd.random()
            r = rnd.random()
            if r < 0.4:
                return round(x, 2)
            if r < 0.5:
                return round(x, 3)
            return x
        if wild == "ext":
            return rnd.choice([lo, hi, (lo + hi) / 2, 0.0, 1.0, d, round(lo + span * rnd.choice([0.25, 0.75]), 3)])
        return rnd.choice([lo - span * rnd.choice([0.1, 0.5, 1.0]), hi + span * rnd.choice([0.1, 0.5, 1.0]), -1.0, 2.0, 20.0, -20.0, 0, 1, 3.7])

    def val(f: dict[str, Any], wild: str) -> Any:
        k = f["kind"]
        if k == "colour":
            if f["opt"] and rnd.random() < 0.15:
                return None
            if wild == "out" and rnd.random() < 0.2:
                return rnd.choice(ODD_COLOURS)
            return colour()
        if k == "enum":
            vals = list(t.enums[f["name"]]) + ([None] if f["opt"] else [])
            return rnd.choice(vals)
        if k == "bool":
            return rnd.random() < 0.5
        if k == "text":
            return rnd.choice(TEXTS)
        if k == "int":
            return rnd.choice(INT_POOL if wild == "out" else (-1, 0, 1, 2, 3, 4))
        if f["opt"] and rnd.random() < 0.15:
            return None
        return flt(f, wild)

    def draw() -> Any:
        # mostly the three small bases, so the diff stays short; now and then a preset or the kit
        p = rnd.choice(others) if rnd.random() < from_presets else rnd.choice([base["A"], base["B"], base["C"], base["C"]])
        wild = rnd.choices(("in", "ext", "out"), weights)[0]
        n = rnd.randint(*fields_per_case)
        top: dict[str, Any] = {}
        sub: dict[str, dict[str, Any]] = {"outfit": {}, "face": {}}
        for f in rnd.sample(fields, n):
            v = val(f, wild)
            if f["section"] == "top":
                top[f["name"]] = v
            else:
                sub[f["section"]][f["name"]] = v
        top["finish"] = rnd.choice(("flat", "soft"))
        return t.rep(p, top=top, outfit=sub["outfit"], face=sub["face"])

    return draw


def cat_random(t: Types, s: Sink, base: dict[str, Any], kit: Any, rnd: random.Random) -> None:
    """(e) seeded random combinations (see `random_drawer`)."""
    draw = random_drawer(t, base, kit, rnd)
    for i in range(N_RANDOM):
        s.add(f"rnd-{i:04d}", draw())


def cat_audit(t: Types, s: Sink, base: dict[str, Any]) -> None:
    """Cases the test audit (docs/ts-port-test-audit.md section 6) needs, so that Python tests can
    be dropped as covered by the oracle. Ids start with `aud-`; item numbers are the audit's."""
    c = base["C"]
    presets = t.presets.PRESETS
    # 1. catalogue extremes: lo and hi of every garment range (garment on), face range, hair_length,
    # hair_tail, the other top-level ranges, and every scar option
    for gi, g in enumerate(t.garments):
        cf_ = g["color"]["field"]
        on = c if cf_ == "underwear_color" else t.setf(c, cf_, PALETTE[gi % len(PALETTE)])
        req = g.get("requires")
        if req:
            rf = next(x for x in t.garments if x["id"] == req)["color"]["field"]
            on = t.setf(on, rf, PALETTE[(gi + 3) % len(PALETTE)])
        for r in g.get("ranges", []):
            for tag, v in (("lo", r["min"]), ("hi", r["max"])):
                s.add(f"aud-cat-{g['id']}-{r['field']}-{tag}", t.setf(on, r["field"], v))
        for r in g.get("selects", []):
            for o in r["options"]:
                s.add(f"aud-cat-{g['id']}-{r['field']}-{tok(o['value'])}", t.setf(on, r["field"], o["value"]))
    for r in t.cat["face"]["ranges"]:
        for tag, v in (("lo", r["min"]), ("hi", r["max"])):
            s.add(f"aud-cat-face-{r['field']}-{tag}", t.setf(c, r["field"], v))
    for r in t.cat["face"]["selects"]:
        for o in r["options"]:
            s.add(f"aud-cat-face-{r['field']}-{tok(o['value'])}", t.setf(c, r["field"], o["value"]))
    for k in ("hair_length", "hair_tail", "height", "face_age", "bust", "chest", "waist_shift", "highlight_strength"):
        lo, hi = t.ranges[k]
        for tag, v in (("lo", lo), ("hi", hi)):
            q = t.setf(c, k, v)
            if k == "highlight_strength":
                q = dataclasses.replace(q, finish="soft")
            s.add(f"aud-cat-top-{k}-{tag}", q)
            for hs in t.enums["hairstyle"]:
                if k in ("hair_length", "hair_tail"):
                    s.add(f"aud-cat-top-{k}-{tag}-{hs}", t.rep(q, top={"hairstyle": hs}))
    # 2. the background option: absent, None, empty, and paints
    sat = dataclasses.replace(presets["satoko"], finish="flat")
    s.add("aud-bg-absent", sat)
    s.add("aud-bg-null", sat, {"background": None})
    for n, bg in (("white", "white"), ("hex3", "#fff"), ("red", "red"), ("url", "url(#x)"), ("empty", "")):
        s.add(f"aud-bg-{n}", sat, {"background": bg})
        s.add(f"aud-bg-{n}-c", c, {"background": bg})
    # 3. user text in the wristband: markup, quotes, ampersand, angle brackets, emoji, long, empty, lone surrogate
    texts = {
        "script": "</text><script>alert(1)</script>",
        "quotes": "\"'\"'",
        "amp": "&amp; &lt; & &#x41;",
        "lt": "<",
        "gt": ">",
        "both": "<b>&</b>",
        "emoji": "\U0001f600",
        "emoji3": "a\U0001f600b\U0001f9d1\u200d\U0001f680c",
        "long": "W" * 400,
        "longword": "0123456789 " * 60,
        "empty": "",
        "space": " ",
        "lone_hi": "\ud800",
        "lone_lo": "ab\udc00cd",
        "nul": "a\x00b",
        "newline": "a\nb\r\n\tc",
        "cjk": "日本語",
        "combining": "e\u0301\u0302",
        "rtl": "\u05d0\u05d1 abc",
        "bom": "\ufeffx",
        "ctrl": "\x1b[0m",
        "backslash": "a\\b\\1\\g<1>",
        "dollar": "$& $1 $$",
    }
    for n, tx in texts.items():
        for side in (1, -1):
            q = t.rep(c, outfit={"wristband_color": "#f2efe6", "wristband_text": tx, "wristband_side": side})
            s.add(f"aud-text-{n}-s{tok(side)}", q)
        s.add(f"aud-text-{n}-soft", dataclasses.replace(t.rep(c, outfit={"wristband_color": "#f2efe6", "wristband_text": tx}), finish="soft"))
    s.add("aud-text-lindita", presets["lindita"])
    for n in ("script", "emoji3", "lone_hi", "long"):
        s.add(f"aud-text-{n}-lindita", t.rep(presets["lindita"], outfit={"wristband_text": texts[n]}))
        s.add(f"aud-text-{n}-md", t.rep(c, outfit={"wristband_color": "#f2efe6", "wristband_text": texts[n]}), {"metadata": True})
    # 4. height 0.8 and either side of it, on a figure with every optional garment colour off
    bare = t.rep(c, outfit={f["name"]: None for f in t.fields if f["section"] == "outfit" and f["opt"] and f["kind"] == "colour"})
    for hv in (0.79, 0.7999, 0.8, 0.8001, 0.81, 0.9, 1.0, 1.0001, 0.9999):
        for fin in ("flat", "soft"):
            s.add(f"aud-height-bare-{tok(hv)}-{fin}", dataclasses.replace(t.rep(bare, top={"height": hv}), finish=fin))
        s.add(f"aud-height-clothed-{tok(hv)}", t.rep(c, top={"height": hv}))
    # 5. combinations the one-field sweeps do not reach
    for n, p in presets.items():
        for tag, o in (("notunic", {"tunic_color": None}), ("notunic-notrou", {"tunic_color": None, "trouser_color": None}), ("noboots", {"boot_color": None}), ("trouoff", {"trouser_color": None})):
            s.add(f"aud-pre-{n}-{tag}", t.rep(p, outfit=o))
        for fa in (0.0, 1.0, 2.0):
            s.add(f"aud-pre-{n}-age{tok(fa)}-eye", t.rep(p, top={"face_age": fa}, face={"eye_size": 1.05, "eye_width": 1.10}))
    for hs in t.enums["hairstyle"]:
        for fin in ("flat", "soft"):
            s.add(f"aud-chiyo-{hs}-{fin}", dataclasses.replace(presets["chiyo"], hairstyle=hs, finish=fin))
    for n in ("risa", "satoshi"):
        for gz in (-1.0, -0.8, 0.0, 0.8, 1.0):
            s.add(f"aud-gaze-{n}-{tok(gz)}", t.rep(presets[n], face={"gaze": gz}))
    for n, kw in (("risa", {"right_arm_out": 128.0}), ("risa", {"right_arm_out": 125.0, "left_arm_out": 125.0}), ("keiko", {"right_arm_out": 128.0}), ("keiko", {"right_arm_out": 125.0, "left_arm_out": 125.0}), ("risa", {}), ("keiko", {})):
        tag = "-".join(f"{k[0]}{tok(v)}" for k, v in kw.items()) or "rest"
        s.add(f"aud-arm-{n}-{tag}", t.rep(presets[n], top=kw))
    # 6. highlight_strength: flat never validates it, soft raises outside 0 to 2 (errors go to errors.json)
    for hv in (0, 0.3, 9.0, -1, -1.0, 0.0, 2.0, 2.1, -0.1, 1e300, float("nan"), float("inf")):
        s.add(f"aud-hs-flat-{tok(hv)}", dataclasses.replace(c, finish="flat", highlight_strength=hv))
    for hv in (-0.1, 2.1, "1", None, True, False, float("nan"), 0, 0.0, 2, 2.0, 0.3, 9.0, -1, [], float("inf")):
        key = tok(hv) if not isinstance(hv, list) else "list"
        s.add(f"aud-hs-soft-{key}", dataclasses.replace(c, finish="soft", highlight_strength=hv))
    # 7. the soft finish with a tip colour on every authored cut, and on the big preset
    for hs in ("short_layered", "long_traced", "long_parted", "long_fringed", "short_crop"):
        for tn, tip in (("pale", "#eceae3"), ("peach", "#f8b890"), ("dark", "#1b1b1b")):
            s.add(f"aud-tip-{hs}-{tn}", dataclasses.replace(c, finish="soft", hairstyle=hs, hair_tip_color=tip))
    for hs in t.enums["hairstyle"]:
        s.add(f"aud-tip-katherina-{hs}", dataclasses.replace(presets["katherina"], finish="soft", hairstyle=hs, hair_tip_color="#f8b890"))


def cat_coverage(t: Types, s: Sink, base: dict[str, Any], kit: Any) -> None:
    """Cases added after the first coverage run (see docs/ts-port-coverage.md): parameter
    combinations the generic sweeps did not reach. Each block names the function it was added for."""
    c = base["C"]
    # _sleeve_cutaway, _raised_shoulder, _raised_cuff, _chain_until_y, _reversed_chain,
    # _without_raised_sleeves, _arm_pivot, _arms (raised arm in a coat whose sleeve is part of its
    # silhouette): the blazer is the one cut with `arm_lines`, and any non-zero arm swing raises it.
    for bn in t.enums["body"]:
        for arm in (0.07, 36.0, -36.0, 90.0):
            for sides in ("r", "l", "rl"):
                for sleeve in (None, "wide"):
                    top: dict[str, Any] = {"body": bn}
                    if "r" in sides:
                        top["right_arm_out"] = arm
                    if "l" in sides:
                        top["left_arm_out"] = -arm
                    o: dict[str, Any] = {"coat_color": "#4d5159", "coat_cut": "blazer", "sleeve_cut": sleeve}
                    q = t.rep(c, top=top, outfit=o)
                    s.add(f"cov-blazer-arm-{bn}-{tok(arm)}-{sides}-{tok(sleeve)}", q)
                    if sleeve is None:
                        s.add(f"cov-blazer-arm-{bn}-{tok(arm)}-{sides}-traced", t.rep(q, top={"hand_style": "traced"}))
    # _cuff_opening (mirrored normals), _traced_placement: a traced sleeve with a swung arm and every hand
    for bn in t.enums["body"]:
        for arm in (20.0, -20.0, 60.0, -60.0):
            for hs in t.enums["hand_style"]:
                q = t.rep(c, top={"body": bn, "left_arm_out": arm, "right_arm_out": -arm, "hand_style": hs}, outfit={"sleeve_cut": "wide", "tunic_color": "#2e86c1", "sleeve_long": True})
                s.add(f"cov-sleeve-arm-{bn}-{tok(arm)}-{hs}", q)
    # _cuff_opening (the sign flips of its two normals): a traced sleeve on the slender body with
    # the belt line moved far down. Found by a random search and then reduced to these two fields.
    for bn in t.enums["body"]:
        for ws in (-1.0, -0.5, 0.0, 0.5, 1.0, 1.25, 1.5, 3.0):
            for hs in ("mitten", "traced"):
                q = t.rep(c, top={"body": bn, "waist_shift": ws, "hand_style": hs}, outfit={"sleeve_cut": "wide"})
                s.add(f"cov-cuff-{bn}-ws{tok(ws)}-{hs}", q)
    # _belt, `_cut_half_w_at` returning None: a belt over a traced coat worn over the arms, with the
    # belt line moved until its row misses the coat's fills.
    for cut in ("open_jacket", "blazer", "lab_coat"):
        for ws in (-3.0, -1.0, 0.0, 1.0, 1.5, 3.0, 5.0):
            for bs in (1.0, 2.0, 3.0):
                q = t.rep(c, top={"waist_shift": ws}, outfit={"coat_color": "#4d5159", "coat_cut": cut, "belt_color": "#2f2b28", "belt_scale": bs})
                s.add(f"cov-beltcoat-{cut}-ws{tok(ws)}-bs{tok(bs)}", q)
    # _belt_drawn: a dress belt (keeper pair) with the tunic off; _hair_tip_tone: a tip colour equal to the hair colour
    for tun in (None, "#373833"):
        for fin in ("flat", "soft"):
            s.add(f"cov-keeper-tunic-{tok(tun)}-{fin}", t.rep(dataclasses.replace(c, finish=fin), outfit={"belt_color": "#ececec", "belt_keeper_pair": True, "tunic_color": tun}))
    for hs in t.enums["hairstyle"]:
        for fin in ("flat", "soft"):
            s.add(f"cov-tipsame-{hs}-{fin}", dataclasses.replace(c, hairstyle=hs, finish=fin, hair_tip_color=c.hair_color))
    # the geometry fields against the traced garments, every pair that moves a landmark
    for bn, ws, h, sleeve, cut in itertools.product(t.enums["body"], (-1.0, 1.5), (0.8, 1.3), (None, "wide"), (None, "open_jacket", "lab_coat", "blazer")):
        o: dict[str, Any] = {"sleeve_cut": sleeve}
        if cut is not None:
            o.update(coat_color="#4a5442", coat_cut=cut)
        s.add(f"cov-geom-{bn}-ws{tok(ws)}-h{tok(h)}-{tok(sleeve)}-{tok(cut)}", t.rep(c, top={"body": bn, "waist_shift": ws, "height": h}, outfit=o))


def cat_options(t: Types, s: Sink, base: dict[str, Any], kit: Any, rnd: random.Random) -> None:
    """(g) render options: id_prefix, background, metadata."""
    from anime_character_creator.supporting import SUPPORTING

    a, b, c = base["A"], dataclasses.replace(base["B"], finish="soft"), base["C"]
    sat = dataclasses.replace(t.presets.PRESETS["satoko"], finish="flat")
    sat_soft = dataclasses.replace(t.presets.PRESETS["satoko"], finish="soft")
    for pn, pv in ODD_PREFIXES:
        for bn, p in (("A", a), ("B", b), ("C", c), ("sat", sat), ("satsoft", sat_soft), ("K", kit)):
            s.add(f"ro-prefix-{pn}-{bn}", p, {"id_prefix": pv})
    for pre in ("hair-front", "id", "-", "a b", "a\"b", "<x>", "x" * 40, "0", "日本", "_", "a-b-c", "\\", "$1", "$$", "\\n", "\\\\", "%s", "{x}"):
        s.add(f"ro-prefixodd-{tok(pre)}", sat_soft, {"id_prefix": pre})
        s.add(f"ro-prefixodd-{tok(pre)}-flat", sat, {"id_prefix": pre})
    for bgn, bg in (("white", "white"), ("hex", "#fff"), ("red", "red"), ("url", "url(#g)"), ("empty", ""), ("quote", 'a"b<c&d'), ("rgba", "rgba(1,2,3,0.5)")):
        for bn, p in (("A", a), ("B", b), ("C", c), ("sat", sat), ("satsoft", sat_soft)):
            s.add(f"ro-bg-{bgn}-{bn}", p, {"background": bg})
    s.add("ro-both-sat", sat_soft, {"id_prefix": "q", "background": "white", "metadata": True})
    s.add("ro-both-K", kit, {"id_prefix": "a$&b", "background": "white", "metadata": True})
    # metadata: presets, odd floats and unusual text, which the reproduction link encodes
    names = sorted(t.presets.PRESETS)
    for i, n in enumerate(names):
        s.add(f"md-pre-{n}", dataclasses.replace(t.presets.PRESETS[n], finish="soft" if i % 3 == 0 else "flat"), {"metadata": True})
    for n in sorted(SUPPORTING):
        s.add(f"md-sup-{n}", SUPPORTING[n], {"metadata": True})
    odd: list[tuple[str, Any]] = [
        ("intfloat", t.rep(c, top={"hair_length": 1, "height": 1, "bust": 0}, face={"eye_size": 1, "blush": 0})),
        ("negzero", t.rep(c, top={"waist_shift": -0.0, "frame": -0.0})),
        ("tiny", t.rep(c, top={"bust": 1e-9, "hair_tail": 1e-05, "chest": 5e-324})),
        ("big", t.rep(c, top={"right_arm_out": 1e22, "left_arm_out": -1e21})),
        ("neg20", t.rep(c, top={"bust": -20.0, "chest": 20.0})),
        ("long_float", t.rep(c, top={"hair_length": 0.30000000000000004, "bust": 0.1 + 0.2, "frame": 2 / 3})),
        ("text_unicode", t.rep(c, outfit={"wristband_color": "#f2efe6", "wristband_text": "日本語é"})),
        ("text_astral", t.rep(c, outfit={"wristband_color": "#f2efe6", "wristband_text": "a😀b"})),
        ("text_markup", t.rep(c, outfit={"wristband_color": "#f2efe6", "wristband_text": '<&>"\''})),
        ("kit", kit),
        ("kit_soft", dataclasses.replace(kit, finish="soft")),
        ("tunic_off", t.rep(c, outfit={"tunic_color": None, "boot_color": None})),
        ("strength", t.rep(dataclasses.replace(c, finish="soft"), top={"highlight_strength": 0.001})),
        ("strength2", t.rep(dataclasses.replace(c, finish="soft"), top={"highlight_strength": 2})),
        ("tip", t.rep(c, top={"hair_tip_color": "#eceae3"})),
        ("nan_flat", t.rep(c, top={"bust": float("nan")}, face={"eye_size": float("inf")})),
        ("odd_colour", t.rep(c, top={"hair_color": "#FFAA00", "skin_tone": "ff8800"})),
        ("scar", t.rep(c, face={"scar_side": -1, "glasses": True})),
        ("body_slender", t.rep(c, top={"body": "tall_slender", "height": 1.3})),
        ("expr", t.presets.EXPRESSIONS["smile"].applied_to(c)),
    ]
    for n, p in odd:
        s.add(f"md-odd-{n}", p, {"metadata": True})
    # metadata on the corpus' own variety: every 25th random-looking sweep case
    for i, f in enumerate(fields_sample(t, rnd, 12)):
        s.add(f"md-sweep-{f['name']}", t.setf(c, f["name"], values_for(t, f, "lite")[0]), {"metadata": True})


def fields_sample(t: Types, rnd: random.Random, n: int) -> list[dict[str, Any]]:
    return rnd.sample(t.fields, n)


# --------------------------------------------------------------------------
# cases that raise, and the urlstate operations
# --------------------------------------------------------------------------
def cat_errors(t: Types, s: Sink, base: dict[str, Any]) -> None:
    """(h) inputs that must raise (and some that look like they should and do not)."""
    c = base["C"]
    for fin in ("x", "", "Flat", "SOFT", "soft ", None, 1, True):
        s.add(f"err-finish-{tok(fin)}", t.rep(c, top={"finish": fin}))
    for hs in (-1, 2.5, float("nan"), True, False, "1", None, 2, 0, 1, 1.0, 2.0000001, -0.0000001, float("inf"), float("-inf"), [1.0], 10**30, [], "soft"):
        key = tok(hs) if not isinstance(hs, list) else "list" + str(len(hs))
        s.add(f"err-soft-hs-{key}", t.rep(c, top={"finish": "soft", "highlight_strength": hs}))
        s.add(f"err-flat-hs-{key}", t.rep(c, top={"finish": "flat", "highlight_strength": hs}))
    for fld in ("hairstyle", "body", "belt_cut", "skirt_cut", "collar_cut", "coat_cut", "boot_cut", "hair_clip", "hand_style", "grip_style", "sleeve_cut"):
        for name in ("nope", "", "LONG_BLUNT", "long_traced_real", None):
            q = t.setf(c, fld, name)
            if fld in ("belt_cut", "skirt_cut", "collar_cut", "coat_cut", "boot_cut", "sleeve_cut"):
                gate = {"belt_cut": "belt_color", "skirt_cut": "skirt_color", "collar_cut": "collar_color", "coat_cut": "coat_color", "boot_cut": "boot_color", "sleeve_cut": "tunic_color"}[fld]
                q = t.setf(q, gate, "#4a5442")
            if fld == "hair_clip":
                q = t.setf(q, "hair_clip_color", "#c4903c")
            s.add(f"err-name-{fld}-{tok(name)}", q)
    for col in ("", "#", "#12", "#abc", "#12345", "#gg0000", "red", "rgb(1,2,3)", "#ff00", "none", "ÿÿÿ", " ", "#12 456", "1e5000", None, 5, 1.5, True, ["#fff"]):
        for fld in ("hair_color", "skin_tone", "eye_color", "tunic_color", "coat_color", "hair_tip_color", "belt_color", "underwear_color", "hat_color", "familiar_color", "beard_color", "trouser_color", "staff_color", "goggle_color"):
            key = tok(col) if not isinstance(col, list) else "list"
            s.add(f"err-colour-{fld}-{key}", t.setf(c, fld, col))
    for fld in ("hair_length", "beard_length", "height", "bust", "chest", "frame", "waist_shift", "face_age", "hair_tail", "highlight_strength"):
        for v in (-1.0, -0.001, -20.0, 20.0, 1e9, -1e9, float("nan"), float("inf"), float("-inf"), "1", "0.5", None, True, [0.5]):
            for fin in ("flat", "soft"):
                key = tok(v) if not isinstance(v, list) else "list"
                s.add(f"err-num-{fld}-{key}-{fin}", t.rep(t.setf(c, fld, v), top={"finish": fin}))
    for fld in ("hair_length", "beard_length", "skirt_length", "coat_length", "belt_scale", "katana_length", "boot_shaft", "sleeve_drop", "hakama_length"):
        for v in (-1.0, -0.001, -20.0, 20.0, float("nan"), "1"):
            gate_field = {"hair_length": None, "beard_length": "beard_color", "skirt_length": "skirt_color", "coat_length": "coat_color", "belt_scale": "belt_color", "katana_length": "katana_color", "boot_shaft": "boot_color", "sleeve_drop": "robe_color", "hakama_length": "hakama_color"}[fld]
            q = t.setf(c, fld, v)
            if gate_field:
                q = t.setf(q, gate_field, "#6b5334")
            s.add(f"err-num2-{fld}-{tok(v)}", q)
    # which values make the maths fail: negative lengths and heights on every cut, soft and flat
    for hs in t.enums["hairstyle"]:
        for fin in ("flat", "soft"):
            for ln in (-0.1, -1.0, -20.0, 20.0):
                s.add(f"err-math-{hs}-{fin}-len{tok(ln)}", t.rep(c, top={"hairstyle": hs, "finish": fin, "hair_length": ln}))
            for tail in (-1.0, 20.0):
                s.add(f"err-math-{hs}-{fin}-tail{tok(tail)}", t.rep(c, top={"hairstyle": hs, "finish": fin, "hair_tail": tail}))
    for bn in t.enums["body"]:
        for h in (-1.0, -0.2, 0.0, 0.001, 20.0, -20.0):
            s.add(f"err-math-{bn}-h{tok(h)}", t.rep(c, top={"body": bn, "height": h}))
        for fr in (-20.0, 20.0, -3.0, 3.0):
            s.add(f"err-math-{bn}-fr{tok(fr)}", t.rep(c, top={"body": bn, "frame": fr}))
        for bu in (-1.0, -20.0, 20.0, 3.0):
            s.add(f"err-math-{bn}-bust{tok(bu)}", t.rep(c, top={"body": bn, "bust": bu}))
        for ws in (-20.0, 20.0, -3.0, 5.0):
            s.add(f"err-math-{bn}-ws{tok(ws)}", t.rep(c, top={"body": bn, "waist_shift": ws}))
    for fld in ("scar_side", "wristband_side", "shoulder_bars_side", "shoulder_bars"):
        for v in (0.5, 1.0, 2.5, "1", None, True, 3.0, float("nan"), -1.5):
            q = t.setf(c, fld, v)
            q = t.rep(q, outfit={"wristband_color": "#f2efe6", "wristband_text": "12", "coat_color": "#4a5442", "shoulder_bars_color": "#b79a52"})
            s.add(f"err-int-{fld}-{tok(v)}", q)
    for v in (1.5, 2.0, 0.5, -1.5, "2", None, True, 20, 0, -1):
        q = t.rep(c, outfit={"coat_color": "#4a5442", "shoulder_bars_color": "#b79a52", "shoulder_bars": v})
        s.add(f"err-bars-{tok(v)}", q)
    for v in ("x", 1, None, True, [], {}):
        s.add(f"err-wtext-{tok(v) if not isinstance(v, (list, dict)) else type(v).__name__}", t.rep(c, outfit={"wristband_color": "#f2efe6", "wristband_text": v}))
    for v in (1, 0, "a", None, [], 0.0):
        s.add(f"err-bool-nose-{tok(v) if not isinstance(v, list) else 'list'}", t.rep(c, face={"nose_dot": v, "glasses": v, "eyes_closed": v, "chin_shadow": v, "brows_over_hair": v}))
        s.add(f"err-bool-top-{tok(v) if not isinstance(v, list) else 'list'}", t.rep(c, top={"shaded": v, "hair_knot": v, "familiar_smile": v}, outfit={"sleeve_long": v, "tunic_tucked": v, "crystal_tongs": v, "collar_mock": v, "coat_sleeves": v}))
    # a render keyword that is not a string where one is needed
    for pre in (None, 5, 1.5, True):
        s.add(f"err-prefix-{tok(pre)}", c, {"id_prefix": pre})
    for bg in (5, 1.5, True, 0, None):
        s.add(f"err-bg-{tok(bg)}", c, {"background": bg})
    for md in (0, 1, "yes", None):
        s.add(f"err-md-{tok(md)}", c, {"metadata": md})


def url_ops(t: Types) -> list[dict[str, Any]]:
    """urlstate operations: dicts and strings that arrive from outside, with their outcome."""
    from anime_character_creator import urlstate

    full = dataclasses.asdict(t.defaults)
    ops: list[dict[str, Any]] = []

    def pf(oid: str, arg: dict[str, Any]) -> None:
        ops.append({"id": f"url-pfd-{oid}", "op": "params_from_dict", "arg": arg})

    def dc(oid: str, arg: str) -> None:
        ops.append({"id": f"url-dec-{oid}", "op": "decode_params", "arg": arg})

    pf("empty", {})
    pf("full", full)
    pf("heads", {"heads": 2.4})
    pf("body_none", {"body": None})
    pf("traced_real", {"hairstyle": "long_traced_real"})
    pf("eye_style", {"face": {"eye_style": "anime", "eye_glow": 0.5}})
    pf("young", {"face_age": 0.0})
    pf("young_neg", {"face_age": -3.0})
    pf("age_exact", {"face_age": 0.9})
    pf("age_below", {"face_age": 0.8999999})
    pf("age_str", {"face_age": "1"})
    pf("age_none", {"face_age": None})
    pf("unknown_top", {"nope": 1})
    pf("unknown_outfit", {"outfit": {"nope": 1}})
    pf("unknown_face", {"face": {"nope": 1}})
    pf("outfit_not_dict", {"outfit": 5})
    pf("outfit_list", {"outfit": []})
    pf("outfit_none", {"outfit": None})
    pf("face_none", {"face": None})
    pf("finish_x", {"finish": "x"})
    pf("finish_soft", {"finish": "soft"})
    pf("hs_neg", {"finish": "soft", "highlight_strength": -1})
    pf("hs_big", {"finish": "soft", "highlight_strength": 2.5})
    pf("hs_flat_big", {"highlight_strength": 99})
    pf("hs_bool", {"finish": "soft", "highlight_strength": True})
    pf("hs_str", {"finish": "soft", "highlight_strength": "1"})
    pf("hs_nan", {"finish": "soft", "highlight_strength": float("nan")})
    pf("intfloat", {"hair_length": 1, "height": 1, "face_age": 1})
    pf("bad_type_len", {"hair_length": "1"})
    pf("unicode_text", {"outfit": {"wristband_color": "#f2efe6", "wristband_text": "日本語😀"}})
    pf("many", {"hairstyle": "short_crop", "outfit": {"coat_color": "#112233", "coat_cut": "blazer"}, "face": {"scar_side": -1}, "bust": 0.5})
    pf("key_positional", {"outfit": {"tunic_color": None}, "face": {}, "skin_tone": "#fff"})
    dc("empty", "")
    dc("bang", "!!!")
    dc("brace", "e30")
    dc("brace_pad", "e30=")
    dc("list", "W10")
    dc("null", "bnVsbA")
    dc("number", "MQ")
    dc("string", "ImEi")
    dc("bad_json", "eyJ4Ijox")
    dc("unknown_key", "eyJ4IjoxfQ")
    dc("nonascii", "é")
    dc("space", "e30 ")
    dc("lenient_junk", "e30!!")
    dc("lenient_junk2", "e3!0")
    dc("std_alphabet", "e+/0")
    dc("one_char", "e")
    dc("three_char", "e30x")
    dc("nan_json", base64_of('{"face_age":NaN}'))
    dc("inf_json", base64_of('{"bust":Infinity}'))
    dc("dup_keys", base64_of('{"bust":1,"bust":0.5}'))
    dc("bom", base64_of("﻿{}"))
    dc("trailing", base64_of("{} x"))
    dc("utf16", base64_of("{}", enc="utf-16"))
    dc("latin1", base64_of('{"hairstyle":"é"}', enc="latin-1"))
    # depth 5000 gives "not an object" on CPython 3.13 but a RecursionError message on 3.11, so it is not in the corpus
    dc("deep", base64_of("[" * 100 + "]" * 100))
    dc("valid_default", urlstate.encode_params(t.defaults))
    dc("valid_katherina", urlstate.encode_params(t.presets.PRESETS["katherina"]))
    dc("valid_padded", urlstate.encode_params(t.presets.PRESETS["satoko"]) + "==")
    dc("valid_kit", urlstate.encode_params(kitted(t)))
    return ops


def base64_of(text: str, enc: str = "utf-8") -> str:
    import base64

    return base64.urlsafe_b64encode(text.encode(enc)).decode("ascii").rstrip("=")


def run_url_op(op: dict[str, Any]) -> dict[str, Any]:
    """Execute one url op; the entry plus its outcome."""
    from anime_character_creator import urlstate

    out = dict(op)
    try:
        if op["op"] == "params_from_dict":
            arg = {k: _decode_obj(v) for k, v in op["arg"].items()}
            res = urlstate.params_from_dict(arg)
        else:
            res = urlstate.decode_params(op["arg"])
        out["exc"] = None
        out["result_sha"] = hashlib.sha256(urlstate.encode_params(res).encode("utf-8")).hexdigest()
    except Exception as e:  # recorded, not raised
        out["exc"] = type(e).__name__
        out["msg"] = str(e)
    return out


def _decode_obj(v: Any) -> Any:
    if isinstance(v, dict):
        if set(v) == {"$float"}:
            return dec(v)
        return {k: _decode_obj(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_decode_obj(x) for x in v]
    return v


def _encode_obj(v: Any) -> Any:
    if isinstance(v, dict):
        return {k: _encode_obj(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_encode_obj(x) for x in v]
    return enc(v)


# --------------------------------------------------------------------------
# generation, classification, files
# --------------------------------------------------------------------------
def candidates(skip: tuple[str, ...] = ()) -> Sink:
    t = types()
    rnd = random.Random(SEED)
    s = Sink(t)
    base = bases(t)
    kit = kitted(t)
    cat_presets(t, s)
    if "aud" not in skip:
        cat_audit(t, s, base)
    cat_expressions(t, s, base, kit)
    cat_sweeps(t, s, base)
    cat_garments(t, s, base, kit)
    cat_removal(t, s, base, kit)
    cat_hair(t, s, base)
    cat_skeleton(t, s, base, rnd)
    cat_random(t, s, base, kit, rnd)
    cat_options(t, s, base, kit, rnd)
    cat_errors(t, s, base)
    if "cov" not in skip:
        cat_coverage(t, s, base, kit)
    return s


def entry_of(t: Types, cid: str, p: Any, kw: dict[str, Any]) -> dict[str, Any]:
    return {"id": cid, "p": t.diff_of(p), "kw": kw}


def render_outcome(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Render one entry with no hook. None if it renders; else the exception's class, message
    and the innermost frame inside the package."""
    from anime_character_creator.character import render_character

    try:
        render_character(load_full_case(entry), **entry["kw"])
    except Exception as e:
        tb = e.__traceback__
        at = ""
        while tb is not None:
            fn = Path(tb.tb_frame.f_code.co_filename)
            if "anime_character_creator" in fn.parts:
                at = f"{fn.name}:{tb.tb_frame.f_code.co_name}:{tb.tb_lineno}"
            tb = tb.tb_next
        return {"exc": type(e).__name__, "msg": str(e), "at": at}
    return None


def _outcome_worker(entry: dict[str, Any]) -> dict[str, Any] | None:
    return render_outcome(entry)


def classify(entries: list[dict[str, Any]], workers: int) -> list[dict[str, Any] | None]:
    if workers <= 1:
        return [render_outcome(e) for e in entries]
    import multiprocessing

    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(workers) as pool:
        return pool.map(_outcome_worker, entries, chunksize=64)


def generate(workers: int = 8, skip: tuple[str, ...] = ()) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    t = types()
    s = candidates(skip)
    entries = [entry_of(t, cid, p, kw) for cid, p, kw in s.items]
    # the round trip: the JSON text, parsed again, rebuilds exactly the params it came from
    for (cid, p, kw), e in zip(s.items, entries, strict=True):
        back = json.loads(dumps_compact(e))
        q = load_full_case(back)
        if not strictly_equal(p, q):
            raise RuntimeError(f"{cid}: round trip changed the params")
        if back["kw"] != kw or dumps_compact(back) != dumps_compact(e):
            raise RuntimeError(f"{cid}: round trip changed the entry")
    outcomes = classify(entries, workers)
    ok: list[dict[str, Any]] = []
    errs: list[dict[str, Any]] = []
    for e, o in zip(entries, outcomes, strict=True):
        if o is None:
            ok.append(e)
        else:
            errs.append({**e, "op": "render", **o})
    for op in url_ops(t):
        errs.append(run_url_op(_with_encoded(op)))
    stats = {"candidates": len(entries), "dropped_duplicates": dict(s.dropped)}
    return ok, errs, stats


def _with_encoded(op: dict[str, Any]) -> dict[str, Any]:
    return {**op, "arg": _encode_obj(op["arg"])}


def render_files(ok: list[dict[str, Any]], errs: list[dict[str, Any]]) -> tuple[str, str]:
    full = "[\n" + ",\n".join(dumps_compact(e) for e in ok) + "\n]\n"
    err = "[\n" + ",\n".join(dumps_compact(e) for e in errs) + "\n]\n"
    return full, err


def read_corpus() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return json.loads(FULL.read_text(encoding="utf-8")), json.loads(ERRORS.read_text(encoding="utf-8"))


def category_counts(entries: list[dict[str, Any]]) -> Counter[str]:
    return Counter(e["id"].split("-")[0] for e in entries)


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "stats"
    workers = 8
    skip: tuple[str, ...] = ()
    out_dir = CORPUS_DIR
    if "--skip" in argv:
        skip = tuple(argv[argv.index("--skip") + 1].split(","))
    if "--dir" in argv:
        out_dir = Path(argv[argv.index("--dir") + 1])
    if mode not in ("write", "check", "stats", "roundtrip"):
        print(__doc__)
        return 2
    if mode == "stats":
        ok, errs = read_corpus()
        print(f"full.json {FULL.stat().st_size} bytes, {len(ok)} cases; errors.json {ERRORS.stat().st_size} bytes, {len(errs)} entries")
        print("ok per category:", dict(sorted(category_counts(ok).items())))
        print("errors per category:", dict(sorted(category_counts(errs).items())))
        return 0
    if mode == "roundtrip":
        t = types()
        ok, errs = read_corpus()
        for e in [*ok, *(x for x in errs if x["op"] == "render")]:
            p = load_full_case(e)
            if t.diff_of(p) != e["p"]:
                raise RuntimeError(f"{e['id']}: diff of the rebuilt params differs from p")
        print(f"round trip ok for {len(ok)} cases and {sum(1 for x in errs if x['op'] == 'render')} error cases")
        return 0
    ok, errs, stats = generate(workers, skip)
    full, err = render_files(ok, errs)
    if mode == "write":
        out_dir.mkdir(exist_ok=True)
        (out_dir / "full.json").write_text(full, encoding="utf-8")
        (out_dir / "errors.json").write_text(err, encoding="utf-8")
        print(f"wrote {out_dir / 'full.json'} ({len(ok)} cases, {len(full)} bytes) and {out_dir / 'errors.json'} ({len(errs)} entries, {len(err)} bytes)")
        print(stats)
        print("ok per category:", dict(sorted(category_counts(ok).items())))
        print("errors per category:", dict(sorted(category_counts(errs).items())))
        return 0
    same_full = FULL.read_text(encoding="utf-8") == full
    same_err = ERRORS.read_text(encoding="utf-8") == err
    print(f"full.json {'matches' if same_full else 'DIFFERS'}; errors.json {'matches' if same_err else 'DIFFERS'}")
    return 0 if same_full and same_err else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
