"""The visible regions of Franzi's head in the reference, as masks: face skin, each ear, the hair, and the hair silhouette.

    ./harness/run.sh harness/franzi_hair/outline_masks.py

The render's outline layer is built on these (docs/adult-body-status.md, "outlines"): one hair silhouette drawn after the body and
before the face, with the visible face and ears drawn over it, each its own region traced to the real edge. Every skin and hair edge
then carries exactly one stroke, the skin region's, because the silhouette is built to run under the skin regions (it takes them
in, shrunk a few pixels) and so never has an edge of its own where hair meets skin. The earlier build cut the hair into pieces with
straight lines, gave each its own outline, and mirrored the face from its right half, which is where the steps, ledges, hooks and
doubled lines came from.

Writes out/franzi_hair/outline_masks.npz (boolean arrays, reference canvas 1312 x 2440) and prints each region's size.

    face    the visible skin of forehead, cheeks and chin (rows above the chin, one component), filled across the eyes and brows
    ear_l   ear_r    the visible skin of each ear
    hair    every visible hair pixel: the dome, the curtains, the left lock, the ponytail, the back hair behind the neck
    sil     the hair silhouette: hair, plus face and ears shrunk by SINK px (so its edge never meets theirs), holes filled
"""

import numpy as np
from PIL import Image
from scipy import ndimage

SINK = 4  # px: how far the silhouette runs under a skin region
a = np.array(Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")).astype(int)
rgb, alpha = a[..., :3], a[..., 3]
lum = rgb.mean(2)
H, W = lum.shape

# --- skin: warm and light. The lit colour (252,208,181) and the shadow the hair casts on it (214,154,123) both have red minus blue
# near 70 to 90, hair, eyes, lines and the page are near 0, and the bikini is white.
warm = ((rgb[..., 0] - rgb[..., 2]) > 45) & (lum > 105) & (alpha > 128)
warm[600:] = False  # head and neck only; the body is the body part's

# --- the face: the component holding the forehead, closed over the thin dark lines inside it (lashes, brows, mouth), filled.
# Label on an eroded mask: the jaw's drawn line is about 2 px and its anti-aliased edge is warm enough to bridge it from the face to the
# neck, which closed the face onto the neck and chest. The component is grown back inside the skin afterwards.
# The eyes, lashes and brows are dark but they are not hair, so they belong to the face: in the eye rows a dark pixel that is not in the
# hair layer counts as face. (A first version filled each row between the skin's own outermost pixels, which cannot reach the strip of
# skin left of the outer eye corner, since that strip only joins the rest below the eye, and it left a rectangular hole round the eye.)
seg_all = np.array(Image.open("ref/franzi/segments/04-bikini-fullbody/black-hair.png"))[..., 3] > 128
feature = (lum < 125) & (alpha > 128) & ~ndimage.binary_dilation(seg_all, iterations=1)
feature[:235] = False
feature[352:] = False
skin_like = warm | feature
lab, _ = ndimage.label(ndimage.binary_erosion(skin_like, iterations=2), structure=np.ones((3, 3)))
core = lab == lab[330, 660]
face = ndimage.binary_dilation(core, iterations=3) & skin_like
face = ndimage.binary_fill_holes(ndimage.binary_closing(face, iterations=2))
# The segmentation counted the black brows as hair, so each cut a slit into the face from the curtain side: close the face over any gap
# up to 17 px tall between skin above and below it, in the rows from the brows to the lower lashes only.
band = np.zeros_like(face)
band[235:352] = True
face = face | (ndimage.binary_closing(face, structure=np.ones((17, 1))) & band)
face = ndimage.binary_fill_holes(face)

# The thin slivers of skin between a curtain and the face's drawn edge line are joined to the face by the closing above and showed as
# a staircase in its edge. At the temples (above the cheek, outside the eye-to-eye width) open the face with a disc wider than a
# sliver: what is thinner than that is not the face, and falls into the strips below.
yy, xx = np.mgrid[0:H, 0:W]
disc = (np.hypot(*np.mgrid[-6:7, -6:7]) <= 6)
opened = ndimage.binary_opening(face, structure=disc)
temple = (yy < 345) & (np.abs(xx - 660) > 40)
face = np.where(temple, opened, face)
face = ndimage.label(face, structure=np.ones((3, 3)))[0] == ndimage.label(face, structure=np.ones((3, 3)))[0][330, 660]

# --- the ears: the skin components beside the face at the ears' height
def comp_near(x, y, avoid):
    m = warm & ~avoid
    lab2, _ = ndimage.label(ndimage.binary_closing(m, iterations=2), structure=np.ones((3, 3)))
    ys, xs = np.nonzero(lab2)
    i = int(np.argmin((xs - x) ** 2 + (ys - y) ** 2))
    return ndimage.binary_fill_holes(lab2 == lab2[ys[i], xs[i]])


face_wide = ndimage.binary_dilation(face, iterations=2)
ear_r = comp_near(790, 335, face_wide)
ear_l = comp_near(535, 345, face_wide)

# --- strips: small skin components beside the face (the side of the neck under the ear, between a curtain and the cheek line). They are
# separated from the cheek by its drawn line, so they are their own regions; each runs a few pixels under the face so the face's
# stroke is the only line between them and nothing doubles it.
lab3, n3 = ndimage.label(warm & ~ndimage.binary_dilation(face, iterations=2) & ~ear_r & ~ear_l, structure=np.ones((3, 3)))
near_face = ndimage.binary_dilation(face, iterations=14)
strips = np.zeros_like(face)
for i in range(1, n3 + 1):
    c = lab3 == i
    ys_, xs_ = np.nonzero(c)
    if c.sum() >= 25 and (near_face & c).any() and ys_.min() > 185 and ys_.max() < 465 and 550 < xs_.min() and xs_.max() < 805:
        strips |= c
strips = ndimage.binary_fill_holes(ndimage.binary_closing(strips, iterations=3))
strips = strips | (ndimage.binary_dilation(strips, iterations=4) & face)

# --- the hair: the segmentation layer, plus every dark opaque pixel in the head box that it missed. The layer's edge is ragged (an AI
# segmentation), so smooth it a little; the silhouette is fitted from this.
seg = np.array(Image.open("ref/franzi/segments/04-bikini-fullbody/black-hair.png"))[..., 3] > 128
dark = (lum < 95) & (alpha > 128) & (np.abs(rgb[..., 0] - rgb[..., 2]) < 40)
box = np.zeros_like(seg)
box[40:560, 430:920] = True
hair = ndimage.binary_fill_holes(seg | (dark & box & ndimage.binary_dilation(seg, iterations=8)))
hair &= ~face
hair = ndimage.gaussian_filter(hair.astype(float), 1.0) > 0.5

# --- the ponytail runs on behind the shoulder. In the reference its end tapers to a point exactly where the shoulder's line crosses it
# (the shoulder's top is at y 506 to 516 under it), so the hair appears to go behind. The mask stops there, which in the render leaves
# a rounded end above the shoulder and a sliver of page between it and the neck. Extend it down past the shoulder line and left to
# the neck, into the part the body covers when the hair is drawn behind it (render order: the silhouette first, then the body).
from PIL import ImageDraw
ext = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(ext)
d.polygon([(718, 450), (734, 490), (752, 500), (761, 505), (783, 510), (790, 516), (791, 575), (700, 575), (700, 450)], fill=255)  # the right edge carries on the taper the mask has at rows 490 to 513 (x 799 to 790), then drops behind the shoulder
hair = hair | (np.array(ext) > 0)

# --- the silhouette
sink_face = ndimage.binary_erosion(face, iterations=SINK)
sink_ears = ndimage.binary_erosion(ear_r | ear_l | (strips & ~face), iterations=max(1, SINK - 1))
sil = ndimage.binary_fill_holes(ndimage.binary_closing(hair | sink_face | sink_ears, iterations=2))

np.savez_compressed("out/franzi_hair/outline_masks.npz", face=face, ear_l=ear_l, ear_r=ear_r, strips=strips, hair=hair, sil=sil)
for name, m in (("face", face), ("ear_l", ear_l), ("ear_r", ear_r), ("strips", strips), ("hair", hair), ("sil", sil)):
    ys, xs = np.nonzero(m)
    print(f"{name:6s} {int(m.sum()):7d} px  x {xs.min()}..{xs.max()}  y {ys.min()}..{ys.max()}")
