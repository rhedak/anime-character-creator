"""Place `ref-local/katherina_hair/` in `katherina_grok_real`'s frame.

The owner's hair-only reference (2026-09-29) is Katherina's hair with nothing
in front of it: `hair_only.png` the whole of it, `hair_with_human_shape.png`
the same with a human silhouette cut out, so what is left is what hangs in
front of the body. Both carry alpha and share one frame. Neither has a face,
so D0's face-width calibration cannot be made on them directly. Instead the
front piece is registered to `katherina_grok_real`'s seen hair between the
brim and the chin (the fringe, the parting, the curtains), which that
calibration already ties to our face: one uniform scale and a translation (the
trace skill's rule), the one with the best overlap (intersection over union),
the bat's cut left out of the score. A coarse pass at half resolution over
scales 0.40 to 0.95, then a fine one around the best.

Writes `out/hair_only/register.json` and `register.png` (the scaled front
piece's outline over the old reference).
"""

import json
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.signal import fftconvolve

OLD = "ref-local/katherina_grok_real/katherina_grok_real.png"
OLD_SEG = "ref-local/katherina_grok_real/segments"
OLD_AT = {"purple-hair": (435, 200), "black-bat": (708, 297)}
NEW_FRONT = "ref-local/katherina_hair/hair_with_human_shape.png"
OUT = "out/hair_only"
# The old reference's rows compared: its brim to its chin (px).
ROWS = (200, 399)


def placed(name, shape):
    s = np.asarray(Image.open(f"{OLD_SEG}/{name}.png").convert("RGBA"))[..., 3] > 128
    m = np.zeros(shape, bool)
    x, y = OLD_AT[name]
    m[y : y + s.shape[0], x : x + s.shape[1]] = s
    return m


def search(target, weight, front, scales, k):
    """Best (iou, scale, dx, dy) over `scales`, at 1/`k` resolution; dx, dy the
    scaled front piece's top-left in the old reference's full pixels."""
    T = target[::k, ::k].astype(float)
    Wt = weight[::k, ::k].astype(float)
    TW = T * Wt
    best = None
    for sc in scales:
        w, h = int(front.shape[1] * sc / k), int(front.shape[0] * sc / k)
        A = np.asarray(Image.fromarray(front.astype(np.uint8) * 255).resize((w, h), Image.BILINEAR)) > 127
        A = A.astype(float)
        Af = A[::-1, ::-1]
        inter = fftconvolve(TW, Af, mode="full")
        a_in = fftconvolve(Wt, Af, mode="full")
        t_in = TW.sum()
        iou = inter / np.maximum(a_in + t_in - inter, 1)
        j = np.unravel_index(np.argmax(iou), iou.shape)
        dy, dx = j[0] - (h - 1), j[1] - (w - 1)
        if best is None or iou[j] > best[0]:
            best = (float(iou[j]), float(sc), int(dx * k), int(dy * k))
    return best


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    old = Image.open(OLD).convert("RGB")
    shape = (old.height, old.width)
    hair = placed("purple-hair", shape)
    bat = ndi.binary_dilation(placed("black-bat", shape), iterations=4)
    weight = np.zeros(shape, bool)
    weight[ROWS[0] : ROWS[1]] = True
    weight &= ~bat
    front = np.asarray(Image.open(NEW_FRONT).convert("RGBA"))[..., 3] > 128

    coarse = search(hair, weight, front, np.arange(0.40, 0.96, 0.02), 2)
    print(f"coarse: iou {coarse[0]:.3f}, scale {coarse[1]:.3f}, at ({coarse[2]}, {coarse[3]})")
    fine = search(hair, weight, front, np.arange(coarse[1] - 0.02, coarse[1] + 0.021, 0.004), 1)
    print(f"fine:   iou {fine[0]:.3f}, scale {fine[1]:.4f}, at ({fine[2]}, {fine[3]})")
    iou, sc, dx, dy = fine
    json.dump({"scale": sc, "offset": [dx, dy], "iou": iou, "rows": ROWS}, open(f"{OUT}/register.json", "w"), indent=1)

    w, h = int(front.shape[1] * sc), int(front.shape[0] * sc)
    A = np.asarray(Image.fromarray(front.astype(np.uint8) * 255).resize((w, h), Image.BILINEAR)) > 127
    edge = A & ~ndi.binary_erosion(A, iterations=2)
    view = np.asarray(old).astype(float) * 1.8
    ys, xs = np.nonzero(edge)
    ys, xs = ys + dy, xs + dx
    ok = (ys >= 0) & (ys < shape[0]) & (xs >= 0) & (xs < shape[1])
    view[ys[ok], xs[ok]] = (0, 255, 120)
    im = Image.fromarray(view.clip(0, 255).astype(np.uint8)).crop((380, 120, 900, 1000))
    ImageDraw.Draw(im).line([(0, ROWS[0] - 120), (im.width, ROWS[0] - 120)], fill=(255, 0, 0))
    ImageDraw.Draw(im).line([(0, ROWS[1] - 120), (im.width, ROWS[1] - 120)], fill=(255, 0, 0))
    im.save(f"{OUT}/register.png")
    print(f"{OUT}/register.png")


if __name__ == "__main__":
    main()
