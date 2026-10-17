"""Contrast variants of the reference's hair, to find the one where the strand lines are readable.

    ./harness/run.sh harness/franzi_hair/contrast.py

The hair is near-black with its lines a few levels darker or lighter than the mass, so on the plain reference they cannot be seen.
Writes out/franzi/contrast-variants.png: the same head crop (440, 60, 900, 560) three ways, each labelled.

    A  linear stretch of the dark range (the one strands.py used)
    B  gamma on the dark range, which lifts the shadows more than the lights
    C  local contrast: luminance minus its own blur, divided by the local spread, so a line reads the same in the dark curtain and in
       the lighter crown (the lines are a local, not a global, difference)
"""

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

BOX = (440, 60, 900, 560)
Z = 2

a = np.array(Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")).astype(float)
lum = a[..., :3].mean(2)
hair = ndimage.binary_fill_holes(np.array(Image.open("ref/franzi/segments/04-bikini-fullbody/black-hair.png"))[..., 3] > 128)


def to_img(v):
    im = Image.fromarray((np.clip(v, 0, 1) * 255).astype(np.uint8)).convert("RGB")
    return im.crop(BOX).resize(((BOX[2] - BOX[0]) * Z, (BOX[3] - BOX[1]) * Z), Image.LANCZOS)


A = np.clip((lum - 8) / 100, 0, 1)
B = np.clip(lum / 90, 0, 1) ** 0.45
mu = ndimage.gaussian_filter(lum, 7)
sd = np.sqrt(ndimage.gaussian_filter((lum - mu) ** 2, 7)) + 2.0
C = 0.5 + 0.28 * (lum - mu) / sd
# outside the hair the skin, the eyes and the page would dominate, so show them flat
for v in (A, B, C):
    v[~hair] = np.where(lum[~hair] > 110, 0.9, 0.12)

pad = 36
imgs = [(to_img(A), "A  linear stretch"), (to_img(B), "B  gamma on the dark range"), (to_img(C), "C  local contrast")]
sheet = Image.new("RGB", (sum(i.width for i, _ in imgs) + 16 * 2, imgs[0][0].height + pad), "white")
x = 0
for im, name in imgs:
    sheet.paste(im, (x, pad))
    ImageDraw.Draw(sheet).text((x + 8, 10), name, fill=(0, 0, 0))
    x += im.width + 16
sheet.save("out/franzi/contrast-variants.png")
for name, v in (("A", A), ("B", B), ("C", C)):
    Image.fromarray((np.clip(v, 0, 1) * 255).astype(np.uint8)).save(f"out/franzi/contrast-{name}.png")
print("wrote out/franzi/contrast-variants.png", sheet.size)
