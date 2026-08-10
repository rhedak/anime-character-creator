"""Draw anime characters as parametric SVG shapes.

A character is a `CharacterParams` (colours, an `Outfit`, a `FaceStyle`, a
haircut, a build) drawn against a `Skeleton` of proportion anchors. Nothing is
composited from pre-made art and no image model is involved: every shape is
computed from the skeleton and written out as SVG text, so a change of
proportions restyles every character at once.

    from anime_character_creator import PRESETS, build_skeleton, render_character

    svg = render_character(PRESETS["satoko"])                     # default build
    svg = render_character(PRESETS["satoko"], build_skeleton(heads=6.0))

`render_character` returns the document as a string; writing it and turning it
into a PNG is `generate.main`, which is also the `anime-character-creator`
command. See `docs/api.md` for the full surface and `docs/architecture.md` for
how the parts fit together.
"""

from __future__ import annotations

from .character import (
    HAIRSTYLES,
    CharacterParams,
    Expression,
    FaceStyle,
    Hairstyle,
    Outfit,
    render_character,
)
from .colorutil import shade
from .presets import DISPLAY_NAMES, EXPRESSIONS, NEUTRAL_BASES, PRESETS, REALISTIC_REFS, ROSTERS
from .skeleton import BUILDS, DEFAULT_BUILD, DEFAULT_HEADS, Skeleton, build_skeleton

__all__ = [
    "BUILDS",
    "DEFAULT_BUILD",
    "DEFAULT_HEADS",
    "DISPLAY_NAMES",
    "EXPRESSIONS",
    "HAIRSTYLES",
    "NEUTRAL_BASES",
    "PRESETS",
    "REALISTIC_REFS",
    "ROSTERS",
    "CharacterParams",
    "Expression",
    "FaceStyle",
    "Hairstyle",
    "Outfit",
    "Skeleton",
    "build_skeleton",
    "render_character",
    "shade",
]

__version__ = "0.1.0"
