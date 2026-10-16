"""Emit the `core-head` module of the TypeScript port from its two templates, so no coordinate is ever typed by hand.

    PY harness/ts_port/gen_core_head.py [--force] [--out-dir DIR]

Reads `gen_core_head.tpl.ts` and `gen_core_head_tables.tpl.ts` (hand-written TypeScript with directives, below) and
writes `ts/src/core-head.ts` and `ts/src/core-head-tables.ts`. The output is a first draft that is then owned by hand: once
a file is in `ts/src/`, edit it there. Running this again overwrites it, so it refuses unless `--force` is given.

Directives, each alone on a line (the indentation of the line is the indentation the output gets):

    //@lead NAME        the comments that lead module-level NAME in character.py, as `//` lines
    //@doc NAME         NAME's docstring, as a JSDoc block
    //@const NAME       the comments that lead NAME, then its assignment as `export const NAME ...;`
    //@py A-B [name:Type ...]   the Python lines A to B (whole statements), translated; a `name:Type` gives an unannotated
                        assignment its type
    //@items A-B        the Python lines A to B as items of a list the template has opened (no `;`)
    //@comments A-B     only the comment lines among lines A to B

The translator is deliberately small. It turns tuples into arrays, a leading `*` into `...`, `#` into `//`, `None` into
`null`, snake_case locals into camelCase (attributes after a `.` stay as they are: they are dataclass fields), a
module-level name into its TypeScript name (`_hair_fall` -> `hairFall`, `_HAIR_CHEEK_Y` -> `HAIR_CHEEK_Y`), and a
statement `x: T = e` into `const x: T = e;`. Anything else (`if`, `for`, `**`, `%`, `==`, slices, negative indices,
`math.`, keyword arguments, nested `def`) raises, so that it is written by hand where a hazard is decided. Every `/` it
passes is listed, so that each is checked against the hazard ledger.
"""

from __future__ import annotations

import ast
import io
import keyword
import re
import sys
import tokenize
from pathlib import Path

import _bootstrap  # noqa: F401

_bootstrap.assert_package_location()

import anime_character_creator.character as ch  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "src" / "anime_character_creator" / "character.py"
LINES = SRC.read_text().split("\n")
TREE = ast.parse(SRC.read_text())

# --------------------------------------------------------------------------------------------------------------------
# The module's nodes and their leading comments

NODES: dict[str, ast.AST] = {}
LEAD: dict[str, list[str]] = {}
_prev_end = 0
for node in TREE.body:
    names: list[str] = []
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        names = [node.name]
    elif isinstance(node, ast.Assign):
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if not names:
            names = [e.id for t in node.targets if isinstance(t, ast.Tuple) for e in t.elts if isinstance(e, ast.Name)]
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        names = [node.target.id]
    start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
    lead = [ln for ln in LINES[_prev_end : start - 1]]
    # A decorator line belongs to the node, not to the comments before it.
    while lead and lead[0].strip() == "":
        lead.pop(0)
    while lead and lead[-1].strip() == "":
        lead.pop()
    for n in names:
        # A name defined twice (`_straight`) keeps the LAST definition: it is the one Python uses.
        NODES[n] = node
        LEAD[n] = lead
    _prev_end = node.end_lineno or node.lineno

MODULE_FUNCS = {n for n, nd in NODES.items() if isinstance(nd, ast.FunctionDef)}
MODULE_CONSTS = {n for n, nd in NODES.items() if not isinstance(nd, ast.FunctionDef)}

# --------------------------------------------------------------------------------------------------------------------
# Names

SPECIAL_NAMES = {"abs": "Math.abs", "max": "pyMax", "min": "pyMin", "None": "null", "True": "true", "False": "false"}
SNAKE = re.compile(r"_([a-z0-9])")


def camel(name: str) -> str:
    stripped = name.lstrip("_")
    return stripped[:1] + SNAKE.sub(lambda m: m.group(1).upper(), stripped[1:])


def ts_name(name: str, after_dot: bool) -> str:
    if after_dot:
        return name
    if name in SPECIAL_NAMES:
        return SPECIAL_NAMES[name]
    if name in MODULE_FUNCS:
        return camel(name)
    if name in MODULE_CONSTS:
        return name.lstrip("_")
    if name == "_":
        return "_"
    if keyword.iskeyword(name) or name in {"math", "range", "len", "list", "tuple", "float", "int", "sorted", "enumerate", "zip"}:
        raise Unsupported(f"name {name!r}")
    if name.upper() == name and "_" in name:
        raise Unsupported(f"unknown constant {name!r}")
    return camel(name) if "_" in name else name


class Unsupported(Exception):
    pass


# --------------------------------------------------------------------------------------------------------------------
# Types

def ts_type(text: str) -> str:
    """A Python annotation as a TypeScript type, for the shapes this module uses."""
    tree = ast.parse(text.strip(), mode="eval").body

    def go(n: ast.AST) -> str:
        if isinstance(n, ast.Name):
            return {"float": "number", "int": "number", "str": "string", "bool": "boolean"}.get(n.id, n.id)
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name):
            args = n.slice.elts if isinstance(n.slice, ast.Tuple) else [n.slice]
            if n.value.id == "list":
                return f"{go(args[0])}[]"
            if n.value.id == "tuple":
                if len(args) == 2 and isinstance(args[1], ast.Constant) and args[1].value is Ellipsis:
                    return f"readonly {go(args[0])}[]"
                return "[" + ", ".join(go(a) for a in args) + "]"
        raise Unsupported(f"type {text!r}")

    return go(tree)


# --------------------------------------------------------------------------------------------------------------------
# The translator

SLASHES: list[str] = []
ALLOWED_OPS = {"+", "-", "*", "/", "(", ")", "[", "]", ",", ".", "=", ":"}


def translate(
    first: int, last: int, indent: int, label: str, items: bool = False, hints: dict[str, str] | None = None
) -> list[str]:
    """Python lines `first`..`last` (1-based, inclusive), as TypeScript lines at `indent` spaces."""
    raw = LINES[first - 1 : last]
    base = len(raw[0]) - len(raw[0].lstrip())
    for ln in raw:
        if ln.strip() and (len(ln) - len(ln.lstrip())) < base:
            raise Unsupported(f"{label}: a line is less indented than the first one")
    text = "\n".join(ln[base:] if ln.strip() else "" for ln in raw) + "\n"
    out_lines = [list(ln) for ln in text.split("\n")[:-1]]  # characters, so that edits keep their columns
    toks = [t for t in tokenize.generate_tokens(io.StringIO(text).readline)]
    edits: list[tuple[int, int, int, str]] = []  # row (0-based), col, length, replacement
    logical: list[list[tokenize.TokenInfo]] = []
    cur: list[tokenize.TokenInfo] = []
    comments: list[tokenize.TokenInfo] = []
    for t in toks:
        if t.type in (tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER):
            continue
        if t.type == tokenize.COMMENT:
            comments.append(t)
            continue
        if t.type == tokenize.NL:
            continue
        if t.type == tokenize.NEWLINE:
            if cur:
                logical.append(cur)
            cur = []
            continue
        cur.append(t)
    if cur:
        logical.append(cur)

    def edit(t: tokenize.TokenInfo, new: str) -> None:
        edits.append((t.start[0] - 1, t.start[1], t.end[1] - t.start[1], new))

    assigned: set[str] = set()
    for lt in logical:
        mark = len(edits)
        # parentheses: call, tuple or grouping
        stack: list[list[int | bool]] = []
        for i, t in enumerate(lt):
            if t.type == tokenize.OP and t.string in "([":
                prev = lt[i - 1] if i else None
                is_call = prev is not None and (
                    (prev.type == tokenize.NAME and not keyword.iskeyword(prev.string) and prev.string not in ("None", "True", "False"))
                    or prev.string in (")", "]")
                )
                stack.append([i, is_call, False])
                if t.string == "[" and is_call:
                    nxt = lt[i + 1] if i + 1 < len(lt) else None
                    if nxt is not None and nxt.string == "-":
                        raise Unsupported(f"{label}: negative index at line {first + t.start[0] - 1}")
            elif t.type == tokenize.OP and t.string in ")]":
                top = stack.pop()
                j = int(top[0])
                if t.string == ")" and not top[1]:
                    is_empty = i == j + 1
                    if top[2] or is_empty:
                        edit(lt[j], "[")
                        edit(t, "]")
            elif t.type == tokenize.OP and t.string == ",":
                if stack:
                    stack[-1][2] = True
        depth = 0
        eq0 = None
        for i, t in enumerate(lt):
            if t.string in "([":
                depth += 1
            elif t.string in ")]":
                depth -= 1
            elif depth == 0 and t.type == tokenize.OP and t.string == "=":
                eq0 = i
                break
        for i, t in enumerate(lt):
            prev = lt[i - 1] if i else None
            if eq0 is not None and i < eq0:
                continue  # the head of an assignment is rewritten whole, below
            if t.type == tokenize.NAME:
                if t.string == "return" and i == 0:
                    continue
                after_dot = prev is not None and prev.string == "."
                nxt = lt[i + 1] if i + 1 < len(lt) else None
                if nxt is not None and nxt.string == "=" and not (i == 0) and not after_dot:
                    # keyword argument or an inner assignment
                    depth_hint = any(x.string in "([" for x in lt[:i])
                    if depth_hint:
                        raise Unsupported(f"{label}: keyword argument at line {first + t.start[0] - 1}")
                if t.string == "_" and (i == 0 or prev.string == ","):
                    continue  # an elision in a destructuring, handled with the statement head
                try:
                    new = ts_name(t.string, after_dot)
                except Unsupported as ex:
                    raise Unsupported(f"{label}: Python line {first + t.start[0] - 1}: {ex}") from None
                if new != t.string:
                    edit(t, new)
            elif t.type == tokenize.OP:
                if t.string == "*" and prev is not None and prev.string in ("(", "[", ",") and prev.type == tokenize.OP:
                    edit(t, "...")
                elif t.string not in ALLOWED_OPS:
                    raise Unsupported(f"{label}: operator {t.string!r} at line {first + t.start[0] - 1}")
                if t.string == "/":
                    SLASHES.append(f"{label}: line {first + t.start[0] - 1}: {LINES[first + t.start[0] - 2].strip()[:90]}")
            elif t.type == tokenize.STRING:
                if t.string.startswith(("f", "F", "r", "b")) or t.string.startswith(('"""', "'''")):
                    raise Unsupported(f"{label}: string {t.string[:12]!r}")
                if t.string.startswith("'"):
                    raise Unsupported(f"{label}: single-quoted string {t.string[:12]!r}")
        if items:
            continue  # list items (`a, b,` lines inside a bracket the template opened): no statement, no `;`
        # the statement head
        head = lt[0]
        eqs = []
        depth = 0
        for i, t in enumerate(lt):
            if t.string in "([":
                depth += 1
            elif t.string in ")]":
                depth -= 1
            elif depth == 0 and t.type == tokenize.OP and t.string == "=":
                eqs.append(i)
        rhs_start = 0
        if head.string == "return":
            rhs_start = 1
        elif eqs:
            e = eqs[0]
            lhs = lt[:e]
            colon = next((i for i, t in enumerate(lhs) if t.string == ":"), None)
            if colon is not None:
                if colon != 1 or lhs[0].type != tokenize.NAME:
                    raise Unsupported(f"{label}: annotated target")
                name = ts_name(lhs[0].string, False)
                ann = text.split("\n")[lhs[colon].start[0] - 1][lhs[colon].end[1] : lhs[-1].end[1]]
                new_head = f"const {name}: {ts_type(ann)} ="
            elif all(t.type == tokenize.NAME or t.string == "," for t in lhs):
                names_ = [t.string for t in lhs if t.string != ","]
                if len(names_) == 1:
                    hint = (hints or {}).get(names_[0])
                    new_head = f"const {ts_name(names_[0], False)}{': ' + hint if hint else ''} ="
                else:
                    new_head = "const [" + ", ".join("" if n == "_" else ts_name(n, False) for n in names_) + "] ="
                for n in names_:
                    if n != "_":
                        if n in assigned:
                            raise Unsupported(f"{label}: {n!r} is assigned twice")
                        assigned.add(n)
            else:
                raise Unsupported(f"{label}: assignment target at line {first + head.start[0] - 1}")
            if colon is not None:
                assigned.add(lhs[0].string)
            # drop the edits made on the head's tokens, replace the whole head
            if lhs[0].start[0] != lt[e].end[0]:
                raise Unsupported(f"{label}: head over several lines")
            row = head.start[0] - 1
            end_col = lt[e].end[1]
            edits[mark:] = [ed for ed in edits[mark:] if not (ed[0] == row and head.start[1] <= ed[1] < end_col)]
            edits.append((row, head.start[1], end_col - head.start[1], new_head))
            rhs_start = e + 1
        elif head.type == tokenize.NAME and head.string not in ("return",):
            raise Unsupported(f"{label}: statement at line {first + head.start[0] - 1}: {LINES[first + head.start[0] - 2].strip()[:60]}")
        # a bare tuple on the right-hand side
        depth = 0
        bare = False
        for t in lt[rhs_start:]:
            if t.string in "([":
                depth += 1
            elif t.string in ")]":
                depth -= 1
            elif depth == 0 and t.string == ",":
                bare = True
        # the end of the statement (applied before the closing bracket of a bare tuple, which lands at the same column)
        last_t = lt[-1]
        edits.append((last_t.end[0] - 1, last_t.end[1], 0, ";"))
        if bare:
            first_t = lt[rhs_start]
            edits.append((first_t.start[0] - 1, first_t.start[1], 0, "["))
            edits.append((last_t.end[0] - 1, last_t.end[1], 0, "]"))
    for c in comments:
        body = c.string
        if "fmt: skip" in body or "fmt: off" in body or "fmt: on" in body:
            edits.append((c.start[0] - 1, c.start[1], len(body), ""))
        else:
            edits.append((c.start[0] - 1, c.start[1], 1, "//"))
    # apply the edits: last first, and at one column an insertion after a replacement
    for row, col, length, new in sorted(edits, key=lambda e: (e[0], e[1], e[2] != 0), reverse=True):
        line = out_lines[row]
        out_lines[row] = line[:col] + list(new) + line[col + length :]
    result = []
    for ln in out_lines:
        s = "".join(ln).rstrip()
        if not s:
            result.append("")
            continue
        lead = len(s) - len(s.lstrip())
        result.append(" " * (indent + lead // 2) + s.lstrip())
    return result


# --------------------------------------------------------------------------------------------------------------------
# Comments, docstrings, constants

def comment_lines(name: str, indent: int) -> list[str]:
    out = []
    for ln in LEAD.get(name, []):
        s = ln.strip()
        if s == "":
            out.append("")
        elif s.startswith("#"):
            out.append(" " * indent + "//" + s[1:])
        else:
            raise Unsupported(f"leading line of {name} is not a comment: {ln!r}")
    return out


def doc_lines(name: str, indent: int) -> list[str]:
    node = NODES[name]
    doc = ast.get_docstring(node, clean=True)
    if doc is None:
        return []
    doc = doc.replace("*/", "*\\/")
    pad = " " * indent
    if "\n" not in doc and len(doc) < 100:
        return [f"{pad}/** {doc} */"]
    body = [f"{pad} * {ln}".rstrip() for ln in doc.split("\n")]
    return [f"{pad}/**", *body, f"{pad} */"]


def const_lines(name: str, indent: int) -> list[str]:
    node = NODES[name]
    out = comment_lines(name, indent)
    lines = translate(node.lineno, node.end_lineno or node.lineno, indent, name)
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        # `NAME = value` has no annotation: `const NAME = value;`
        pass
    out.extend(lines)
    out[len(out) - len(lines)] = out[len(out) - len(lines)].replace("const ", "export const ", 1)
    return out


def expand(template: str) -> str:
    out: list[str] = []
    for ln in template.split("\n"):
        m = re.match(r"^(\s*)//@(lead|doc|const|py|items|comments|imports)(?:\s+(.*))?$", ln)
        if not m:
            out.append(ln)
            continue
        pad, kind, arg = m.group(1), m.group(2), (m.group(3) or "").strip()
        indent = len(pad)
        if kind == "imports":
            out.append(ln)  # filled in after the file is expanded, once the names it uses are known
            continue
        if kind == "comments":
            a, b = arg.split("-")
            for k in range(int(a), int(b) + 1):
                cs = LINES[k - 1].strip()
                if cs.startswith("#"):
                    out.append(" " * indent + "//" + cs[1:])
            continue
        if kind == "lead":
            out.extend(comment_lines(arg, indent))
        elif kind == "doc":
            out.extend(doc_lines(arg, indent))
        elif kind == "const":
            out.extend(const_lines(arg, indent))
        else:
            rng, *hint_args = arg.split()
            hints = dict(h.split(":", 1) for h in hint_args)
            a, b = rng.split("-")
            out.extend(translate(int(a), int(b), indent, f"{kind} {arg}", items=(kind == "items"), hints=hints))
    return "\n".join(out)


# --------------------------------------------------------------------------------------------------------------------
# Imports: a `//@imports [-name ...]` line becomes the import block for the names the file uses and does not define

TS_DIR = ROOT / "ts" / "src"
OTHER_MODULES = ["pynum", "pyjson", "pyvalue", "tables", "character", "colorutil", "model", "params", "plain", "skeleton"]
DECL = re.compile(r"^export\s+(?:declare\s+)?(function|const|class|interface|type)\s+(\w+)", re.M)


def exports_of(text: str) -> dict[str, bool]:
    """name -> is it only a type."""
    out = {}
    for kind, name in DECL.findall(text):
        out[name] = kind in ("interface", "type")
    for block in re.findall(r"^export\s*(?:type\s*)?\{([^}]*)\}", text, re.M):
        for item in block.split(","):
            if item.strip():
                out[item.strip().split(" as ")[-1].strip()] = False
    return out


def strip_noise(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"^export\s*(?:\*|\{[^}]*\})\s*from\s*\"[^\"]*\";", "", text, flags=re.M)
    # a line with a template literal keeps its quotes: `"${fmt1(x)}"` is code between two quotes
    return "\n".join(ln if "`" in ln else re.sub(r'"(?:[^"\\]|\\.)*"', '""', ln) for ln in text.split("\n"))


def fill_imports(text: str, target: str, registry: dict[str, tuple[str, bool]]) -> str:
    m = re.search(r"^//@imports(.*)$", text, re.M)
    if not m:
        return text
    exclude = {w[1:] for w in m.group(1).split() if w.startswith("-")}
    body = strip_noise(text)
    defined = set(exports_of(body)) | set(re.findall(r"^(?:export\s+)?(?:function|const|let)\s+(\w+)", body, re.M))
    used = {name for dots, name in re.findall(r"(\.{1,3})?([A-Za-z_]\w*)", body) if dots != "."}
    by_module: dict[str, list[tuple[str, bool]]] = {}
    for name in sorted(used - defined - exclude):
        if name in registry and registry[name][0] != target:
            mod, is_type = registry[name]
            by_module.setdefault(mod, []).append((name, is_type))
    lines = []
    order = ["character", "colorutil", "model", "params", "plain", "pyjson", "pynum", "pyvalue", "skeleton", "tables", "core-head-tables", "core-head-cuts", "core-head-crop"]
    for mod in sorted(by_module, key=lambda k: order.index(k) if k in order else 99):
        names = by_module[mod]
        if all(t for _, t in names):
            items = ", ".join(n for n, _ in names)
            lines.append(f'import type {{ {items} }} from "./{mod}.ts";')
        else:
            items = ", ".join(("type " if t else "") + n for n, t in names)
            single = f'import {{ {items} }} from "./{mod}.ts";'
            if len(single) <= 120:
                lines.append(single)
            else:
                lines.append("import {\n" + "".join(f"  {('type ' if t else '') + n},\n" for n, t in names) + f'}} from "./{mod}.ts";')
    return text[: m.start()] + "\n".join(lines) + text[m.end() :]


def check_comments(generated: str) -> None:
    """Every comment of every name of the module, in the Python, must be somewhere in the output (the design record)."""
    import json

    have = {ln.strip() for ln in generated.split("\n")}
    have |= {ln.strip() for ln in generated.split("\n") if "//" in ln for ln in [ln[ln.index("//") :]]}
    names = json.loads((HERE / "modules.json").read_text())["core-head"]["names"]
    # Already ported elsewhere (character.ts, model.ts), or not drawn here.
    elsewhere = {"_soft", "_HEAD_SEGMENTS", "_SKULL_NARROW", "_JAW_START_Y", "_JAW_EASE", "_head_pt", "_head_shape", "aged_face"}
    missing: list[str] = []
    for n in names:
        if n["name"] in elsewhere:
            continue
        node = NODES[n["name"]]
        first = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
        rng = list(range(first, (node.end_lineno or first) + 1)) + [
            LINES.index(x) + 1 for x in LEAD.get(n["name"], []) if x.strip().startswith("#") and x in LINES
        ]
        for k in sorted(set(rng)):
            text = LINES[k - 1].strip()
            if text.startswith("#"):
                want = "//" + text[1:]
                if want not in have and "fmt: skip" not in text:
                    missing.append(f"{n['name']}: line {k}: {text[:70]}")
    print(f"{len(missing)} comment lines of the Python are missing from the output")
    for m in missing[:30]:
        print("  ", m)


TEMPLATES = [
    ("gen_core_head_tables.tpl.ts", "core-head-tables.ts"),
    ("gen_core_head_cuts.tpl.ts", "core-head-cuts.ts"),
    ("gen_core_head_crop.tpl.ts", "core-head-crop.ts"),
    ("gen_core_head.tpl.ts", "core-head.ts"),
]


def main() -> None:
    force = "--force" in sys.argv
    out_dir = ROOT / "ts" / "src"
    if "--out-dir" in sys.argv:
        out_dir = Path(sys.argv[sys.argv.index("--out-dir") + 1])
    all_text = ""
    registry: dict[str, tuple[str, bool]] = {}
    for mod in OTHER_MODULES:
        for name, is_type in exports_of((TS_DIR / f"{mod}.ts").read_text()).items():
            registry.setdefault(name, (mod, is_type))
    for tpl, target in TEMPLATES:
        dest = out_dir / target
        if dest.exists() and not force:
            raise SystemExit(f"{dest} exists and is hand-owned now; pass --force to overwrite")
        text = expand((HERE / tpl).read_text())
        text = fill_imports(text, target[:-3], registry)
        for name, is_type in exports_of(text).items():
            if not name.startswith("_"):
                registry[name] = (target[:-3], is_type)
        dest.write_text(text)
        all_text += text + "\n"
        print("wrote", dest, len(text.split("\n")), "lines")
    check_comments(all_text)
    (out_dir / "_slashes.txt").write_text("\n".join(SLASHES) + "\n") if "--slashes" in sys.argv else None
    print(f"{len(SLASHES)} divisions in translated lines")
    if "--slashes" in sys.argv:
        print("\n".join(SLASHES))


if __name__ == "__main__":
    main()
