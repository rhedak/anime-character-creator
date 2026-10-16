"""Emit the parameter types and the field registry (`ts/src/params.ts`) from the Python dataclasses.

    PY harness/ts_port/gen_types.py [--force]

TypeScript has no runtime types, and the code reflects on the dataclasses in four places (`catalogue`,
`urlstate`, `skeleton`, the companion's `render_ops.coerce`), so the field list, the type tags and the defaults
have to exist as data. This writes them once, with the comment above each field carried over as JSDoc (those
comments are the design record). After that the file is hand-owned; this refuses to overwrite it without --force.
"""

from __future__ import annotations

import ast
import dataclasses
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

from anime_character_creator import character as ch  # noqa: E402
from anime_character_creator.skeleton import BodyProfile, Skeleton  # noqa: E402

_bootstrap.assert_package_location()

OUT = Path(__file__).resolve().parents[2] / "ts" / "src" / "params.ts"
CLASSES = [("Outfit", ch.Outfit), ("FaceStyle", ch.FaceStyle), ("Expression", ch.Expression), ("CharacterParams", ch.CharacterParams)]
TAGS = {"str": "string", "float": "number", "int": "number", "bool": "boolean"}


def tag_of(ann: str) -> tuple[str, bool]:
    parts = [p.strip() for p in ann.split("|")]
    nullable = "None" in parts
    base = [p for p in parts if p != "None"]
    if len(base) != 1 or base[0] not in TAGS and base[0] not in {"Outfit", "FaceStyle"}:
        raise SystemExit(f"unexpected annotation {ann!r}")
    return base[0], nullable


def comments_above(source_lines: list[str], lineno: int) -> list[str]:
    out: list[str] = []
    j = lineno - 2
    while j >= 0 and source_lines[j].strip().startswith("#"):
        out.append(source_lines[j].strip().lstrip("#").strip())
        j -= 1
    return list(reversed(out))


def field_comments(cls: type) -> dict[str, list[str]]:
    import inspect

    src, start = inspect.getsourcelines(cls)
    tree = ast.parse("".join(src))
    node = tree.body[0]
    assert isinstance(node, ast.ClassDef)
    out: dict[str, list[str]] = {}
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            out[stmt.target.id] = comments_above(src, stmt.lineno)
    return out


def lit(v: object) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        r = repr(v)
        return r[:-2] if r.endswith(".0") else r
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    raise TypeError(type(v))


def jsdoc(lines: list[str], indent: str) -> list[str]:
    if not lines:
        return []
    safe = [ln.replace("*/", "* /") for ln in lines]
    if len(safe) == 1:
        return [f"{indent}/** {safe[0]} */"]
    return [f"{indent}/**", *[f"{indent} * {ln}".rstrip() for ln in safe], f"{indent} */"]


def main() -> None:
    if OUT.exists() and "--force" not in sys.argv:
        raise SystemExit(f"{OUT} exists and is hand-owned now; pass --force to overwrite")
    L: list[str] = [
        "// Generated once by harness/ts_port/gen_types.py from the Python dataclasses, then owned by hand.",
        "// The registry is the one thing TypeScript cannot reflect: field names, type tags and defaults.",
        "",
        'export type FieldType = "str" | "float" | "int" | "bool" | "Outfit" | "FaceStyle";',
        "",
        "export interface FieldSpec {",
        "  readonly name: string;",
        "  readonly type: FieldType;",
        "  readonly nullable: boolean;",
        "  readonly default: string | number | boolean | null;",
        "}",
        "",
    ]
    defaults_text: list[str] = []
    for name, cls in CLASSES:
        comments = field_comments(cls)
        doc = (cls.__doc__ or "").strip().splitlines()
        L += jsdoc([ln.strip() for ln in doc], "")
        L.append(f"export interface {name} {{")
        specs: list[str] = []
        base = cls() if name != "CharacterParams" else cls()
        for f in dataclasses.fields(cls):
            ann = str(f.type)
            tag, nullable = tag_of(ann)
            ts = {"Outfit": "Outfit", "FaceStyle": "FaceStyle"}.get(tag, TAGS.get(tag))
            L += jsdoc(comments.get(f.name, []), "  ")
            L.append(f"  readonly {f.name}: {ts}{' | null' if nullable else ''};")
            default = getattr(base, f.name)
            d = "null" if tag in ("Outfit", "FaceStyle") else lit(default)
            specs.append(f'  {{ name: "{f.name}", type: "{tag}", nullable: {str(nullable).lower()}, default: {d} }},')
        L.append("}")
        L.append("")
        L.append(f"export const {name.upper()}_FIELDS: readonly FieldSpec[] = [")
        L += specs
        L.append("];")
        L.append("")
        if name != "CharacterParams":
            body = ", ".join(f"{f.name}: {lit(getattr(base, f.name))}" for f in dataclasses.fields(cls))
            defaults_text.append(f"export const DEFAULT_{name.upper()}: {name} = {{ {body} }};")
    # CharacterParams default last, nested
    base = ch.CharacterParams()
    parts = []
    for f in dataclasses.fields(ch.CharacterParams):
        if f.name == "outfit":
            parts.append("outfit: DEFAULT_OUTFIT")
        elif f.name == "face":
            parts.append("face: DEFAULT_FACESTYLE")
        else:
            parts.append(f"{f.name}: {lit(getattr(base, f.name))}")
    defaults_text.append("export const DEFAULT_CHARACTERPARAMS: CharacterParams = { " + ", ".join(parts) + " };")
    L += defaults_text
    L.append("")
    OUT.write_text("\n".join(L))
    print("wrote", OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
