"""Places on Risa's reference that the risa_adult scripts share (reference pixels, ref/risa-adult/00-bikini.png)."""

import numpy as np
from PIL import Image, ImageDraw

W, H = 1312, 1504

# the two brows, the points harness/risa_adult/brows.py snaps onto the drawn lines
BROW_PTS = [
    [(571, 283), (580, 278), (590, 274), (602, 271), (614, 269), (626, 269), (636, 270), (645, 272)],
    [(686, 269), (693, 265), (702, 261), (713, 259), (724, 259), (735, 261), (746, 264), (758, 268), (770, 272)],
]


def box(x0, y0, x1, y1):
    b = np.zeros((H, W), bool)
    b[y0:y1, x0:x1] = True
    return b


def brow_mask(width=7):
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    for pts in BROW_PTS:
        d.line(pts, fill=255, width=width)
    return np.array(img) > 0


# the eyes' upper edges: the lids and lashes are dark lines too
EYES_MASK = box(566, 294, 628, 360) | box(698, 280, 766, 360)

# the fringe's domain: the hair in it is a shape of its own over the skin (outline_masks.py)
DOM_BOX = (568, 176, 780, 306)
