"""Sample a first-draft palette off each reference.

Bands rather than points, and the modal exact colour inside a band rather than a
mean: these are flat cel-shaded images, so the modal value is the garment's own
tone, while a mean drags it toward the line work and the shadow pass.

The bands are fractions of the figure's own ink box, not of the canvas, because
the references are cropped differently from one another. Everything here is a
starting point to be corrected by eye; see `docs/character-roster-plan.md`.
"""

from collections import Counter
from pathlib import Path

from PIL import Image

REF = Path(__file__).resolve().parents[2] / "ref"

# name -> list of (label, y0, y1, x0, x1) as fractions of the ink box
BANDS = [
    ("hair", 0.02, 0.09, 0.40, 0.60),
    ("skin", 0.11, 0.14, 0.44, 0.56),
    ("top", 0.24, 0.32, 0.42, 0.58),
    ("mid", 0.42, 0.50, 0.42, 0.58),
    ("low", 0.62, 0.72, 0.42, 0.58),
    ("foot", 0.93, 0.97, 0.40, 0.60),
]


def ink_box(im):
    """The drawn figure, ignoring the near-white studio background."""
    px = im.load()
    w, h = im.size
    xs, ys = [], []
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            r, g, b = px[x, y]
            if not (r > 225 and g > 225 and b > 225):
                xs.append(x)
                ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def modal(im, box, band):
    x0, y0, x1, y1 = box
    _, fy0, fy1, fx0, fx1 = band
    px = im.load()
    c = Counter()
    for y in range(int(y0 + (y1 - y0) * fy0), int(y0 + (y1 - y0) * fy1)):
        for x in range(int(x0 + (x1 - x0) * fx0), int(x0 + (x1 - x0) * fx1)):
            r, g, b = px[x, y]
            # Skip the outline and anything close to it: it is the one colour
            # every character shares and it would win every band it touches.
            if r + g + b > 90:
                c[(r, g, b)] += 1
    if not c:
        return "-"
    r, g, b = c.most_common(1)[0][0]
    return f"#{r:02x}{g:02x}{b:02x}"


for name in sorted(p.stem for p in REF.glob("*.png") if p.stem.islower() and "-" not in p.stem):
    if name.startswith("character_sheet"):
        continue
    im = Image.open(REF / f"{name}.png").convert("RGB")
    box = ink_box(im)
    row = "  ".join(f"{b[0]}={modal(im, box, b)}" for b in BANDS)
    print(f"{name:10s} {row}")
