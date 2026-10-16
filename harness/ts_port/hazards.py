"""AST ledger of every numeric/semantic hazard site in the frozen Python source.

Writes hazards.json next to this file and prints a summary table plus the
counts the TypeScript port plan claims, so they can be checked.

Run:
  PYTHONPATH=<ts worktree>/src <venv>/bin/python hazards.py

Each entry: {file, line, end_line, class, detail, snippet[, flag]}.
The ledger is a checklist a porter ticks off, so it favours completeness:
every site of a class is listed, even when it looks harmless.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import anime_character_creator as _acc

HERE = Path(__file__).resolve().parent
SRC = HERE.parent.parent / "src" / "anime_character_creator"
assert Path(_acc.__file__).resolve().is_relative_to(SRC.parent), _acc.__file__

FILES = [
    "character.py",
    "presets.py",
    "skeleton.py",
    "colorutil.py",
    "urlstate.py",
    "supporting.py",
    "catalogue.py",
    "attribution.py",
]
STDLIB_NS = {"json", "base64", "struct", "zlib", "re", "hashlib", "itertools", "math", "colorsys"}
CONTAINER_HINT = re.compile(
    r"(list|pts|points|items|paths|lines|dict|set|seq|stack|queue|rows|cols|parts|args|keys|values|strokes|segs|verts|"
    r"layers|els|elems|names|ids|data|stops|curves|pairs|group|bands|strands|locks|tips|ends)", re.I
)
STR_CALLS = {"str", "join", "format", "lower", "upper", "strip", "replace", "hex", "hexdigest", "escape", "title", "repr"}


def src_of(text: str, node: ast.AST) -> str:
    seg = ast.get_source_segment(text, node) or ""
    seg = " ".join(seg.split())
    return seg if len(seg) <= 160 else seg[:157] + "..."


def callee_name(f: ast.expr) -> str | None:
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        base = callee_name(f.value)
        return f"{base}.{f.attr}" if base else f.attr
    return None


def is_const(n: ast.expr) -> bool:
    if isinstance(n, ast.Constant):
        return True
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)) and isinstance(n.operand, ast.Constant):
        return True
    return False


def neg_possible(n: ast.expr) -> str | None:
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
        return "unary-minus"
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Sub):
        return "subtraction"
    if isinstance(n, ast.Name):
        return "name"
    return None


def const_neg_int(n: ast.expr) -> bool:
    return (
        isinstance(n, ast.UnaryOp)
        and isinstance(n.op, ast.USub)
        and isinstance(n.operand, ast.Constant)
    ) or (isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and n.value < 0)


class Ledger(ast.NodeVisitor):
    def __init__(self, fname: str, text: str):
        self.f = fname
        self.text = text
        self.out: list[dict] = []
        self.func_stack: list[str] = []
        self.imported: dict[str, str] = {}  # local name -> module.attr for stdlib from-imports
        self.mod_alias: dict[str, str] = {}  # alias -> module

    # --- helpers
    def add(self, node: ast.AST, cls: str, detail: str = "") -> None:
        e = {
            "file": self.f,
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "class": cls,
            "detail": detail,
            "snippet": src_of(self.text, node),
        }
        if self.f == "attribution.py" and (
            any("png" in fn.lower() for fn in self.func_stack) or "_PNG_" in e["snippet"]
        ):
            e["flag"] = "png-chunk-only"
        self.out.append(e)

    def generic(self, node):
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.func_stack.append(node.name)
        self.generic_visit(node)
        self.func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    # --- imports (to resolve aliases)
    def visit_Import(self, node):
        for a in node.names:
            if a.asname:
                self.mod_alias[a.asname] = a.name
                if a.name.split(".")[0] in STDLIB_NS or a.name.startswith("xml"):
                    self.add(node, "import_alias", f"import {a.name} as {a.asname}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        m = node.module or ""
        if m.split(".")[0] in STDLIB_NS or m.startswith("xml"):
            for a in node.names:
                self.imported[a.asname or a.name] = f"{m}.{a.name}"
                self.add(node, "import_from_stdlib", f"from {m} import {a.name}")
        self.generic_visit(node)

    # --- f-strings
    def visit_FormattedValue(self, node):
        spec = None
        if node.format_spec is not None:
            vals = node.format_spec.values
            if all(isinstance(v, ast.Constant) for v in vals):
                spec = "".join(v.value for v in vals)
            else:
                spec = "<dynamic>" + src_of(self.text, node.format_spec)
        if spec is not None:
            if spec in {".1f", ".2f", ".0f", ".3f", "02x"}:
                self.add(node, f"fstr:{spec}", "conv=%s" % node.conversion if node.conversion != -1 else "")
            else:
                self.add(node, "fstr:other", f"spec={spec!r}" + (f" conv={chr(node.conversion)}" if node.conversion != -1 else ""))
        if node.conversion != -1:
            self.add(node, "conv_" + chr(node.conversion), "!%s conversion" % chr(node.conversion))
        if spec is None and node.conversion == -1:
            v = node.value
            why = None
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                why = "str-constant"
            elif isinstance(v, ast.JoinedStr):
                why = "nested-fstring"
            elif isinstance(v, ast.Call):
                cn = (callee_name(v.func) or "").split(".")[-1]
                if cn in STR_CALLS:
                    why = f"call-{cn}"
            if why:
                self.add(node, "fstr_bare_obvious_str", why)
            else:
                self.add(node, "fstr_bare", type(node.value).__name__)
        self.generic_visit(node)

    # --- operators
    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Mod):
            if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                self.add(node, "mod", "str-format (%)")
            else:
                nl, nr = neg_possible(node.left), neg_possible(node.right)
                flag = []
                if nl:
                    flag.append(f"left:{nl}")
                if nr:
                    flag.append(f"right:{nr}")
                self.add(node, "mod", ("MAYBE-NEGATIVE " + ",".join(flag)) if flag else "operands constant/other")
        elif isinstance(node.op, ast.Pow):
            self.pow_site(node, node.right)
        elif isinstance(node.op, (ast.Div, ast.FloorDiv)):
            # Python raises ZeroDivisionError; JS gives Infinity or NaN. A constant non-zero divisor cannot raise.
            r = node.right
            if isinstance(r, ast.Constant) and isinstance(r.value, (int, float)) and r.value != 0:
                pass
            else:
                self.add(node, "div", "variable divisor: needs pyDiv or a proof it cannot be zero")
        self.generic_visit(node)

    def pow_site(self, node, exp):
        if isinstance(exp, ast.Constant) and isinstance(exp.value, int):
            d = f"integer exponent {exp.value}"
        elif isinstance(exp, ast.Constant) and isinstance(exp.value, float):
            d = f"fractional exponent {exp.value}"
        else:
            d = "non-constant exponent"
        self.add(node, "pow", d)

    def visit_AugAssign(self, node):
        if isinstance(node.op, ast.Mod):
            self.add(node, "mod", "augassign %=")
        if isinstance(node.op, ast.Pow):
            self.pow_site(node, node.value)
        opn = type(node.op).__name__
        tgt = type(node.target).__name__
        counter = (
            isinstance(node.target, ast.Name)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, int)
            and isinstance(node.op, (ast.Add, ast.Sub))
        )
        vk = type(node.value).__name__
        d = f"{opn} target={tgt} value={vk}"
        if isinstance(node.value, (ast.List, ast.ListComp, ast.Tuple)):
            d += " LIST-MUTATION"
        self.add(node, "augassign_counter" if counter else "augassign", d)
        self.generic_visit(node)

    # --- comparisons
    def visit_Compare(self, node):
        if len(node.ops) > 1:
            self.add(node, "chained_compare", " ".join(type(o).__name__ for o in node.ops))
        left = node.left
        for op, right in zip(node.ops, node.comparators):
            if isinstance(op, (ast.Eq, ast.NotEq)) and not is_const(left) and not is_const(right):
                self.add(node, "eq_nonconst", f"{type(op).__name__}")
            left = right
        self.generic_visit(node)

    # --- subscripts
    def visit_Subscript(self, node):
        sl = node.slice
        if isinstance(sl, ast.Slice):
            if sl.step is not None:
                neg = const_neg_int(sl.step)
                self.add(node, "stepped_slice", "negative step" if neg else "step")
            for nm, b in (("lower", sl.lower), ("upper", sl.upper)):
                if b is not None and const_neg_int(b):
                    self.add(node, "neg_slice_bound", nm)
                elif b is not None and neg_possible(b) in ("subtraction", "unary-minus"):
                    self.add(node, "slice_bound_maybe_neg", f"{nm}:{neg_possible(b)}")
        else:
            if const_neg_int(sl):
                self.add(node, "neg_subscript", "constant negative index")
            elif isinstance(sl, ast.UnaryOp) and isinstance(sl.op, ast.USub):
                self.add(node, "neg_subscript", "computed negative index")
            elif isinstance(sl, ast.BinOp) and isinstance(sl.op, ast.Sub):
                self.add(node, "subscript_maybe_neg", "index is subtraction")
        self.generic_visit(node)

    # --- calls
    def visit_Call(self, node):
        f = node.func
        cn = callee_name(f) or ""
        parts = cn.split(".")
        head, last = parts[0], parts[-1]
        kw = {k.arg for k in node.keywords}
        if isinstance(f, ast.Name):
            n = f.id
            if n == "round":
                nd = src_of(self.text, node.args[1]) if len(node.args) > 1 else ("ndigits=" + src_of(self.text, [k for k in node.keywords if k.arg == "ndigits"][0].value) if "ndigits" in kw else "none")
                self.add(node, "round", f"ndigits={nd}" if not nd.startswith("ndigits") else nd)
            elif n == "sum":
                a0 = node.args[0] if node.args else None
                self.add(node, "sum", f"arg0={type(a0).__name__ if a0 is not None else '?'} start={'yes' if len(node.args) > 1 or 'start' in kw else 'no'}")
            elif n == "pow":
                self.pow_site(node, node.args[1] if len(node.args) > 1 else node)
            elif n in ("sorted", "min", "max"):
                key = "key=" + src_of(self.text, [k for k in node.keywords if k.arg == "key"][0].value) if "key" in kw else "no key"
                extra = "" if n == "sorted" else f" nargs={len(node.args)}" + (" default" if "default" in kw else "")
                rev = " reverse" if "reverse" in kw else ""
                self.add(node, "sorted" if n == "sorted" else "minmax", f"{n} {key}{extra}{rev}")
            elif n == "int":
                self.add(node, "int", f"arg={type(node.args[0]).__name__ if node.args else 'none'}" + (" base" if len(node.args) > 1 else ""))
            elif n == "float":
                self.add(node, "float", f"arg={type(node.args[0]).__name__ if node.args else 'none'}")
            elif n == "isinstance":
                self.add(node, "isinstance", src_of(self.text, node.args[1]) if len(node.args) > 1 else "")
            elif n == "zip":
                self.add(node, "zip", "strict=True" if any(k.arg == "strict" and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords) else f"no strict nargs={len(node.args)}")
            elif n == "next":
                self.add(node, "next", f"nargs={len(node.args)}" + (" default" if len(node.args) > 1 else " NO-DEFAULT"))
            elif n in self.imported:
                mod = self.imported[n].split(".")[0]
                if mod in STDLIB_NS or mod == "xml":
                    self.add(node, "xml" if mod == "xml" else mod, f"{self.imported[n]} via bare name {n}")
        elif isinstance(f, ast.Attribute):
            if f.attr == "sort":
                key = "key=" + src_of(self.text, [k for k in node.keywords if k.arg == "key"][0].value) if "key" in kw else "no key"
                self.add(node, "sorted", f".sort {key}" + (" reverse" if "reverse" in kw else ""))
            if f.attr == "replace":
                self.add(node, "str_replace", f"nargs={len(node.args)} (receiver {src_of(self.text, f.value)[:40]})")
            if f.attr == "format":
                self.add(node, "str_format", "")
            if f.attr in ("hexdigest", "digest"):
                self.add(node, "hashlib", f".{f.attr}()")
            if isinstance(f.value, ast.Name):
                base = self.mod_alias.get(f.value.id, f.value.id)
                if base == "math":
                    self.add(node, f"math.{f.attr}", "" if f.value.id == "math" else f"via alias {f.value.id}")
                elif base == "re":
                    self.add(node, "re", f"re.{f.attr}")
                elif base == "hashlib":
                    self.add(node, "hashlib", f"hashlib.{f.attr}" + (f" args={len(node.args)}" if f.attr != "sha1" else ""))
                elif base == "itertools":
                    self.add(node, "itertools", f"itertools.{f.attr}")
                elif base in ("json", "base64", "struct", "zlib"):
                    self.add(node, base, f"{base}.{f.attr}")
                elif base == "colorsys":
                    self.add(node, "colorsys", f"colorsys.{f.attr}")
            elif cn.startswith("xml."):
                self.add(node, "xml", cn)
        # alias detection: math.* passed as a value (not called) is handled in visit_Attribute
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # math.fn used as a value (not the func of a Call) would evade the call ledger; math.pi is a constant
        if isinstance(node.value, ast.Name) and self.mod_alias.get(node.value.id, node.value.id) == "math":
            if node.attr in ("pi", "e", "tau", "inf", "nan"):
                self.add(node, f"math.{node.attr}", "constant")
            elif id(node) not in self._call_funcs:
                self.add(node, f"math.{node.attr}", "REFERENCE not a call (alias risk)")
        self.generic_visit(node)

    # --- truthiness
    def truth(self, test: ast.expr, ctx: str):
        if isinstance(test, (ast.Name, ast.Attribute, ast.Subscript, ast.Call)):
            nm = callee_name(test.func if isinstance(test, ast.Call) else test.value if isinstance(test, ast.Subscript) else test) or ""
            last = nm.split(".")[-1]
            if isinstance(test, ast.Call):
                if last in {"any", "all", "isinstance", "callable", "startswith", "endswith", "isdigit", "isalpha", "hasattr", "isnan", "isinf", "isfinite"}:
                    hint = "bool-returning call"
                elif last in {"get", "match", "search", "fullmatch", "next", "find", "pop"}:
                    hint = "Optional/maybe-empty call"
                elif CONTAINER_HINT.search(last) or last.endswith("s"):
                    hint = "container-returning call?"
                else:
                    hint = "call"
            else:
                hint = "container-name-hint" if (CONTAINER_HINT.search(last) or (last.endswith("s") and not last.endswith("ss"))) else "name/attr"
                if isinstance(test, ast.Subscript):
                    hint = "subscript " + hint
            self.add(test, "truthiness", f"{ctx}: {hint} ({type(test).__name__})")

    def visit_If(self, node):
        self.truth(node.test, "if")
        self.generic_visit(node)

    def visit_While(self, node):
        self.truth(node.test, "while")
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.truth(node.test, "ternary")
        self.generic_visit(node)

    def visit_Assert(self, node):
        self.truth(node.test, "assert")
        self.generic_visit(node)

    def visit_comprehension(self, node):
        for c in node.ifs:
            self.truth(c, "comp-if")
        self.generic_visit(node)

    def visit_UnaryOp(self, node):
        if isinstance(node.op, ast.Not):
            self.truth(node.operand, "not")
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        ctx = "and" if isinstance(node.op, ast.And) else "or"
        for v in node.values:
            self.truth(v, ctx)
        self.generic_visit(node)

    # --- literals and misc
    def visit_Dict(self, node):
        self.add(node, "dict_literal", f"{len(node.keys)} entries" + (" has **spread" if None in node.keys else ""))
        self.generic_visit(node)

    def visit_Set(self, node):
        self.add(node, "set_literal", f"{len(node.elts)} elements")
        self.generic_visit(node)

    def visit_DictComp(self, node):
        self.add(node, "dict_comp", "")
        self.generic_visit(node)

    def visit_SetComp(self, node):
        self.add(node, "set_comp", "")
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        self.add(node, "generator", "generator expression")
        self.generic_visit(node)

    def visit_Yield(self, node):
        self.add(node, "generator", "yield")
        self.generic_visit(node)

    def visit_YieldFrom(self, node):
        self.add(node, "generator", "yield from")
        self.generic_visit(node)

    def visit_Global(self, node):
        self.add(node, "global_nonlocal", "global " + ",".join(node.names))

    def visit_Nonlocal(self, node):
        self.add(node, "global_nonlocal", "nonlocal " + ",".join(node.names))

    def visit_Lambda(self, node):
        self.add(node, "lambda", "args=" + ",".join(a.arg for a in node.args.args))
        self.generic_visit(node)

    _call_funcs: set = set()


def main() -> None:
    ledger: list[dict] = []
    for fn in FILES:
        text = (SRC / fn).read_text()
        tree = ast.parse(text)
        lg = Ledger(fn, text)
        lg._call_funcs = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
        lg.visit(tree)
        ledger.extend(lg.out)
    ledger.sort(key=lambda e: (FILES.index(e["file"]), e["line"], e["class"]))
    (HERE / "hazards.json").write_text(json.dumps(ledger, indent=1) + "\n")

    per = defaultdict(Counter)
    for e in ledger:
        per[e["class"]][e["file"]] += 1
    classes = sorted(per)
    w = max(len(c) for c in classes)
    print(f"{'class':{w}} " + " ".join(f"{f[:9]:>9}" for f in FILES) + "   total")
    for c in classes:
        row = " ".join(f"{per[c][f]:>9}" for f in FILES)
        print(f"{c:{w}} {row}  {sum(per[c].values()):>6}")
    print(f"\nTOTAL entries {len(ledger)}  -> {HERE / 'hazards.json'}")
    other = Counter(e["detail"] for e in ledger if e["class"] == "fstr:other")
    print("\nfstr:other specs:", dict(other.most_common()))
    pngs = [e for e in ledger if e.get("flag")]
    print(f"png-chunk-only flagged entries (attribution.py): {len(pngs)}")

    def tot(c, f=None):
        return sum(v for k, v in per[c].items() if f is None or k == f)

    def mathcount(fn):
        return tot(f"math.{fn}")

    # plan claims
    rnd = [e for e in ledger if e["class"] == "round"]
    sha1 = [e for e in ledger if e["class"] == "hashlib" and e["detail"].startswith("hashlib.sha1")]
    claims = [
        ("sum", 11, tot("sum")),
        ("math.sin", 19, mathcount("sin")),
        ("math.cos", 20, mathcount("cos")),
        ("math.hypot", 13, mathcount("hypot")),
        ("math.atan2", 4, mathcount("atan2")),
        ("math.acos", 2, mathcount("acos")),
        ("math.copysign", 4, mathcount("copysign")),
        ("** (all files)", 25, tot("pow")),
        ("hashlib.sha1", 4, len(sha1)),
        (".1f (all files)", 952, tot("fstr:.1f")),
        (".2f (all files)", 190, tot("fstr:.2f")),
        (".0f (all files)", 10, tot("fstr:.0f")),
        (".3f (character.py)", 1, tot("fstr:.3f", "character.py")),
        ("round sites (all files)", 3, len(rnd)),
        ("chained comparisons (all files)", 7, tot("chained_compare")),
    ]
    print("\nPlan claim check (claimed vs found):")
    for name, claimed, found in claims:
        print(f"  {name:34} claimed {claimed:>4}  found {found:>4}  {'MATCH' if claimed == found else 'DIFFERS'}")
    print("  .3f per file:", dict(per["fstr:.3f"]))
    print("  .1f per file:", dict(per["fstr:.1f"]), " .2f per file:", dict(per["fstr:.2f"]), " .0f per file:", dict(per["fstr:.0f"]))
    print("  pow per file:", dict(per["pow"]), " sum per file:", dict(per["sum"]), " round per file:", dict(per["round"]))
    print("  round sites:", [(e["file"], e["line"], e["detail"]) for e in rnd])
    print("  other math fns:", {c: tot(c) for c in classes if c.startswith("math.") and c not in ("math.sin", "math.cos", "math.hypot", "math.atan2", "math.acos", "math.copysign")})
    print("  chained compare files:", dict(per["chained_compare"]))


if __name__ == "__main__":
    main()
