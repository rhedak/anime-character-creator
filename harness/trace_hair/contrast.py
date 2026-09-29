"""The reference's hair with its line work brought up, for tracing it faithfully.

The hair's fill is a dark purple (about (54, 37, 79)) with lighter sheen and
darker shadow in it, and its lines are only a little darker than the fill, so
a brightness threshold either misses the lines on the sheen or takes the
shadow with them. Three views, in the composite's pixels, the hair's own cut
(`segments/purple-hair.png`, exact, `locate.py`) as the mask:

- **stretched**: the hair's luminance stretched from its 1st to 99th
  percentile, the rest of the picture dimmed, so the eye can follow the lines;
- **black-hat**: the grey closing over a disk wider than a line, minus the
  picture. A thin dark line comes out bright wherever it sits, on sheen or in
  shadow, and flat fill of any shade comes out near zero. Shown inverted,
  dark lines on white;
- **lines**: the black-hat thresholded (`LINE_T` of its 99th percentile
  inside the hair) and cleaned of specks, the candidate line mask the trace
  will centre-line.

Written to `out/trace_hair/contrast.png` (2x) and `contrast_lines.npy` (the
line mask, full frame).
"""

import json

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

REF = "ref-local/katherina_grok_real/katherina_grok_real.png"
DIR = "ref-local/katherina_grok_real/segments"
OUT = "out/trace_hair"
CROP = (420, 190, 870, 720)
# The disk's radius, in pixels: the reference's lines are 2 to 4 px wide.
R = 4
LINE_T = 0.30
SPECK = 20


def hair_mask(shape):
    at = json.load(open(f"{OUT}/segments.json"))["purple-hair"]["at"]
    s = np.asarray(Image.open(f"{DIR}/purple-hair.png").convert("RGBA"))[..., 3] > 128
    m = np.zeros(shape, bool)
    m[at[1] : at[1] + s.shape[0], at[0] : at[0] + s.shape[1]] = s
    return m


def main() -> None:
    a = np.asarray(Image.open(REF).convert("RGB")).astype(float)
    lum = a @ np.array([0.299, 0.587, 0.114])
    m = hair_mask(lum.shape)

    lo, hi = np.percentile(lum[m], (1, 99))
    st = np.clip((lum - lo) / (hi - lo), 0, 1) * 255
    st = np.where(m, st, lum * 0.35)

    disk = np.hypot(*np.mgrid[-R : R + 1, -R : R + 1]) <= R
    bh = ndi.grey_closing(lum, footprint=disk) - lum
    # Off the hair's own edge, where the black page makes the closing jump.
    inner = ndi.binary_erosion(m, iterations=2)
    ref = np.percentile(bh[inner], 99)
    bhn = np.clip(bh / ref, 0, 1)
    bh_view = np.where(m, 255 - bhn * 255, 200)

    lines = inner & (bhn > LINE_T)
    lab, n = ndi.label(lines, structure=np.ones((3, 3)))
    sizes = ndi.sum(lines, lab, range(1, n + 1))
    keep = np.isin(lab, np.nonzero(sizes >= SPECK)[0] + 1)
    np.save(f"{OUT}/contrast_lines.npy", keep)
    print(f"black-hat 99th percentile {ref:.1f}; {int((sizes >= SPECK).sum())} line pieces, {int(keep.sum())} px")
    ln_view = np.where(keep, 0, np.where(m, 235, 200))

    x0, y0, x1, y1 = CROP
    panels = [Image.fromarray(v[y0:y1, x0:x1].astype(np.uint8)).convert("RGB") for v in (st, bh_view, ln_view)]
    w, h = panels[0].size
    out = Image.new("RGB", (w * 3 + 8, h), (120, 120, 120))
    for i, p in enumerate(panels):
        out.paste(p, (i * (w + 4), 0))
    out = out.resize((out.width * 2, out.height * 2), Image.LANCZOS)
    out.save(f"{OUT}/contrast.png")
    print(f"{OUT}/contrast.png", out.size)


if __name__ == "__main__":
    main()
