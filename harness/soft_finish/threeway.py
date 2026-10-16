"""Drawn, soft and a picture pack's frame side by side, at the companion's close-up.

    ./harness/run.sh harness/soft_finish/threeway.py risa ../anime_ai_companion-dev/packs/risa-dress/neutral.webp

Writes `out/soft/threeway-<preset>.png`: the companion's close-up above, and below it the
head zoomed (the drawn figure's `face` view against a crop of the pack frame). The close-up
viewBox and the pack frame have the same aspect (290x330 against 940x1070), so the top row
is the picture the companion shows.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from dataclasses import replace
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "src")
from anime_character_creator import PRESETS, render_character  # noqa: E402

GROUND = "#2b1a55"
W, H = 640, 728  # one panel, the close-up's aspect
FACE_H = 680  # the head row's panels are W wide and this tall
# The head, as fractions of the pack frame (left, top, right, bottom), matched by eye to the
# drawn `face` view (viewBox 120 10 160 170).
PACK_HEAD = (0.26, 0.07, 0.74, 0.52)


def drawn(name: str, finish: str, face: bool = False) -> Image.Image:
    svg = render_character(replace(PRESETS[name], finish=finish))
    box, size = ("120 10 160 170", (W, FACE_H)) if face else ("55 0 290 330", (W, H))
    svg = re.sub(r'viewBox="[^"]+"', f'viewBox="{box}"', svg, count=1)
    svg = re.sub(r'width="400" height="\d+"', f'width="{size[0]}" height="{size[1]}"', svg, count=1)
    png = cairosvg.svg2png(bytestring=svg.encode(), background_color=GROUND)
    return Image.open(io.BytesIO(png)).convert("RGB")


def packed(path: Path, face: bool = False) -> Image.Image:
    frame = Image.open(path).convert("RGBA")
    if face:
        l, t, r, b = PACK_HEAD
        frame = frame.crop((int(l * frame.width), int(t * frame.height), int(r * frame.width), int(b * frame.height)))
    size = (W, FACE_H) if face else (W, H)
    frame = frame.resize(size, Image.LANCZOS)
    return Image.alpha_composite(Image.new("RGBA", size, GROUND), frame).convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("preset", choices=sorted(PRESETS))
    ap.add_argument("pack_frame", type=Path)
    ap.add_argument("--out", default="out/soft")
    args = ap.parse_args()
    labels = ["Drawn (flat, the house style)", "Drawn, soft finish", "Picture pack (made with an image model)"]
    rows = [
        [drawn(args.preset, "flat"), drawn(args.preset, "soft"), packed(args.pack_frame)],
        [drawn(args.preset, "flat", True), drawn(args.preset, "soft", True), packed(args.pack_frame, True)],
    ]
    label_h, gap = 44, 8
    sheet = Image.new("RGB", (W * 3 + gap * 2, label_h + H + gap + FACE_H), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    except OSError:
        font = ImageFont.load_default()
    for i, label in enumerate(labels):
        x = i * (W + gap)
        sheet.paste(rows[0][i], (x, label_h))
        sheet.paste(rows[1][i], (x, label_h + H + gap))
        draw.text((x + 12, 10), label, fill="black", font=font)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"threeway-{args.preset}.png"
    sheet.save(target)
    print(f"wrote {target} ({sheet.width}x{sheet.height})")


if __name__ == "__main__":
    main()
