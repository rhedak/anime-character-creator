"""Comic pages: panels of placed characters, stacked into a vertical strip.

What a comic can do lives here; the comic that is made with it (the script, the
panels, the places) lives with the story that owns it. See `docs/comic/plan.md`.

Not imported by `anime_character_creator` itself, so the character renderer
stays as small as it was.
"""

from __future__ import annotations

from .layout import Panel, Placement, Strip, render_panel, render_strip, write_strip

__all__ = ["Panel", "Placement", "Strip", "render_panel", "render_strip", "write_strip"]
