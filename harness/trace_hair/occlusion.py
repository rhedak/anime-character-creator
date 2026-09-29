"""What hides the reference's hair, and where: the map the gap filling is
planned from.

Every cut in `segments/` is exact (`locate.py`), so each occluder is a mask in
the composite's pixels. Drawn over the dimmed composite: the hair purple, the
hat grey, the bat red, the dress (jacket and arms) blue, the collar yellow,
the staff brown, the belt orange; the head's centre line and the rows of the
reference's chin, shoulder and waist in head radii. Written to
`out/trace_hair/occlusion.png` (2x).
"""

import json

import numpy as np
from PIL import Image, ImageDraw

REF = "ref-local/katherina_grok_real/katherina_grok_real.png"
DIR = "ref-local/katherina_grok_real/segments"
OUT = "out/trace_hair"
CROP = (400, 150, 880, 1000)
ORIGIN, S = (636, 290), 88.7
COLOURS = {
    "witch-hat": (110, 110, 110),
    "black-bat": (220, 40, 40),
    "dark-blue-dress": (60, 90, 220),
    "yellow-collar": (230, 200, 40),
    "wooden-staff": (140, 90, 40),
    "brown-belt": (240, 140, 20),
    "purple-hair": (150, 70, 200),
}


def masks(shape):
    locs = json.load(open(f"{OUT}/segments.json"))
    out = {}
    for name, info in locs.items():
        s = np.asarray(Image.open(f"{DIR}/{name}.png").convert("RGBA"))[..., 3] > 128
        m = np.zeros(shape, bool)
        x, y = info["at"]
        m[y : y + s.shape[0], x : x + s.shape[1]] = s
        out[name] = m
    return out


def main() -> None:
    a = np.asarray(Image.open(REF).convert("RGB")).astype(float)
    v = a * 0.6
    ms = masks(a.shape[:2])
    for name, col in COLOURS.items():
        v[ms[name]] = 0.35 * v[ms[name]] + 0.65 * np.array(col)
    x0, y0, x1, y1 = CROP
    im = Image.fromarray(v[y0:y1, x0:x1].clip(0, 255).astype(np.uint8)).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    ox, oy = ORIGIN
    d.line([((ox - x0) * 2, 0), ((ox - x0) * 2, im.height)], fill=(255, 255, 255))
    for name, hy in (("chin", 1.23), ("shoulder", 1.80), ("waist", 4.40)):
        y = (oy + hy * S - y0) * 2
        d.line([(0, y), (im.width, y)], fill=(0, 255, 0))
        d.text((4, y - 12), f"{name} {hy}", fill=(0, 255, 0))
    im.save(f"{OUT}/occlusion.png")
    print(f"{OUT}/occlusion.png", im.size)


if __name__ == "__main__":
    main()
