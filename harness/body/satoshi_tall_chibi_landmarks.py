"""Satoshi's tall-chibi body landmarks, measured off
`ref-local/satoshi-tall-chibi/satoshi-tall-chibi.png` (`docs/satoshi-tall-chibi-plan.md`,
T2a).

Unlike Katherina's `landmarks.py`, this reference has no prior calibration (no
traced hat or prop gives a known head radius), so the head circle is
calibrated here from the face-skin silhouette itself: the widest row of skin
colour in the face region is the head's widest point (a circle's diameter),
which also locates its vertical centre. This is an estimate, not a trace-grade
calibration, flagged in the plan doc's risks.

Garment regions are found by colour (sampled from the image itself, printed
below) rather than by component id, since this PNG's fills were not
pre-catalogued the way `katherina_grok.jpg`'s were. `big_rows`/`span` drop
stray same-coloured pixels elsewhere in the image (a hair shadow, an eyebrow)
by keeping only components at least `min_size` pixels.
"""

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

REF = "ref-local/satoshi-tall-chibi/satoshi-tall-chibi.png"
im = Image.open(REF).convert("RGBA")
arr = np.asarray(im).astype(int)
bg = np.full(arr.shape[:2] + (3,), 255)
alpha = arr[:, :, 3:4] / 255.0
rgb = (arr[:, :, :3] * alpha + bg * (1 - alpha)).astype(int)


def mask_rgb(col, tol=14):
    return np.abs(rgb - np.array(col)).sum(2) <= tol


def big_rows(m, min_size=200):
    lab, n = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= min_size])
    ys = np.nonzero(keep.any(1))[0]
    return (int(ys.min()), int(ys.max())) if len(ys) else None


def span(m, y):
    xs = np.nonzero(m[y])[0]
    return (int(xs.min()), int(xs.max())) if len(xs) else None


# --- head calibration ---
# The widest row of face skin, in the face's own y-range (excludes the hands,
# a near-identical colour, lower in the image).
skin = mask_rgb([246, 213, 182], 14)
skin[:150, :] = False
skin[470:, :] = False
widths = [
    (y, xs.min(), xs.max(), xs.max() - xs.min())
    for y in range(150, 470)
    if len((xs := np.nonzero(skin[y])[0]))
]
y0, x0, x1, w = max(widths, key=lambda t: t[3])
OX, OY, R = (x0 + x1) / 2, y0, w / 2
print(f"head calibration: centre ({OX:.0f}, {OY:.0f}), r={R:.1f}px")


def hy(y):
    return round((y - OY) / R, 3)


def hx(x):
    return round((x - OX) / R, 3)


# --- garment colours, sampled from the image (see the module docstring) ---
tunic = mask_rgb([105, 127, 101], 25)
sleeve = mask_rgb([177, 163, 137], 18)
belt = mask_rgb([91, 70, 53], 10) | mask_rgb([83, 66, 50], 10)
trousers = mask_rgb([84, 86, 75])
boots = mask_rgb([111, 77, 50])

shoulder_rows = big_rows(tunic | sleeve)
waist_rows = big_rows(belt)
hem_rows = big_rows(trousers)
ankle_rows = big_rows(boots)

print("shoulder (tunic+sleeve) top", hy(shoulder_rows[0]), "  tall_chibi 1.13")
print("waist (belt)", hy((waist_rows[0] + waist_rows[1]) / 2), "  tall_chibi 2.384")
print("hem (crotch, where legs part)", hy(hem_rows[0]), "  tall_chibi 4.26 (skirt hem, not comparable)")
print("ankle (boot shaft top)", hy(ankle_rows[0]), "  tall_chibi 5.55")
print("sole (boot bottom)", hy(ankle_rows[1]), "  tall_chibi 5.94")

waist_span = span(belt, (waist_rows[0] + waist_rows[1]) // 2)
print("waist half-width", round((hx(waist_span[1]) - hx(waist_span[0])) / 2, 3), "  tall_chibi 0.563")

hem_span = span(trousers, hem_rows[0] + 15)
print("hem half-width (pelvis, pre-split)", round((hx(hem_span[1]) - hx(hem_span[0])) / 2, 3), "  tall_chibi 1.13 (skirt, not comparable)")

leg_halfw = []
for y in (900, 1000, 1100, 1200):
    xs = np.nonzero(trousers[y])[0]
    d = np.diff(xs)
    gaps = np.nonzero(d > 5)[0]
    left = xs[: gaps[0] + 1]
    leg_halfw.append((left.max() - left.min()) / 2 / R)
print("leg half-width (mean of 4 rows)", round(sum(leg_halfw) / len(leg_halfw), 3), "  tall_chibi 0.23")

crown_y = OY - R
fig_h = ankle_rows[1] - crown_y  # crown to sole; excludes hair overshoot, same convention build_skeleton uses
print("implied heads (crown-to-sole / head diameter)", round(fig_h / (2 * R), 2), "  tall_chibi 3.47")
