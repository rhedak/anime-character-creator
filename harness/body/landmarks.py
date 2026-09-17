"""Katherina's body landmarks, measured off katherina_grok.jpg.

Labels the reference's non-outline fills (the same method as the hat and staff
traces) and reports each garment region's rows and spans in head radii, on the
hat's calibration: 173.7 px per head radius, head centre (650, 481). Component
ids below are what `scipy.ndimage.label(rgb.sum(2) > 60)` gives on that file.
These are the numbers `BODY_TYPES["tall_chibi"]` was solved from.
"""

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

REF = "../time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg"
OX, OY, SC = 650.0, 481.0, 173.7
rgb = np.asarray(Image.open(REF).convert("RGB")).astype(int)
lab, _ = ndi.label(rgb.sum(2) > 60)


def rows(ids):
    ys = np.nonzero(np.isin(lab, ids).any(1))[0]
    return round((ys.min() - OY) / SC, 3), round((ys.max() - OY) / SC, 3)


def span(ids, y):
    xs = np.nonzero(np.isin(lab, ids)[y])[0]
    return round((xs.min() - OX) / SC, 3), round((xs.max() - OX) / SC, 3)


print("soles / figure heads", rows([216, 218])[1], (rows([216, 218])[1] + 1) / 2)
print("coat top, coat hem", rows([179, 180])[0], rows([202, 203])[1])
print("belt band", rows([192, 193, 194, 195, 196, 198]), span([192, 193, 194, 195, 196, 198], 900))
print("skirt hem", rows([204])[1], "widest", span([204], 1180), "under coat", span([204], 1040))
print("legs", rows([212, 213]), "boots", rows([216, 218]))
print("hair lowest", rows([8])[1])
