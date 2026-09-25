"""Step 1 of `docs/bare-body-plan.md`: what breaks when the tunic comes off.

Every preset at both builds, in three outfits:

- `tunic off`: `tunic_color=None`, everything else as the preset wears it;
- `all off`: every `*_color` field of `Outfit` set to `None`, the tunic and
  the boots included;
- `boots on`: the same with the boots kept.

For each render, the exception if it raised (type, message, the innermost
frame in `character.py`), else every place the string `None` reached the SVG
(the element's tag and attribute). Printed as a table and written to
`out/bare/audit.txt`.

Images only of the adults (`ADULTS`): with the tunic off and no base top yet
(step 3), a render is a bare torso, and the strategy file's rule is that no
such render is made of a character who is not an adult. The others are
audited in text only. Writes `out/bare/audit_<build>.png`.
"""

import dataclasses
import io
import os
import re
import traceback
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS
from anime_character_creator.skeleton import BUILDS

# Adults by the cast notes: Satoko is twenty (Kyoko's flashback is at
# seventeen, three years before), Chiyo late forties to mid fifties, Gero late
# forties, Daizen and Tenno the cast's oldest; Keiko, Krista, Reika and Elara
# are adult by their design briefs. Anyone not listed is left out of images,
# including presets whose age the notes do not state.
ADULTS = ("satoko", "chiyo", "keiko", "krista", "reika", "elara", "gero", "daizen", "tenno")
COLOR_FIELDS = [f.name for f in dataclasses.fields(c.Outfit) if f.name.endswith("_color")]
SCALE = 1


def outfit_variants(p: c.CharacterParams) -> dict[str, c.CharacterParams]:
    return {
        "tunic off": replace(p, outfit=replace(p.outfit, tunic_color=None)),
        "all off": replace(p, outfit=replace(p.outfit, **dict.fromkeys(COLOR_FIELDS))),
        # The boots raise on their own (the first run), which hid everything
        # after them; this is "all off" with the boots kept on.
        "boots on": replace(
            p, outfit=replace(p.outfit, **dict.fromkeys(set(COLOR_FIELDS) - {"boot_color"}))
        ),
    }


def audit(p: c.CharacterParams, heads: float) -> tuple[str, str | None]:
    """`(finding, svg)`: `ok`, the `None`s that reached the SVG, or the error."""
    try:
        svg = c.render_character(p, c.skeleton_for(p, heads), background="#ffffff")
    except Exception as e:
        frames = [f for f in traceback.extract_tb(e.__traceback__) if f.filename.endswith("character.py")]
        where = f"{frames[-1].name}:{frames[-1].lineno}" if frames else "?"
        return f"RAISES {type(e).__name__} at {where}: {e}", None
    hits = sorted({f"<{m[0]} {m[1]}>" for m in re.findall(r'<(\w+)[^>]*?\b([\w-]+)="None"', svg)})
    return ("None in " + ", ".join(hits)) if hits else "ok", svg


def tile(svg: str, label: str) -> Image.Image:
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGB")
    out = Image.new("RGB", (im.width, im.height + 18), (230, 230, 230))
    out.paste(im, (0, 18))
    ImageDraw.Draw(out).text((4, 3), label, fill=(0, 0, 0))
    return out


def main() -> None:
    os.makedirs("out/bare", exist_ok=True)
    lines = []
    for build, heads in (("chibi", None), ("realistic", BUILDS["realistic"])):
        tiles: list[Image.Image] = []
        for name, p in PRESETS.items():
            for variant, q in outfit_variants(p).items():
                finding, svg = audit(q, heads)
                lines.append(f"{build:9} {name:10} {variant:9} {finding}")
                if svg is not None and name in ADULTS:
                    tiles.append(tile(svg, f"{name} {variant}"))
        if tiles:
            cols = 6
            w, h = max(t.width for t in tiles), max(t.height for t in tiles)
            rows = (len(tiles) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * w, rows * h), (200, 200, 200))
            for i, t in enumerate(tiles):
                sheet.paste(t, ((i % cols) * w, (i // cols) * h))
            sheet.save(f"out/bare/audit_{build}.png")
    report = "\n".join(lines)
    print(report)
    with open("out/bare/audit.txt", "w") as f:
        f.write(report + "\n")


main()
