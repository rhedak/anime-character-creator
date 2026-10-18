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

# --- the ears. The whole visible ear, shaded inner part and the fold lines included: skin and its drawn lines are warm (red minus blue
# 25 or more, the fold lines 38 to 77, the shaded concha 70 to 95) where hair is neutral (0 to 7), so no brightness test is used. The
# first version required brightness over 105 like the face does and kept only the pale rim of each ear (263 and 844 px).
warm_ear = ((rgb[..., 0] - rgb[..., 2]) > 25) & (alpha > 128)


def ear_in(box, seed):
    x0, y0, x1, y1 = box
    m = np.zeros_like(warm_ear)
    m[y0:y1, x0:x1] = warm_ear[y0:y1, x0:x1]
    m &= ~ndimage.binary_dilation(face, iterations=2)
    lab_e, _ = ndimage.label(m, structure=np.ones((3, 3)))
    c = lab_e == lab_e[seed[1], seed[0]]
    return ndimage.binary_fill_holes(ndimage.binary_closing(c, iterations=1))


ear_r = ear_in((765, 285, 830, 375), (792, 330))
ear_l = ear_in((505, 295, 548, 375), (532, 340))

# --- the concha: the shaded inner part of each ear (lum 80 to 160 against the pale rim's 200 or more). Taken inside the ear shrunk 2 px so
# the ear's dark outline is not mistaken for shade, and opened a little so speckle does not count.
def concha_of(ear):
    c = ndimage.binary_erosion(ear, iterations=2) & (lum < 185)
    c = ndimage.binary_opening(c, iterations=1)
    lab_c, n = ndimage.label(c, structure=np.ones((3, 3)))
    if n == 0:
        return c
    sizes = ndimage.sum(c, lab_c, range(1, n + 1))
    keep = [1 + i for i, z in enumerate(sizes) if z >= 25]  # the upper and the lower shaded part are separate components
    return ndimage.binary_fill_holes(np.isin(lab_c, keep))


concha_r, concha_l = concha_of(ear_r), concha_of(ear_l)

# --- strips: the skin that shows beside the face between a curtain and the cheek's drawn edge line, three places in the reference:
# the pale sliver at the left temple (between two dark lines, crossed by the brow's extension), the shaded two-lobed region at the left
# cheek and the tan strip beside the right ear. Each is skin-warm and not a dark line (red minus blue over 40, brightness over 100), and
# the thin dark dividers inside them (the brow line, the cheek's diagonal) are closed over so a strip is one region and not five. A first
# version took any warm piece beside the face and got fragments (a sliver in five parts, a strip's top half missing). Each runs a few px
# under the face so the face's stroke is the only line between them.
tone = ((rgb[..., 0] - rgb[..., 2]) > 40) & (lum > 100) & (alpha > 128)
tone &= ~ndimage.binary_dilation(face, iterations=2) & ~ear_r & ~ear_l
strips = np.zeros_like(face)
for (bx0, by0, bx1, by1), close_it, min_px in (((570, 236, 600, 318), 3, 60), ((552, 340, 590, 392), 2, 60), ((748, 338, 772, 378), 2, 40)):
    m = np.zeros_like(tone)
    m[by0:by1, bx0:bx1] = tone[by0:by1, bx0:bx1]
    m = ndimage.binary_closing(m, structure=np.ones((7, 1)), iterations=1) | m  # close the dark dividers that cross a strip
    m = ndimage.binary_fill_holes(ndimage.binary_closing(m, iterations=close_it))
    lab3, n3 = ndimage.label(m, structure=np.ones((3, 3)))
    for i in range(1, n3 + 1):
        if (lab3 == i).sum() >= min_px:
            strips |= lab3 == i
# keep only the three strips themselves: the stray 1 to 14 px pieces the closing leaves are not regions
lab_s, n_s = ndimage.label(strips, structure=np.ones((3, 3)))
strips = np.isin(lab_s, [i for i in range(1, n_s + 1) if (lab_s == i).sum() >= 60])
strips = strips | (ndimage.binary_dilation(strips, iterations=3) & face)

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
# the strips are drawn over the silhouette, and the pale highlight and dark line between a strip and the face belong to neither mask, so
# the silhouette covers each strip with a 6 px margin (up to the face, which is drawn over it) or the page shows through there
sil = ndimage.binary_fill_holes(ndimage.binary_closing(hair | sink_face | sink_ears | ndimage.binary_dilation(strips, iterations=6), iterations=2))

np.savez_compressed("out/franzi_hair/outline_masks.npz", face=face, ear_l=ear_l, ear_r=ear_r, concha_l=concha_l, concha_r=concha_r, strips=strips, hair=hair, sil=sil)
for name, m in (("face", face), ("ear_l", ear_l), ("ear_r", ear_r), ("concha_l", concha_l), ("concha_r", concha_r), ("strips", strips), ("hair", hair), ("sil", sil)):
    ys, xs = np.nonzero(m)
    print(f"{name:6s} {int(m.sum()):7d} px  x {xs.min()}..{xs.max()}  y {ys.min()}..{ys.max()}")
