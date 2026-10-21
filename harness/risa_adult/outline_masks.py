"""The visible regions of Risa's head in ref/risa-adult/00-bikini.png, as masks: face skin, hair, and the hair silhouette.

    ./harness/run.sh harness/risa_adult/outline_masks.py

The same idea as harness/franzi_hair/outline_masks.py (one hair silhouette drawn behind the body, the visible face drawn over it so
the skin's stroke is the only line between skin and hair), on Risa's reference. What is different about her:

  - Her hair is dark red, so it is told from skin by the green-to-red ratio (skin about 0.76, hair under 0.46), not by brightness.
  - Her hair hangs behind the whole body, in front of nothing: the curtains run down behind the shoulders and show between the arms
    and the torso and outside the arms. The silhouette therefore runs under the body: a run of body pixels with hair on both ends is
    filled, so the body drawn over it leaves no page showing through, while the page between an arm and the torso below the hair's
    ends stays open.
  - Her ears are under the hair, so there are no ear or strip regions.

Writes out/risa_adult/outline_masks.npz (boolean arrays on the reference canvas, 1312 x 1504) and out/risa_adult/masks-view.png.
"""

import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, "harness/risa_adult")
from zones import DOM_BOX, EYES_MASK, brow_mask  # noqa: E402

SINK = 4  # px: how far the silhouette runs under the face
IMG = "ref/risa-adult/00-bikini.png"
a = np.array(Image.open(IMG).convert("RGB")).astype(int)
cut = np.array(Image.open("ref/risa-adult/00-bikini-transparent.png").convert("RGBA"))[..., 3] > 128
rgb = a
lum = rgb.mean(2)
H, W = lum.shape
ratio = rgb[..., 1] / np.maximum(rgb[..., 0], 1)

seg = np.array(Image.open("ref/risa-adult/segments/00-bikini/long-red-hair.png"))[..., 3] > 128
skin = (ratio > 0.6) & (lum > 105) & (rgb[..., 0] - rgb[..., 2] > 45) & cut

# --- the face: as for Franzi, the component holding the cheeks, closed over the dark lines inside it (lashes, brows, mouth).
feature = (lum < 125) & cut & ~ndimage.binary_dilation(seg, iterations=1)
feature[:235] = False
feature[352:] = False
skin_like = skin | feature
skin_like[470:] = False  # head only: the chin's tip is at about row 455
lab, _ = ndimage.label(ndimage.binary_erosion(skin_like, iterations=2), structure=np.ones((3, 3)))
core = lab == lab[330, 660]
# The fringe leaves wedges of forehead a few px wide that the erosion above drops from the core, so above the eyes the core is grown back
# much further inside the skin (the jaw's bridge to the neck is below that, where it is grown 3 px only).
face = ndimage.binary_dilation(core, iterations=3) & skin_like
upper = np.zeros_like(face)
upper[:330] = True
face = face | (ndimage.binary_dilation(core, iterations=30) & skin_like & upper)
face = ndimage.binary_fill_holes(ndimage.binary_closing(face, iterations=2))
band = np.zeros_like(face)
band[235:352] = True
face = face | (ndimage.binary_closing(face, structure=np.ones((17, 1))) & band)
face = ndimage.binary_fill_holes(face)
disc = np.hypot(*np.mgrid[-1:2, -1:2]) <= 1  # Franzi's is 6; Risa's fringe leaves wedges and slits of forehead a few px wide that are real, so only the slivers under 3 px go
yy, xx = np.mgrid[0:H, 0:W]
opened = ndimage.binary_opening(face, structure=disc)
temple = (yy < 345) & (np.abs(xx - 660) > 40)
face = np.where(temple, opened, face)
# --- the hair: the segmentation layer plus every red pixel of the figure it missed, smoothed a little
red = (ratio < 0.55) & (rgb[..., 0] > 40) & cut
hair = ndimage.binary_fill_holes(seg | (red & ndimage.binary_dilation(seg, iterations=6)))
hair &= ~face
hair = ndimage.gaussian_filter(hair.astype(float), 1.0) > 0.5

# --- the fringe as its own shape. The skin is extended up under the fringe (everything in EXT that is hair or skin becomes skin) so that the gaps between the locks show
# skin; the fringe's hair (every hair pixel in DOM) is drawn over it as a shape of its own with the real tips and slits; and the edge lines are the pixels of that shape's
# boundary that touch skin, to be drawn thin (not the domain's own border, which lies inside the hair).
def box(x0, y0, x1, y1):
    b = np.zeros((H, W), bool)
    b[y0:y1, x0:x1] = True
    return b


DOM = box(*DOM_BOX)
EXT = box(596, 200, 732, 336)
# The face rule above counts any dark pixel the segment layer does not cover as skin (lashes, brows), so it takes the thin dark tips of the locks too, which shortens and
# narrows the fringe's lower edge. In the fringe's box the hair is therefore found by colour: dark red pixels (green to red ratio under 0.6, not light) that join the hair,
# not counting the two brows (thin dark lines over the skin, their snapped points as in brows.py) and the eyes.

brow_mask = brow_mask()
eyes_mask = EYES_MASK
dark_red = (ratio < 0.6) & (lum < 125) & (rgb[..., 0] > 30) & cut & ~brow_mask & ~eyes_mask
fringe_hair = ndimage.binary_propagation(hair & DOM, mask=(hair | dark_red) & DOM)
face_ext = face | (EXT & (hair | face))
nonhair = DOM & ~fringe_hair
fringe_hair = ndimage.gaussian_filter(fringe_hair.astype(float), 0.8) > 0.5
fringe_edge = fringe_hair & ndimage.binary_dilation(nonhair, iterations=1) 

# The cheek's contour runs from the temple down to the jaw and is one smooth curve in the reference, but hair strands cross it and leave small notches and hooks in the mask (the owner saw two). In the
# band of the cheeks and the jaw's upper half (rows 318 to 430) the mask is low-passed with a Gaussian of 6 px, which takes out anything under about a dozen pixels along the edge and keeps the curve. It is
# done after the hair and the fringe are computed, so that only the face's own edge and the silhouette change (the approved fringe and strands do not).
band_c = np.zeros_like(face)
band_c[318:430] = True
face = np.where(band_c, ndimage.gaussian_filter(face.astype(float), 6.0) > 0.5, face)
lab, _ = ndimage.label(face, structure=np.ones((3, 3)))
face = lab == lab[330, 660]
# face_ext is what the face's chain is fitted to (the skin extended up under the fringe): smoothed at the cheeks' edges only, away from the fringe's own zone
cheek_cols = np.zeros_like(face)
cheek_cols[:, :602] = True
cheek_cols[:, 732:] = True
face_ext = np.where(band_c & cheek_cols, ndimage.gaussian_filter(face_ext.astype(float), 6.0) > 0.5, face_ext)

# --- the silhouette: hair, the face shrunk, and every run of figure pixels that has hair at both ends (the body in front of the hair)
fig = cut | hair
body = fig & ~hair
filled = hair.copy()
for y in range(H):
    xs = np.nonzero(hair[y])[0]
    if len(xs) == 0:
        continue
    row = body[y]
    # runs of body pixels bounded by hair on both sides
    lab_r, n = ndimage.label(row)
    for i in range(1, n + 1):
        rx = np.nonzero(lab_r == i)[0]
        x0, x1 = rx[0], rx[-1]
        if x0 > 0 and x1 < W - 1 and hair[y, x0 - 1] and hair[y, x1 + 1]:
            filled[y, x0 : x1 + 1] = True
sink_face = ndimage.binary_erosion(face, iterations=SINK)
sil = ndimage.binary_fill_holes(ndimage.binary_closing(filled | sink_face, iterations=2))

np.savez_compressed("out/risa_adult/outline_masks.npz", face=face, face_ext=face_ext, hair=hair, sil=sil, fringe_hair=fringe_hair, fringe_edge=fringe_edge)
for name, m in (("face", face), ("hair", hair), ("sil", sil)):
    ys, xs = np.nonzero(m)
    print(f"{name:5s} {int(m.sum()):7d} px  x {xs.min()}..{xs.max()}  y {ys.min()}..{ys.max()}")

view = np.array(Image.open(IMG).convert("RGB")).astype(float)
for m, col, k in ((hair, (255, 255, 0), 0.0), (face, (0, 255, 255), 0.45)):
    view[m] = view[m] * (1 - k) + np.array(col) * k
edge = sil & ~ndimage.binary_erosion(sil, iterations=2)
view[edge] = (0, 255, 0)
Image.fromarray(view.astype(np.uint8)).save("out/risa_adult/masks-view.png")
