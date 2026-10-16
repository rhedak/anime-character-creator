"""AST-instrumenting import hook that records every part of `render_character`.

`install()` puts a finder first on sys.meta_path for the single module
`anime_character_creator.character`. Its loader compiles a transformed AST of the
source text every time (no .pyc is read or written), so the whole package sees one
instrumented `character` module and class identity stays consistent.

Inside `render_character` only, the transform:
  * wraps each element E of the list literals `chest`, `under_arms`, `layers` as
    `__stage(NAME, INDEX, SOURCE_TEXT, E)`. INDEX is the position in the source
    list literal, starred elements included in the count, so `layers[17]` is the
    18th slot of the literal. Starred elements (`*chest`, `*under_arms`) are left
    alone: their items are already recorded as chest[i] and under_arms[i].
  * inserts `__mark("body", body)` after the join, `__mark("body_soft", body)`
    after the soft-finish `if`, `__mark("body_ns", body)` after the id_prefix `if`,
    and wraps the returned document in `__mark("doc", ...)`.
`__stage` and `__mark` are builtins bound to one Recorder. Outside a recording
they pass the value straight through.
"""

from __future__ import annotations

import ast
import builtins
import dataclasses
import importlib.abc
import importlib.machinery
import importlib.util
import sys
from typing import Any

import _bootstrap

TARGET = "anime_character_creator.character"
LISTS = ("chest", "under_arms", "layers")


class Recorder:
    def __init__(self) -> None:
        self.active: list[dict[str, Any]] | None = None

    def stage(self, name: str, index: int, expr: str, value: Any) -> Any:
        if self.active is not None:
            if not isinstance(value, str):
                raise TypeError(f"{name}[{index}] evaluated to {type(value).__name__}, not str")
            self.active.append({"name": f"{name}[{index}]", "expr": expr, "text": value})
        return value

    def mark(self, name: str, value: Any) -> Any:
        if self.active is not None:
            self.active.append({"name": name, "expr": None, "text": value})
        return value


RECORDER = Recorder()


def _call(fn: str, *args: ast.expr) -> ast.Call:
    return ast.Call(func=ast.Name(id=fn, ctx=ast.Load()), args=list(args), keywords=[])


def _const(v: Any) -> ast.Constant:
    return ast.Constant(value=v)


def _mark_stmt(name: str, anchor: ast.stmt) -> ast.stmt:
    stmt = ast.Expr(value=_call("__mark", _const(name), ast.Name(id="body", ctx=ast.Load())))
    return ast.copy_location(stmt, anchor)


def transform(source: str, path: str) -> ast.Module:
    tree = ast.parse(source, path)
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "render_character"]
    if len(funcs) != 1:
        raise RuntimeError("expected exactly one module-level render_character")
    fn = funcs[0]
    seen: dict[str, int] = {}

    # Only direct statements of the function body: the three list assignments, the
    # `body = ...join` assignment, the two ifs, the return.
    new_body: list[ast.stmt] = []
    for stmt in fn.body:
        new_body.append(stmt)
        if (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
        ):
            tname = stmt.targets[0].id
            if tname in LISTS and isinstance(stmt.value, ast.List):
                seen[tname] = seen.get(tname, 0) + 1
                elts: list[ast.expr] = []
                for i, e in enumerate(stmt.value.elts):
                    if isinstance(e, ast.Starred):
                        elts.append(e)
                        continue
                    text = ast.get_source_segment(source, e)
                    if text is None:
                        raise RuntimeError(f"no source text for {tname}[{i}]")
                    call = _call("__stage", _const(tname), _const(i), _const(text), e)
                    elts.append(ast.copy_location(call, e))
                stmt.value.elts = elts
            elif tname == "body" and isinstance(stmt.value, ast.Call):
                seen["body"] = seen.get("body", 0) + 1
                new_body.append(_mark_stmt("body", stmt))
        elif isinstance(stmt, ast.If) and isinstance(stmt.test, ast.Call):
            callee = stmt.test.func
            if isinstance(callee, ast.Name) and callee.id == "_soft":
                seen["soft_if"] = seen.get("soft_if", 0) + 1
                new_body.append(_mark_stmt("body_soft", stmt))
        elif isinstance(stmt, ast.If) and isinstance(stmt.test, ast.Name) and stmt.test.id == "id_prefix":
            seen["ns_if"] = seen.get("ns_if", 0) + 1
            new_body.append(_mark_stmt("body_ns", stmt))
        elif isinstance(stmt, ast.Return) and stmt.value is not None:
            seen["return"] = seen.get("return", 0) + 1
            stmt.value = ast.copy_location(_call("__mark", _const("doc"), stmt.value), stmt.value)
    fn.body = new_body
    want = {"chest": 1, "under_arms": 1, "layers": 1, "body": 1, "soft_if": 1, "ns_if": 1, "return": 1}
    if seen != want:
        raise RuntimeError(f"render_character shape changed: found {seen}, expected {want}")
    ast.fix_missing_locations(tree)
    return tree


class InstrumentedLoader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname: str) -> Any:
        path = self.get_filename(fullname)
        source = self.get_data(path).decode("utf-8")
        return compile(transform(source, path), path, "exec", dont_inherit=True)


class InstrumentingFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> Any:
        if fullname != TARGET:
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is None or spec.origin is None:
            return None
        return importlib.util.spec_from_file_location(
            fullname, spec.origin, loader=InstrumentedLoader(fullname, spec.origin)
        )


_installed = False


def install() -> None:
    global _installed
    if _installed:
        return
    if "anime_character_creator" in sys.modules:
        raise RuntimeError("anime_character_creator already imported; install() must come first")
    sys.dont_write_bytecode = True
    builtins.__stage = RECORDER.stage  # type: ignore[attr-defined]
    builtins.__mark = RECORDER.mark  # type: ignore[attr-defined]
    sys.meta_path.insert(0, InstrumentingFinder())
    _installed = True
    _bootstrap.assert_package_location()
    from anime_character_creator import character

    if "__stage" not in character.render_character.__code__.co_names:
        raise RuntimeError("character.render_character is not instrumented")
    if not isinstance(character.__loader__, InstrumentedLoader):
        raise RuntimeError("character was not loaded by the instrumented loader")


def render_stages(params: Any, **render_kwargs: Any) -> dict[str, Any]:
    """Render `params` and return {"skeleton": {...}, "stages": [...], "doc": str}."""
    from anime_character_creator.character import render_character, skeleton_for

    if RECORDER.active is not None:
        raise RuntimeError("render_stages is not re-entrant")
    skeleton = dataclasses.asdict(skeleton_for(params))
    RECORDER.active = []
    try:
        doc = render_character(params, **render_kwargs)
        stages = RECORDER.active
    finally:
        RECORDER.active = None
    if stages[-1]["name"] != "doc" or stages[-1]["text"] != doc:
        raise RuntimeError("last stage is not the returned document")
    return {"skeleton": skeleton, "stages": stages}
