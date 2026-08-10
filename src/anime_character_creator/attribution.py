"""The `<metadata>` block `render_character(metadata=True)` can embed.

`docs/web-gui-plan.md`'s licensing section settles what this says and why it
has to be metadata rather than an enforced term: the permissive licence
covers the code, forkable on purpose, which is what makes an attribution
*clause* on the output unenforceable. What a claim of hand-drawing it *is*
vulnerable to is the file itself saying otherwise, which is what this writes.

Off by default on `render_character`, so the fourteen files `ref-out/`
compares byte for byte do not churn on every unrelated change; the web tool
turns it on for what a visitor downloads.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from .character import CharacterParams
from .urlstate import character_url

TOOL_URL = "https://rhedak.github.io/anime-character-creator/"
REPOSITORY_URL = "https://github.com/rhedak/anime-character-creator"
LICENSE_STATEMENT = (
    "MIT License. Free to use, including commercially. "
    "Please link back to the tool or the code, and please do not present this "
    "as hand-drawn: a program drew it."
)
NOVEL_TITLE = "The Hero of the Mist Tragedy"
NOVEL_URL = "https://www.honeyfeed.fm/novels/32712"


def metadata_block(p: CharacterParams) -> str:
    """An SVG `<metadata>` element: the tool, the licence, the novel, and a
    link that reproduces `p` exactly, all in one place so a downloaded file
    carries its own provenance rather than depending on a page around it."""
    character = escape(character_url(p, TOOL_URL))
    title_attr = escape(NOVEL_TITLE, {'"': "&quot;"})
    return (
        "<metadata>\n"
        f"    <source>{escape(TOOL_URL)}</source>\n"
        f"    <repository>{escape(REPOSITORY_URL)}</repository>\n"
        f"    <license>{escape(LICENSE_STATEMENT)}</license>\n"
        f'    <novel title="{title_attr}">{escape(NOVEL_URL)}</novel>\n'
        f"    <character>{character}</character>\n"
        "  </metadata>"
    )
