"""Our blazer's outline drawn over the reference, to check its shape.

    ./harness/run.sh harness/risa_adult/blazer_outline_check.py

Renders Risa in the whole uniform with the blazer in a marker colour, maps the render to the reference's pixels (compare_head.py's mapping: a head height of 352 px, the centre line at 668.2, the chin at 434),
takes the boundary of the marked region and draws it in cyan over ref/risa-adult/01-school-uniform.png registered to the bikini's grid (registration.py). The reference's own blazer layer
(`school-blazer`, registered the same way) is drawn in yellow, so where the two lines part is where the shapes differ. Writes out/risa_adult/blazer-outline-full.png and blazer-outline-upper.png.
"""

import json
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, "harness/risa_adult")
from registration import Registration  # noqa: E402

meta = json.load(open("out/franzi/al-meta.json"))
H_REF, CX_REF, CHIN_REF = 352.0, 668.2, 434.0
scale = H_REF / (2 * meta["head_r"])
over = {"outfit": {"tunic_color": "#f4ecec", "collar_cut": "shirt", "sleeve_long": True, "tunic_tucked": True, "skirt_color": "#697897", "skirt_cut": "pleated", "ribbon_color": "#5784ae", "coat_color": "#ff00ff", "coat_cut": "blazer", "coat_button_color": "#ba975e"}}
subprocess.run(["node", "harness/risa_adult/risa.ts", "out/risa_adult/blazermark.svg", json.dumps(over)], check=True, stderr=subprocess.DEVNULL)
subprocess.run([sys.executable, "harness/svg2png.py", "out/risa_adult/blazermark.svg", "out/risa_adult/blazermark.png", "--scale", f"{scale:.5f}"], check=True, stdout=subprocess.DEVNULL)
a = np.array(Image.open("out/risa_adult/blazermark.png").convert("RGB")).astype(int)
mark = (a[..., 0] > 200) & (a[..., 1] < 60) & (a[..., 2] > 200)
ox = round((meta["canvas_w"] / 2) * scale - CX_REF)
oy = round(meta["chin_y"] * scale - CHIN_REF)
H, W = 1504, 1312
ours = np.zeros((H, W), bool)
ys, xs = np.nonzero(mark)
ys, xs = ys - oy, xs - ox
ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
ours[ys[ok], xs[ok]] = True
ours = ndimage.binary_fill_holes(ndimage.binary_closing(ours, iterations=2))  # the ink lines inside it (the lapel's, the pockets', the buttons') are not edges of it
R = Registration("ref/risa-adult/01-school-uniform.png")
ref_img = np.array(R.register(Image.open("ref/risa-adult/01-school-uniform.png").convert("RGB")))
ref_m = np.array(R.register(Image.open("ref/risa-adult/segments/01-school-uniform/school-blazer.png").convert("RGBA"), Image.BILINEAR))[..., 3] > 200


def edge(m, k=1):
    return ndimage.binary_dilation(m & ~ndimage.binary_erosion(m), iterations=k)


out = ref_img.copy()
out[edge(ref_m)] = (255, 220, 0)
out[edge(ours)] = (0, 255, 255)
im = Image.fromarray(out)
im.crop((340, 420, 1010, 1130)).save("out/risa_adult/blazer-outline-full.png")
up = im.crop((420, 430, 940, 800))
up.resize((up.width * 3, up.height * 3), Image.LANCZOS).save("out/risa_adult/blazer-outline-upper.png")
print("row   ours left..right        reference left..right    (outer edges of the whole blazer, sleeves included)")
for y in (560, 620, 700, 780, 860, 940, 1020, 1060):
    o = np.nonzero(ours[y])[0]
    r = np.nonzero(ref_m[y])[0]
    print(f"{y:4d}  {o.min():4d}..{o.max():4d} (w {o.max() - o.min() + 1:3d})   {r.min():4d}..{r.max():4d} (w {r.max() - r.min() + 1:3d})")
inter = (ours & ref_m).sum()
print("ours px", int(ours.sum()), "ref px", int(ref_m.sum()), "IoU", round(inter / (ours | ref_m).sum(), 3))
print("ours bbox", [int(v) for v in (np.nonzero(ours)[1].min(), np.nonzero(ours)[1].max(), np.nonzero(ours)[0].min(), np.nonzero(ours)[0].max())], "ref bbox", [int(v) for v in (np.nonzero(ref_m)[1].min(), np.nonzero(ref_m)[1].max(), np.nonzero(ref_m)[0].min(), np.nonzero(ref_m)[0].max())])
