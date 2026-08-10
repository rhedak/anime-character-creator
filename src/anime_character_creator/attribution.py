"""The `<metadata>` block `render_character(metadata=True)` can embed.

`docs/web-gui-plan.md`'s licensing section settles what this says and why it
has to be metadata rather than an enforced term: the permissive licence
covers the code, forkable on purpose, which is what makes an attribution
*clause* on the output unenforceable. What a claim of hand-drawing it *is*
vulnerable to is the file itself saying otherwise, which is what this writes.

Off by default on `render_character`, `render_sheet` and `render_cover`
themselves, so the files `ref-out/` compares byte for byte do not churn on
every unrelated change (a wording edit to `LICENSE_STATEMENT` or `TOOL_URL`
below would otherwise touch every one of them at once). The CLI wrappers
(`generate.py`, `sheet.py`, `cover.py`) default their own `--metadata` flag
to *on*, since a file that leaves this repo is exactly the case this
exists for; `refresh-ref-out.sh` passes `--no-metadata` explicitly to keep
its own comparison clean. The web tool always turns it on for what a
visitor downloads, the same way.
"""

from __future__ import annotations

import struct
import zlib
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


def _metadata_header() -> str:
    """The four lines every `<metadata>` block here carries regardless of
    what it is attached to: the tool, the licence and the novel. Shared so
    `metadata_block` and `sheet_metadata_block` cannot say two different
    things about the same three facts."""
    title_attr = escape(NOVEL_TITLE, {'"': "&quot;"})
    return (
        f"    <source>{escape(TOOL_URL)}</source>\n"
        f"    <repository>{escape(REPOSITORY_URL)}</repository>\n"
        f"    <license>{escape(LICENSE_STATEMENT)}</license>\n"
        f'    <novel title="{title_attr}">{escape(NOVEL_URL)}</novel>\n'
    )


def metadata_block(p: CharacterParams) -> str:
    """An SVG `<metadata>` element: the tool, the licence, the novel, and a
    link that reproduces `p` exactly, all in one place so a downloaded file
    carries its own provenance rather than depending on a page around it."""
    character = escape(character_url(p, TOOL_URL))
    return f"<metadata>\n{_metadata_header()}    <character>{character}</character>\n  </metadata>"


def sheet_metadata_block(members: tuple[str, ...]) -> str:
    """The sheet's own `<metadata>` element: like `metadata_block`, except a
    sheet has no single character to reproduce, so this carries one named
    `<character>` per member instead of one bare one. Each member is a
    `PRESETS` name (`members_of` already guarantees that), so its own
    reproduction link comes straight from the preset rather than anything
    the sheet itself computed.
    """
    # Imported here, not at module level: `presets` imports `character`,
    # which this module already reaches through `character_url`, and nothing
    # forces the cycle to resolve in the order that needs.
    from .presets import PRESETS

    entries = "".join(
        f'    <character name="{escape(name)}">{escape(character_url(PRESETS[name], TOOL_URL))}</character>\n'
        for name in members
    )
    return f"<metadata>\n{_metadata_header()}{entries}  </metadata>"


_PNG_SIGNATURE_LEN = 8


def inject_png_text(png_bytes: bytes, keyword: str, text: str) -> bytes:
    """Splice a `tEXt` chunk (PNG spec, section 11.3.4.3) right after IHDR,
    the first chunk in every PNG `cairosvg.svg2png` writes.

    A PNG rasterizer drops an SVG's own `<metadata>` element the same way a
    browser's `<canvas>` does, so a PNG needs this written directly rather
    than carried over from the SVG that made it. `web/app.js`'s
    `injectPngText` does the identical splice for the browser's own
    downloads (using `TextEncoder` and a hand-rolled CRC table, since a
    browser has no `zlib`); the two should stay in step.
    """
    ihdr_len = struct.unpack(">I", png_bytes[_PNG_SIGNATURE_LEN : _PNG_SIGNATURE_LEN + 4])[0]
    ihdr_chunk_len = 4 + 4 + ihdr_len + 4  # length + type + data + crc
    insert_at = _PNG_SIGNATURE_LEN + ihdr_chunk_len

    # Latin-1, per the PNG spec's own tEXt encoding; every character a
    # reproduction link can contain (base64url's alphabet, `?` and `=`) is
    # plain ASCII, so this never has anything Latin-1 can't hold.
    data = keyword.encode("latin-1") + b"\x00" + text.encode("latin-1")
    chunk_type = b"tEXt"
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    chunk = struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)
    return png_bytes[:insert_at] + chunk + png_bytes[insert_at:]


def png_with_metadata(png_bytes: bytes, p: CharacterParams) -> bytes:
    """`png_bytes` with the same reproduction link `metadata_block` embeds in
    an SVG, under the "Source" keyword `web/app.js` uses for its own PNG
    downloads, so a PNG carries the same link regardless of which of the two
    wrote it."""
    return inject_png_text(png_bytes, "Source", character_url(p, TOOL_URL))


def sheet_png_with_metadata(png_bytes: bytes, members: tuple[str, ...]) -> bytes:
    """`png_bytes` with one reproduction link per member, `; `-joined into a
    single "Source" chunk rather than one `tEXt` chunk per member: a sheet
    can carry fourteen of these, and one chunk a reader has to split is
    simpler than fourteen a reader has to find."""
    from .presets import PRESETS

    text = "; ".join(f"{name}={character_url(PRESETS[name], TOOL_URL)}" for name in members)
    return inject_png_text(png_bytes, "Source", text)
