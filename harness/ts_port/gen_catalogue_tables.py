"""Emit `catalogue.py`'s label tables and field tables as TypeScript, so none of them is typed by hand.

    PY harness/ts_port/gen_catalogue_tables.py            writes ts/src/catalogue-tables.ts

The output is generated and stays generated: run this again after a change to the Python tables. It reads the
real `anime_character_creator.catalogue` module, walks its module namespace in definition order, and writes each
label table (a dict of str to str), each field table (`RangeField`, `BoolField`, `SelectField`, `GarmentSlot`
and the tuples of them) and the tuples `HAND_STYLES` and `GRIP_STYLES` of `character.py`, which the TypeScript
`ts/src` does not export under that name.

Three things are not plain data and the script handles them on purpose:

* A cut select (`sleeve_cut`, `boot_cut`, `belt_cut`, `skirt_cut`, `collar_cut`, `coat_cut`, `hair_clip`) is
  `(None, "Plain"), *sorted(LABELS.items())` in Python. The script checks that Python's options equal exactly
  that and writes the derived expression, so a label table stays the one place a cut appears.
* Python's `_color`, `_range`, `_bool`, `_face_*` check a field name against the real dataclass; the output calls
  the TypeScript twins (`catalogue-types.ts`), which check against the field registry.
* A `RangeField` whose `lo` and `hi` are ints in Python (`shoulder_bars`, 1 to 4) is written with a trailing
  `true`, so the JSON writer prints `1` and `4`. A range whose `lo` is `ADULT_FACE_AGE` is written with the name.
"""

from __future__ import annotations

import ast
import io
import sys
import tokenize
from pathlib import Path

import _bootstrap  # noqa: F401

import anime_character_creator.character as ch  # noqa: E402
import anime_character_creator.catalogue as C  # noqa: E402
import anime_character_creator.presets as presets  # noqa: E402

_bootstrap.assert_package_location()

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ts" / "src" / "catalogue-tables.ts"

# label table -> (registry name in TypeScript, assert message or None)
REGISTRY = {
    "SLEEVE_CUT_LABELS": ("SLEEVE_CUTS", None),
    "BOOT_CUT_LABELS": ("BOOT_CUTS", None),
    "BELT_CUT_LABELS": ("BELT_CUTS", None),
    "SKIRT_CUT_LABELS": ("SKIRT_CUTS", None),
    "COLLAR_CUT_LABELS": ("COLLAR_CUTS", None),
    "HAIR_CLIP_LABELS": ("HAIR_CLIPS", None),
    "COAT_CUT_LABELS": ("COAT_CUTS", None),
    "FINISH_LABELS": ("FINISHES", None),
    "HAIRSTYLE_LABELS": (
        "HAIRSTYLES",
        "HAIRSTYLE_LABELS and HAIRSTYLES have drifted apart; a cut was added or removed on one side without the other",
    ),
    "BODY_LABELS": (
        "BODY_TYPES",
        "BODY_LABELS and BODY_TYPES have drifted apart; a body type was added or removed on one side without the other",
    ),
    "HAND_LABELS": ("HAND_STYLES", None),
    "GRIP_LABELS": ("GRIP_STYLES", None),
}
PYTHON_REGISTRY = {
    "SLEEVE_CUTS": ch.SLEEVE_CUTS,
    "BOOT_CUTS": ch.BOOT_CUTS,
    "BELT_CUTS": ch.BELT_CUTS,
    "SKIRT_CUTS": ch.SKIRT_CUTS,
    "COLLAR_CUTS": ch.COLLAR_CUTS,
    "HAIR_CLIPS": ch.HAIR_CLIPS,
    "COAT_CUTS": ch.COAT_CUTS,
    "FINISHES": ch.FINISHES,
    "HAIRSTYLES": ch.HAIRSTYLES,
    "BODY_TYPES": ch.BODY_TYPES,
    "HAND_STYLES": ch.HAND_STYLES,
    "GRIP_STYLES": ch.GRIP_STYLES,
}
# select field -> (label table, first option or None for "no prefix")
CUT_SELECTS = {
    "sleeve_cut": ("SLEEVE_CUT_LABELS", "Plain"),
    "boot_cut": ("BOOT_CUT_LABELS", "Boot"),
    "belt_cut": ("BELT_CUT_LABELS", "Band"),
    "skirt_cut": ("SKIRT_CUT_LABELS", "Gathered"),
    "collar_cut": ("COLLAR_CUT_LABELS", "Band"),
    "coat_cut": ("COAT_CUT_LABELS", "Two panels"),
    "hair_clip": ("HAIR_CLIP_LABELS", None),
}


def s(v: str) -> str:
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def num(v: float | int) -> str:
    assert not isinstance(v, bool)
    r = repr(v)
    return r[:-2] if r.endswith(".0") else r


def value(v: object) -> str:
    if v is None:
        return "null"
    if isinstance(v, str):
        return s(v)
    if isinstance(v, bool):
        raise TypeError("bool option")
    if isinstance(v, int):
        return str(v)
    raise TypeError(type(v))


def options(field: str, opts: tuple) -> str:
    if field in CUT_SELECTS:
        labels, prefix = CUT_SELECTS[field]
        table = getattr(C, labels)
        if prefix is None:
            assert list(opts) == list(table.items()), field
            return f"Object.entries({labels})"
        assert list(opts) == [(None, prefix), *sorted(table.items())], field
        return f'[[null, {s(prefix)}], ...sorted(Object.entries({labels}), (e) => e[0])]'
    return "[" + ", ".join(f"[{value(v)}, {s(lbl)}]" for v, lbl in opts) + "]"


def is_int_range(r: C.RangeField) -> bool:
    ints = (isinstance(r.lo, int), isinstance(r.hi, int))
    assert ints[0] == ints[1], r
    assert not isinstance(r.lo, bool)
    return ints[0]


def range_call(fn: str, r: C.RangeField) -> str:
    tail = ", true" if is_int_range(r) else ""
    return f"{fn}({s(r.field)}, {s(r.label)}, {num(r.lo)}, {num(r.hi)}{tail})"


def color_call(c: C.ColorField, *, helper: bool) -> str:
    if helper:
        extra = "" if c.optional else ", false"
        return f"color({s(c.field)}, {s(c.label)}{extra})"
    return f"colorField({s(c.field)}, {s(c.label)}, {'true' if c.optional else 'false'})"


def slot(g: C.GarmentSlot) -> str:
    parts = []
    if g.ranges:
        parts.append("ranges: [" + ", ".join(range_call("range", r) for r in g.ranges) + "]")
    if g.bools:
        parts.append("bools: [" + ", ".join(f"bool({s(b.field)}, {s(b.label)})" for b in g.bools) + "]")
    if g.selects:
        parts.append(
            "selects: ["
            + ", ".join(f"selectField({s(x.field)}, {s(x.label)}, {options(x.field, x.options)})" for x in g.selects)
            + "]"
        )
    if g.requires is not None:
        parts.append(f"requires: {s(g.requires)}")
    # the helper `color` is `_color`, whose `optional` default is True
    args = [s(g.id), s(g.label), color_call(g.color, helper=True)]
    if parts:
        args.append("{ " + ", ".join(parts) + " }")
    one = f"garmentSlot({', '.join(args)})"
    if len(one) <= 110:
        return one
    inner = ",\n".join("  " + a for a in args)
    return f"garmentSlot(\n{inner},\n)"


def labels_table(name: str, table: dict) -> str:
    rows = "\n".join(f"  {s(k)}: {s(v)}," for k, v in table.items())
    return f"export const {name}: Readonly<Record<string, string>> = {{\n{rows}\n}};"


def tuple_const(name: str, items: tuple[str, ...]) -> str:
    return f"export const {name}: readonly string[] = [{', '.join(s(i) for i in items)}];"


def source_comments() -> list[tuple[int, str]]:
    """Every whole-line comment of `catalogue.py` as (line, text without the marker), in order."""
    src = Path(C.__file__).read_text()
    out = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT and tok.line.strip().startswith("#"):
            out.append((tok.start[0], tok.string[1:].strip()))
    return out


def statement_ends() -> dict[str, int]:
    """The last line of the top-level statement that assigns each name."""
    tree = ast.parse(Path(C.__file__).read_text())
    ends: dict[str, int] = {}
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        for tg in targets:
            if isinstance(tg, ast.Name):
                ends.setdefault(tg.id, node.end_lineno)
    return ends


# Comments above this line of `catalogue.py` belong to the dataclasses, which are in `catalogue-types.ts`.
FIRST_TABLE_LINE = 152


def main() -> None:
    body: list[str] = []
    emitted: set[str] = set()
    comments = [(ln, tx) for ln, tx in source_comments() if ln >= FIRST_TABLE_LINE]
    ends = statement_ends()
    used = 0

    def with_comments(name: str, chunk: str) -> str:
        """Put every comment up to this statement's last line in front of it, so none is lost."""
        nonlocal used
        lines = []
        while used < len(comments) and comments[used][0] <= ends[name]:
            lines.append("// " + comments[used][1] if comments[used][1] else "//")
            used += 1
        return "\n".join([*lines, chunk])

    names = [n for n in vars(C) if not n.startswith("_")]
    for n in names:
        v = getattr(C, n)
        if n in REGISTRY:
            assert isinstance(v, dict)
            body.append(with_comments(n, labels_table(n, v)))
            reg, msg = REGISTRY[n]
            args = f"{n}, {reg}" + (f", {s(msg)}" if msg else "")
            body.append(f"assertKeysEqual({args});")
            emitted.add(n)
        elif isinstance(v, C.GarmentSlot):
            body.append(with_comments(n, f"export const {n}: GarmentSlot = {slot(v)};"))
            emitted.add(n)
        elif n == "GARMENTS":
            ids = [next(k for k in names if getattr(C, k) is g) for g in v]
            rows = "\n".join(f"  {k}," for k in ids)
            body.append(with_comments(n, f"export const GARMENTS: readonly GarmentSlot[] = [\n{rows}\n];"))
            emitted.add(n)
        elif n == "COLORS":
            rows = "\n".join(f"  {color_call(c, helper=False)}," for c in v)
            body.append(with_comments(n, f"export const COLORS: readonly ColorField[] = [\n{rows}\n];"))
            emitted.add(n)
        elif isinstance(v, C.RangeField):
            ints = ", true" if is_int_range(v) else ""
            lo = num(v.lo)
            if n == "AGE":
                assert v.lo == ch.ADULT_FACE_AGE
                lo = "ADULT_FACE_AGE"  # the lower end is the constant, not a copy of its value
            body.append(
                with_comments(
                    n,
                    f"export const {n}: RangeField = rangeField({s(v.field)}, {s(v.label)}, {lo}, {num(v.hi)}{ints});",
                )
            )
            emitted.add(n)
        elif isinstance(v, C.BoolField):
            body.append(with_comments(n, f"export const {n}: BoolField = boolField({s(v.field)}, {s(v.label)});"))
            emitted.add(n)
        elif n == "SKIN_SWATCHES":
            rows = "\n".join(f"  [{s(a)}, {s(b)}]," for a, b in v)
            body.append(with_comments(n, f"export const SKIN_SWATCHES: readonly (readonly [string, string])[] = [\n{rows}\n];"))
            emitted.add(n)
        elif n == "FACE_RANGES":
            rows = "\n".join(f"  {range_call('faceRange', r)}," for r in v)
            body.append(with_comments(n, f"export const FACE_RANGES: readonly RangeField[] = [\n{rows}\n];"))
            emitted.add(n)
        elif n == "FACE_BOOLS":
            rows = "\n".join(f"  faceBool({s(b.field)}, {s(b.label)})," for b in v)
            body.append(with_comments(n, f"export const FACE_BOOLS: readonly BoolField[] = [\n{rows}\n];"))
            emitted.add(n)
        elif n == "FACE_SCAR":
            body.append(
                with_comments(
                    n,
                    f"export const FACE_SCAR: SelectField = faceSelect({s(v.field)}, {s(v.label)}, {options(v.field, v.options)});",
                )
            )
            emitted.add(n)
        elif n == "FACE_SELECTS":
            assert v == (C.FACE_SCAR,)
            body.append(with_comments(n, "export const FACE_SELECTS: readonly SelectField[] = [FACE_SCAR];"))
            emitted.add(n)
    # the hand and grip tuples come before their labels in the TypeScript, as the Python imports them first
    header_tuples = [
        "// `character.py` HAND_STYLES and GRIP_STYLES. The TypeScript modules do not export them under these names, so",
        "// they are generated here (a copy, not a link to another module). `assertKeysEqual` ties the labels to them.",
        tuple_const("HAND_STYLES", ch.HAND_STYLES),
        tuple_const("GRIP_STYLES", ch.GRIP_STYLES),
    ]
    # the comments between the statements that are not data (the asserts) rode along with the next table; any
    # left after the last one would be lost
    assert used == len(comments), f"{len(comments) - used} comments of catalogue.py were not placed"
    # every public name that is data must have been emitted (names imported from character.py or presets.py,
    # classes, functions and modules are not data of this module)
    skipped = [
        n
        for n in names
        if n not in emitted
        and not isinstance(getattr(C, n), type)
        and not callable(getattr(C, n))
        and not hasattr(getattr(C, n), "__file__")
        and not any(getattr(m, n, None) is getattr(C, n) for m in (ch, presets))
        and n not in ("annotations",)
    ]
    assert not skipped, f"catalogue data not emitted: {skipped}"

    head = f'''// GENERATED by harness/ts_port/gen_catalogue_tables.py from `catalogue.py`. Do not edit; run the script again.
// The comments that say why each range has its bounds are in `catalogue.py` (lines 155 to 700), which stays the record.

import {{ BODY_TYPES }} from "./body.ts";
import {{ BOOT_CUTS, SKIRT_CUTS }} from "./body-parts-tables.ts";
import {{ FINISHES }} from "./character.ts";
import {{ HAIRSTYLES }} from "./core-head.ts";
import {{ COAT_CUTS, SLEEVE_CUTS }} from "./core-limbs-tables.ts";
import {{ BELT_CUTS, COLLAR_CUTS }} from "./garments-tables.ts";
import {{ HAIR_CLIPS }} from "./hair.ts";
import {{ ADULT_FACE_AGE }} from "./model.ts";
import {{ sorted }} from "./pynum.ts";
import {{
  assertKeysEqual,
  bool,
  boolField,
  color,
  colorField,
  faceBool,
  faceRange,
  faceSelect,
  garmentSlot,
  range,
  rangeField,
  selectField,
}} from "./catalogue-types.ts";
import type {{ BoolField, ColorField, GarmentSlot, RangeField, SelectField }} from "./catalogue-types.ts";

'''
    text = head + "\n".join(header_tuples) + "\n\n" + "\n".join(body) + "\n"
    OUT.write_text(text)
    print(f"wrote {OUT} ({text.count(chr(10))} lines)", file=sys.stderr)


if __name__ == "__main__":
    main()
