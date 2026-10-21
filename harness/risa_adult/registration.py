"""The uniform reference on the bikini reference's grid.

ref/risa-adult/README.md says the images share a pixel grid, and they do share a size (1312 x 1504), but the uniform figure is drawn at 0.786 of the bikini figure's scale (it
has to fit the knees and the loafers in the same frame), with the head higher. Tracing the uniform's pixels as if they were on the bikini's grid put the skirt under the breasts.

The two are registered on the head: the irises' centres (the green blobs, 617.3 / 319.9 and 727.1 / 307.8 in the bikini image, 629.5 / 243.0 and 715.8 / 233.6 in the uniform one)
fix the scale (the distance between them, 110.5 against 86.8 px: 1.273) and the offset (the midpoints), and the hair clip lands on the bikini's within a pixel (the centroids,
771.2 / 233.4 and 750.4 / 174.8 mapped, give 771.2 / 233.0). There is no rotation (the eye line slopes -0.110 in one and -0.109 in the other). With that mapping the blended
images line up head, hair, shoulders and the skirt's top against the briefs.

    S, to_bikini(x, y)       the scale and the mapping of a uniform pixel to the bikini's grid
    register(img, resample)  a PIL image of the uniform's size resampled onto the bikini's grid (white, or transparent for RGBA, where the uniform does not reach)
"""

import numpy as np
from PIL import Image
from scipy import ndimage

BIK_MID = (672.2, 313.85)  # the midpoint of the bikini image's two irises (617.3, 319.9) and (727.1, 307.8)
BIK_SEP = 110.5  # and how far apart they are
SIZE = (1312, 1504)


def irises(path):
    """The two irises' centres (left, right) of a reference image: its two largest green blobs in the rows of the eyes."""
    a = np.array(Image.open(path).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = (g > r + 8) & (g > b + 8)
    green[:200] = False
    green[480:] = False
    lab, n = ndimage.label(green, structure=np.ones((3, 3)))
    blobs = []
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() >= 120:
            ys, xs = np.nonzero(m)
            blobs.append((m.sum(), xs.mean(), ys.mean()))
    blobs = sorted(sorted(blobs, reverse=True)[:2], key=lambda t: t[1])
    return (blobs[0][1], blobs[0][2]), (blobs[1][1], blobs[1][2])


class Registration:
    """An image of Risa fitted to the bikini image's grid by its irises: a scale (the ratio of the distances between them) and a translation (their midpoints), no rotation (the eye line
    slopes alike in every one of these images)."""

    def __init__(self, path):
        (x0, y0), (x1, y1) = irises(path)
        self.sep = float(np.hypot(x1 - x0, y1 - y0))
        self.s = BIK_SEP / self.sep
        self.mid = ((x0 + x1) / 2, (y0 + y1) / 2)

    def to_bikini(self, x, y):
        return (self.s * (x - self.mid[0]) + BIK_MID[0], self.s * (y - self.mid[1]) + BIK_MID[1])

    def register(self, img, resample=Image.BICUBIC, size=SIZE):
        """`size` taller than the bikini's canvas for the legs: the uniform figure is cropped at its loafers, which land below row 1504 of the bikini's grid."""
        a = 1 / self.s
        coeffs = (a, 0, self.mid[0] - BIK_MID[0] * a, 0, a, self.mid[1] - BIK_MID[1] * a)
        fill = (255, 255, 255, 0) if img.mode == "RGBA" else (255, 255, 255)
        return img.transform(size, Image.AFFINE, coeffs, resample=resample, fillcolor=fill)


# the first uniform image's registration, kept for what was traced from it (skirt_trace.py until 2026-10-21)
_U01 = Registration("ref/risa-adult/01-school-uniform.png")
S = _U01.s


def to_bikini(x, y):
    return _U01.to_bikini(x, y)


def register(img, resample=Image.BICUBIC):
    return _U01.register(img, resample)


# ---- from the bikini's grid onto our body, landmark to landmark
#
# Registered, the uniform's pixels are where Risa's are in the bikini image. Our body is not Risa's (the adult body is Franzi's, and Risa's torso is shorter and her hips narrower in the
# reference), so a cut traced at the reference's pixels would hang at the wrong height on it: the first skirt did, with the briefs showing under the hem. The rule of docs/risa-plan.md,
# decision 3, is to map every traced cut from landmark to landmark. The landmarks are measured by body_landmarks.py (the underwear's extent in the reference and in our render):
#
#   reference row   our row    what
#   434             434        the chin (the head's mapping fixes it)
#   762             761        the bikini top's lower edge
#   1019            1041       the briefs' top
#   1189            1226       the briefs' lower tip (the crotch)
#
# between them linear in the row, past the last with its slope (the legs have no landmark in the bikini image, which ends at mid thigh; the knee and ankle will take theirs from the
# uniform's socks and loafers). Widths: the garment's half-width is scaled by our width over the reference's where the two measure, the top (277 against 283 px, with the bust at
# -0.18) and the briefs (339 against 355), and kept past them.
ROWS = [(434.0, 434.0), (762.0, 761.0), (1019.0, 1041.0), (1189.0, 1226.0)]
WIDTHS = [(762.0, 283 / 277), (1019.0, 355 / 339)]  # (reference row, our width over the reference's)
CHIN, HEAD, CENTRE = 434.0, 352.0, 668.2


def body_row(y):
    """Our body's row for a row of the bikini's grid."""
    if y <= ROWS[0][0]:
        return y
    for (r0, b0), (r1, b1) in zip(ROWS, ROWS[1:]):
        if y <= r1:
            return b0 + (y - r0) * (b1 - b0) / (r1 - r0)
    (r0, b0), (r1, b1) = ROWS[-2], ROWS[-1]
    return b1 + (y - r1) * (b1 - b0) / (r1 - r0)


def width_ratio(y):
    if y <= WIDTHS[0][0]:
        return WIDTHS[0][1]
    if y >= WIDTHS[1][0]:
        return WIDTHS[1][1]
    t = (y - WIDTHS[0][0]) / (WIDTHS[1][0] - WIDTHS[0][0])
    return WIDTHS[0][1] + t * (WIDTHS[1][1] - WIDTHS[0][1])


def to_body(x, y):
    """A pixel of the bikini's grid as [x, d] for our body: x in head heights from the centre line, d in head heights below the chin."""
    return ((x - CENTRE) / HEAD * width_ratio(y), (body_row(y) - CHIN) / HEAD)
