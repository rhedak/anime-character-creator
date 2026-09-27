"""D4d H1 of `docs/detail-plan.md`: map the fill regions in each reference hand.

The reference is on a near-black page, so outline and background are one
colour: the trace skill's step 3 labels the fills between the outlines. Prints
every component over 30 px starting inside each hand's box, with its bbox and
mean colour, and writes `out/trace_hands/seg_<hand>.png`, each component in a
colour of its own with its label, at 5x.
"""

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

REF = "ref-local/katherina_grok_real/katherina_grok_real.png"
OUT = "out/trace_hands"
BOXES = {"grip": (340, 700, 450, 800), "relaxed": (790, 850, 880, 975)}


def main() -> None:
    a = np.asarray(Image.open(REF).convert("RGB")).astype(int)
    fill = a.sum(2) > 150
    rng = np.random.default_rng(3)
    for name, (x0, y0, x1, y1) in BOXES.items():
        sub = fill[y0:y1, x0:x1]
        lab, n = ndi.label(sub)
        view = np.zeros((*sub.shape, 3), dtype=np.uint8)
        d_items = []
        for i in range(1, n + 1):
            m = lab == i
            if m.sum() < 30:
                continue
            ys, xs = np.nonzero(m)
            col = a[y0:y1, x0:x1][m].mean(0)
            print(f"{name} #{i}: {m.sum()} px, x {xs.min() + x0}..{xs.max() + x0}, y {ys.min() + y0}..{ys.max() + y0}, mean {tuple(int(v) for v in col)}")
            view[m] = rng.integers(60, 255, 3)
            d_items.append((i, xs.mean(), ys.mean()))
        im = Image.fromarray(view).resize((sub.shape[1] * 5, sub.shape[0] * 5), Image.NEAREST)
        d = ImageDraw.Draw(im)
        for i, mx, my in d_items:
            d.text((mx * 5, my * 5), str(i), fill=(0, 0, 0))
        im.save(f"{OUT}/seg_{name}.png")


if __name__ == "__main__":
    main()
