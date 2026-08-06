"""So `python -m anime_character_creator` is the CLI, same as the installed
`anime-character-creator` command. `render.sh` uses this form, which needs the
package importable but not installed."""

from __future__ import annotations

from .generate import main

main()
