"""Where the reference shades Risa (docs/risa-polish-plan.md, stage 8): per material, the pixels darker than that material's median, marked in colour over the reference.

    ./harness/run.sh harness/risa_adult/shadow_map.py

A garment is its Grok segment layer, darker than 0.82 of its median luminance (smoothed 2 px); the skin is the figure less the garments, warm and light, darker than 0.88 of its median.
Writes out/risa_adult/shadow-map-01.png (the uniform: the blazer blue, the shirt red, the skirt green, the skin magenta) and shadow-map-00.png (the bikini), and prints each share.
"""

import numpy as np
from PIL import Image
from scipy import ndimage
def shadows(img_path, layers, skin_from=None, out=None, crop=None):
    img = np.array(Image.open(img_path).convert("RGB")).astype(float)
    L = ndimage.gaussian_filter(img @ np.array([0.299, 0.587, 0.114]), 2)
    vis = (img * 0.35 + 255 * 0.65).astype(np.uint8)
    covered = np.zeros(L.shape, bool)
    colours = [(30, 60, 220), (220, 30, 30), (20, 160, 60), (200, 120, 0), (150, 0, 200)]
    for k, lay in enumerate(layers):
        m = np.array(Image.open(lay))[..., 3] > 200
        covered |= m
        med = np.median(L[m]); sh = m & (L < 0.82 * med)
        vis[sh] = colours[k % len(colours)]
        print(f"  {lay.split('/')[-1]:28s} median L {med:5.1f}, shadow {100 * sh.sum() / m.sum():4.1f}% of it")
    if skin_from is not None:
        a = np.array(Image.open(skin_from))[..., 3] > 200
        skin = a & ~covered & (img[..., 0] > img[..., 2] + 25) & (L > 120)
        med = np.median(L[skin]); sh = skin & (L < 0.88 * med)
        vis[sh] = (255, 0, 200)
        print(f"  skin                         median L {med:5.1f}, shadow {100 * sh.sum() / skin.sum():4.1f}% of it")
    Image.fromarray(vis).crop(crop).save(out)
print("01 uniform:")
d = "ref/risa-adult/segments/01-school-uniform/"
shadows("ref/risa-adult/01-school-uniform.png", [d + "school-blazer.png", d + "white-collared-shirt.png", d + "pleated-skirt.png"], "ref/risa-adult/01-school-uniform-transparent.png", "out/risa_adult/shadow-map-01.png", (330, 220, 1010, 1504))
print("00 bikini:")
shadows("ref/risa-adult/00-bikini.png", ["ref/risa-adult/segments/00-bikini/white-bikini-top.png", "ref/risa-adult/segments/00-bikini/white-bikini-bottom.png"], "ref/risa-adult/00-bikini-transparent.png", "out/risa_adult/shadow-map-00.png", (300, 380, 1040, 1504))
