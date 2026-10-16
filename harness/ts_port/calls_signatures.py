"""Write `fixtures/calls/_signatures.json`: for each recorded function, its parameter names in order, so a keyword argument in a
recorded call can be placed at its position when the TypeScript function is called.

    PY harness/ts_port/calls_signatures.py
"""

from __future__ import annotations

import importlib
import inspect
import json
from pathlib import Path

import _bootstrap  # noqa: F401

HERE = Path(__file__).resolve().parent
_bootstrap.assert_package_location() if False else None


def main() -> None:
    index = json.loads((HERE / "out/calls/_index.json").read_text())["functions"]
    out: dict[str, list[str]] = {}
    for e in index:
        mod = importlib.import_module(f"anime_character_creator.{e['module']}")
        obj = mod
        parts = e["function"].split(".")
        try:
            for part in parts:
                obj = getattr(obj, part)
            sig = inspect.signature(obj)
        except (AttributeError, ValueError, TypeError):
            continue
        out[e["function"]] = [n for n, p in sig.parameters.items() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)]
    (HERE / "fixtures/calls/_signatures.json").write_text(json.dumps(out, indent=0, sort_keys=True))
    print(len(out), "signatures")


if __name__ == "__main__":
    main()
