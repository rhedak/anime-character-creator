"""Make `anime_character_creator` resolve to THIS worktree's src, never the editable install.

Import this before anything imports the package. It puts the worktree src first on
sys.path (PYTHONPATH would do the same; this makes the scripts independent of it) and
turns off bytecode writing so no .pyc is written or trusted for the instrumented module.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parent.parent
SRC = WORKTREE / "src"
PKG = SRC / "anime_character_creator"

sys.dont_write_bytecode = True
if str(SRC) not in sys.path[:1]:
    sys.path.insert(0, str(SRC))
if str(HERE) not in sys.path:
    sys.path.insert(1, str(HERE))


def assert_package_location() -> None:
    import anime_character_creator

    got = Path(anime_character_creator.__file__).resolve()
    if PKG not in got.parents:
        raise RuntimeError(f"anime_character_creator imported from {got}, expected under {PKG}")
