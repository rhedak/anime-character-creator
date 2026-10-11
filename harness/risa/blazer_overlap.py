"""How well our blazer lies on hers (`docs/risa-plan.md`, M7): the overlap of the two
blazers' navy, and the distance between their outlines, on the same pixels.

Both figures are on white at one head scale (`compare.py`). Her hair lies over her
shoulders where ours does not, so the comparison is made on the torso below the
armpit, rows 650 to 860 of her composite, where nothing covers either garment but
the hands, and on the whole garment separately for the record.

    ./harness/run.sh harness/risa/blazer_overlap.py
"""

import numpy as np
from compare import R, _SLENDER_HEAD_SCALE, ours, reference
from scipy import ndimage as ndi

from anime_character_creator.presets import RISA

NAVY = np.array([27, 39, 57])


def navy(im, tol=38):
    a = np.asarray(im).astype(int)
    return np.abs(a - NAVY).sum(2) < tol


ref_im = reference()
mine_im = ours(RISA, ref_im.size, r=R * _SLENDER_HEAD_SCALE)
rn, mn = navy(ref_im), navy(mine_im)
# The blazer is the navy in the garment's band, which keeps her black hair (a different
# grey) and the black socks out of it.
box = np.zeros_like(rn)
box[415:870, 440:825] = True
rn, mn = rn & box, mn & box


def report(label, rows):
    sel = np.zeros_like(rn)
    sel[rows[0] : rows[1]] = True
    a, b = rn & sel, mn & sel
    inter, union = (a & b).sum(), (a | b).sum()
    edge_a = a ^ ndi.binary_erosion(a)
    edge_b = b ^ ndi.binary_erosion(b)
    # Mean distance from each of our outline's pixels to her nearest outline pixel.
    d = ndi.distance_transform_edt(~edge_a)[edge_b].mean()
    print(f"{label:<34} overlap {inter / union:.3f}   mean outline distance {d:.2f} px ({d / (R * _SLENDER_HEAD_SCALE):.3f} head radii)")


report("whole garment, rows 415 to 870", (415, 870))
report("below the armpit, rows 650 to 860", (650, 860))

# A picture of where they differ: hers only in red, ours only in blue, both in grey.
from PIL import Image

out = np.full((*rn.shape, 3), 255, np.uint8)
out[rn & mn] = (170, 170, 170)
out[rn & ~mn] = (220, 40, 40)
out[~rn & mn] = (40, 80, 230)
Image.fromarray(out).crop((430, 405, 835, 880)).resize((810, 950), Image.NEAREST).save("out/risa/m7_overlap.png")
print("wrote out/risa/m7_overlap.png")
