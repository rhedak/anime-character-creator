"""Risa's body target from the bikini image (docs/risa-polish-plan.md, stage 1): the figure's silhouette less the hair, neck down to the image's lower edge (mid-thigh).

    ./harness/run.sh harness/risa_adult/target.py

The bikini image is canon for her proportions (the plan's decision 1). The body is the cutout's alpha less Grok's hair layer (`long-red-hair`), the holes that hair strands
leave inside it filled. Writes, on the bikini's grid (1312 x 1504):

    out/risa_adult/target.png        the body, white on black
    out/risa_adult/target-unknown.png  where the body's edge is not known: hair over or beside the body, within a few px of it
    out/risa_adult/target-check.png  the body's edge in cyan and the unknown zone in magenta over the reference, for the eye

The unknown zone exists because the hair layer cannot say whether a strand lies in front of the body or behind it beside the body: both are hair pixels next to skin. In `00`
locks lie in front of both shoulders, from beside the neck down the bust's sides to the band, and strand tips cross the forearms, so taking the hair out bites into the body
there. Below the band the hair between an arm and the torso hangs behind them (the gap shows it), so those edges are known, and so is every outer edge (the arm is in front of
the hair that hangs beside it). Hence two rules: above the band (`BAND_D`), hair within `UNKNOWN_PX` of the body and inside the row's span of it (between the shoulder and the
neck or the bust, where a real body has no gap); below it, only the narrow bites a strand makes in an edge (what a closing of the body by a small disk would fill). The gate
counts no pixel of the zone either way, and skips a width whose edge lies in it.

Only small holes are filled: the gap between an arm and the torso is closed off where the hand touches the thigh, so a plain hole fill would take it for body.
"""

from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

REF = Path("ref/risa-adult")
OUT = Path("out/risa_adult")
OUT.mkdir(parents=True, exist_ok=True)
CHIN, H = 434.0, 352.0
NECK_D = 0.12  # the neck's top, in head heights below the chin: where adultBodyPath starts
HOLE_MAX = 1500  # px: a hole up to this size is a strand's gap; the arm gap is tens of thousands
UNKNOWN_PX = 10  # above the band, hair within this distance of the body is the unknown zone
BAND_D = 0.95  # the bikini top's lower edge (row 762, bust_metrics.py), in head heights below the chin
BITE_R = 7  # below the band, a bite up to about twice this wide is a strand across the edge

top = int(CHIN + NECK_D * H)
alpha = np.array(Image.open(REF / "00-bikini-transparent.png"))[..., 3] > 127
hair = np.array(Image.open(REF / "segments/00-bikini/long-red-hair.png"))[..., 3] > 127
body = alpha & ~hair
body[:top] = False
body = ndimage.binary_opening(body, structure=np.ones((3, 3)))
lab, n = ndimage.label(body)
sizes = ndimage.sum(body, lab, range(1, n + 1))
body = np.isin(lab, 1 + np.flatnonzero(sizes > 2000))  # the figure's pieces; the hands may be apart where strands cross the wrists
holes, nh = ndimage.label(~body)
hsizes = ndimage.sum(~body, holes, range(1, nh + 1))
body |= np.isin(holes, 1 + np.flatnonzero(hsizes <= HOLE_MAX))
band = int(CHIN + BAND_D * H)
cols = np.arange(body.shape[1])[None, :]
first = np.where(body.any(1), body.argmax(1), body.shape[1])[:, None]
last = np.where(body.any(1), body.shape[1] - 1 - body[:, ::-1].argmax(1), -1)[:, None]
near = ndimage.binary_dilation(body, iterations=UNKNOWN_PX) & (cols > first) & (cols < last)
yy, xx = np.mgrid[-BITE_R : BITE_R + 1, -BITE_R : BITE_R + 1]
bites = ndimage.binary_closing(body, structure=(xx**2 + yy**2) <= BITE_R**2)
unknown = hair & alpha & ~body & np.where(np.arange(body.shape[0])[:, None] < band, near, bites)
unknown[:top] = False

Image.fromarray((body * 255).astype(np.uint8)).save(OUT / "target.png")
Image.fromarray((unknown * 255).astype(np.uint8)).save(OUT / "target-unknown.png")

ref = np.array(Image.open(REF / "00-bikini.png").convert("RGB"))
chk = ref.copy()
chk[unknown] = (chk[unknown] // 3) + np.array([170, 0, 170], np.uint8)
chk[body ^ ndimage.binary_erosion(body, iterations=2)] = (0, 255, 255)
Image.fromarray(chk).crop((280, 380, 1060, 1504)).save(OUT / "target-check.png")
ys = np.where(body.any(1))[0]
print(f"target: {int(body.sum())} px body, {int(unknown.sum())} px unknown, rows {ys.min()} to {ys.max()}")
