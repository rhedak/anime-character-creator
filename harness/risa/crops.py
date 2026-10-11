"""Which of Risa's segments are true pixel crops of `ref-local/mio/mio.png`
(`docs/risa-plan.md`, M2).

The skill's standing check: an AI tool's layer export is not necessarily a crop
of the composite, and coordinates may be taken off a segment only if it is one
(the witch hat lost two passes to a layer that was a regenerated variant). For
each segment this finds the offset at which it best matches the composite, by a
masked sum-of-squares search over every offset (three FFT correlations per
channel), and reports the mean RGB difference there, in 0 to 255 units per
channel, over the segment's own opaque pixels eroded by two so the antialiased
edge does not count.

A crop matches at a difference near zero (Keiko's three were 0.012 to 0.097). A
regenerated variant matches nowhere, so its best difference stays large and the
best offset is noise. The runner-up offset away from the best is printed too,
since a flat region can match at several offsets and the best of those is not a
placement.

    ./harness/run.sh harness/risa/crops.py
"""

import glob

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.signal import fftconvolve

BASE = "ref-local/mio"
comp = Image.open(f"{BASE}/mio.png").convert("RGBA")
carr = np.asarray(comp).astype(float)
# Composite colour where the composite is itself opaque; elsewhere the page is
# transparent and a segment pixel there is a genuine mismatch.
ch, cw = carr.shape[:2]
crgb = carr[:, :, :3] * (carr[:, :, 3:4] / 255.0)
calpha = (carr[:, :, 3] > 250).astype(float)


def search(seg_path):
    seg = np.asarray(Image.open(seg_path).convert("RGBA")).astype(float)
    sh, sw = seg.shape[:2]
    m = ndi.binary_erosion(seg[:, :, 3] > 250, iterations=2)
    if m.sum() < 30:
        m = seg[:, :, 3] > 250
    m = m.astype(float)
    # A mismatch is also a segment pixel over a transparent composite pixel, so
    # fold the composite's opacity in as a fourth channel that must read 1.
    chans = [(crgb[:, :, c], seg[:, :, c] * seg[:, :, 3] / 255.0) for c in range(3)]
    chans.append((calpha * 255.0, np.full((sh, sw), 255.0)))
    ssd = None
    for big, small in chans:
        # sum over the mask of (big - small)^2, for every offset.
        a2 = fftconvolve(big**2, m[::-1, ::-1], mode="valid")
        ab = fftconvolve(big, (m * small)[::-1, ::-1], mode="valid")
        b2 = (m * small**2).sum()
        term = a2 - 2 * ab + b2
        ssd = term if ssd is None else ssd + term
    mean = np.sqrt(np.maximum(ssd, 0) / (m.sum() * 4))
    iy, ix = np.unravel_index(np.argmin(mean), mean.shape)
    best = mean[iy, ix]
    # The runner-up: the best offset at least 12 px from the winner.
    far = mean.copy()
    far[max(0, iy - 12) : iy + 13, max(0, ix - 12) : ix + 13] = np.inf
    ry, rx = np.unravel_index(np.argmin(far), far.shape)
    return (ix, iy), best, (rx, ry), far[ry, rx], (sw, sh)


if __name__ == "__main__":
    files = sorted(glob.glob(f"{BASE}/segments/**/*.png", recursive=True))
    print(f"composite {cw} x {ch}\n")
    print(f"{'segment':42s} {'size':>10s}  {'offset (x, y)':>14s}  {'rms diff':>8s}   runner-up")
    for f in files:
        name = f.split("segments/")[1]
        if "black-background" in name:
            continue
        (x, y), d, (rx, ry), rd, (w, h) = search(f)
        verdict = "CROP" if d < 6 else ("close" if d < 20 else "NOT a crop")
        print(
            f"{name:42s} {w:4d}x{h:<5d}  ({x:4d}, {y:4d})   {d:8.2f}   ({rx}, {ry}) {rd:.1f}   {verdict}"
        )
