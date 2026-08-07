"""Put the trouser measurements into head radii, so they can be compared with
the skeleton instead of with each other.

The head is measured on the *face*, not on the silhouette: the silhouette at
head height is hair, which stands well clear of the skull and would make every
width derived from it too small. Skin is the only large peach area on either
sheet, so the widest skin row above the shoulders is the face at the cheeks,
which is a little narrower than the skull. The skull's own half-width is
recovered from `character._head_edge_x`, which knows how much the cheek is in
from the widest point at a given build.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

REF = Path(__file__).resolve().parents[2] / "ref"


def face_half_width(name: str) -> tuple[float, int]:
    im = Image.open(REF / name).convert("RGB")
    w, h = im.size
    px = im.load()
    best, best_y = 0, 0
    for y in range(h // 2):
        xs = [
            x
            for x in range(w)
            if (lambda r, g, b: r > 195 and r > g + 12 and g > b and r - b > 28)(*px[x, y])
        ]
        if len(xs) > 20 and xs[-1] - xs[0] > best:
            best, best_y = xs[-1] - xs[0], y
    return best / 2, best_y


for name in ("satoshi-chibi.jpg", "satoshi.png"):
    hw, y = face_half_width(name)
    print(f"{name}: widest face half-width {hw:.1f}px at y={y}")
