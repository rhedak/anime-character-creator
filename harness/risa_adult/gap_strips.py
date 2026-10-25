"""The gap analysis's strips (docs/risa-polish-plan.md): the reference beside our render on the bikini's grid (compare_head.py's mapping: a head height of 352 px, the centre
line at 668.2, the chin at 434), with guide lines every half head height.

    ./harness/run.sh harness/risa_adult/gap_strips.py

Renders Risa in the bikini (risa.ts) and the preset in the uniform, and writes out/gap/: bikini_full, uniform_full and noblazer_full (reference, ours, a 50% blend), the outlines of
ours over the reference, the heads at 1.2x and the torso. Then prints the figure's width without the hair, row by row, against 00 and 02.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "harness/risa_adult")
from registration import Registration  # noqa: E402

Path("out/gap").mkdir(parents=True, exist_ok=True)
Path("out/franzi").mkdir(parents=True, exist_ok=True)
subprocess.run(["node", "harness/franzi/underwear.ts", "adult_female", "out/franzi/al-meta.svg"], check=True, stderr=subprocess.DEVNULL)
subprocess.run(["node", "harness/risa_adult/risa.ts", "out/gap/risa_bikini.svg"], check=True, stderr=subprocess.DEVNULL)
subprocess.run(["node", "ts/bin/render.ts", "--out", "out/gap/risa_uniform", "--preset", "risa"], check=True, stdout=subprocess.DEVNULL)

meta = json.load(open("out/franzi/al-meta.json"))
H, CX, CHIN = 352.0, 668.2, 434.0
scale = H / (2 * meta["head_r"])
W, HT = 1312, 2200


def ours(svg):
    png = svg[:-4] + ".png"
    subprocess.run([sys.executable, "harness/svg2png.py", svg, png, "--scale", f"{scale:.5f}"], check=True, stdout=subprocess.DEVNULL)
    im = Image.open(png).convert("RGBA")
    ox = round((meta["canvas_w"] / 2) * scale - CX)
    oy = round(meta["chin_y"] * scale - CHIN)
    canvas = Image.new("RGBA", (W, HT), (0, 0, 0, 0))
    canvas.alpha_composite(im, (-ox, -oy)) if ox <= 0 and oy <= 0 else canvas.paste(im.crop((ox, oy, ox + W, oy + HT)), (0, 0))
    return canvas


def on(bg, im):
    b = Image.new("RGBA", im.size, bg)
    b.alpha_composite(im)
    return b.convert("RGB")


def ref(name, registered=True):
    im = Image.open(f"ref/risa-adult/{name}-transparent.png").convert("RGBA")
    if not registered:
        c = Image.new("RGBA", (W, HT), (0, 0, 0, 0))
        c.paste(im, (0, 0))
        return c
    return Registration(f"ref/risa-adult/{name}.png").register(im, size=(W, HT))


def guides(im, y0, y1):
    d = ImageDraw.Draw(im)
    for k in range(0, 20):
        y = CHIN + (k - 2) * H / 2
        if y0 <= y <= y1:
            d.line([(0, y - y0), (im.width, y - y0)], fill=(0, 160, 255), width=1)
    d.line([(CX, 0), (CX, im.height)], fill=(0, 160, 255), width=1)
    return im


def strip(panels, box, out, zoom=0.5, bg="white"):
    x0, y0, x1, y1 = box
    crops = [guides(on(bg, p).crop(box), y0, y1) for p in panels]
    w, h = crops[0].size
    s = Image.new("RGB", (w * len(crops) + 10 * (len(crops) - 1), h), "white")
    for i, c in enumerate(crops):
        s.paste(c, (i * (w + 10), 0))
    s = s.resize((round(s.width * zoom), round(s.height * zoom)), Image.LANCZOS)
    s.save(out)


def blend(a, b, bg="white"):
    return Image.blend(on(bg, a), on(bg, b), 0.5).convert("RGBA")


def outline_over(base, other, color):
    """`other`'s alpha boundary drawn on `base` (RGB)."""
    m = np.array(other)[..., 3] > 127
    edge = m ^ np.roll(m, 1, 0) | m ^ np.roll(m, 1, 1)
    a = np.array(base.convert("RGB"))
    a[edge] = color
    return Image.fromarray(a).convert("RGBA")


bik_ref = ref("00-bikini", registered=False)
uni_ref = ref("01-school-uniform")
nob_ref = ref("02-uniform-no-blazer")
bik_ours = ours("out/gap/risa_bikini.svg")
uni_ours = ours("out/gap/risa_uniform.svg")

FULL = (230, 40, 1100, 2200)
strip([bik_ref, bik_ours, blend(bik_ref, bik_ours, "black")], (230, 40, 1100, 1504), "out/gap/bikini_full.png", 0.6, bg="black")
strip([uni_ref, uni_ours, blend(uni_ref, uni_ours)], FULL, "out/gap/uniform_full.png", 0.5)
strip([nob_ref, uni_ours], FULL, "out/gap/noblazer_full.png", 0.5)
strip([outline_over(on("white", uni_ref), uni_ours, (0, 200, 255))], FULL, "out/gap/uniform_outline.png", 0.6)
strip([outline_over(on("black", bik_ref), bik_ours, (0, 255, 255))], (230, 40, 1100, 1504), "out/gap/bikini_outline.png", 0.7, bg="black")
strip([uni_ref, uni_ours], (470, 120, 870, 470), "out/gap/head_uniform.png", 1.2)
strip([bik_ref, bik_ours], (470, 120, 870, 470), "out/gap/head_bikini.png", 1.2, bg="black")
strip([uni_ref, uni_ours], (360, 420, 980, 1120), "out/gap/torso_uniform.png", 0.8)

# per-row figure width (alpha), and the width without the hair, in px of this grid and in head heights
def widths(im, hair_mask=None):
    a = np.array(im)[..., 3] > 127
    if hair_mask is not None:
        a = a & ~hair_mask
    rows = {}
    for d in np.arange(0.5, 4.6, 0.25):
        y = int(round(CHIN + d * H))
        if y >= a.shape[0]:
            continue
        xs = np.nonzero(a[y])[0]
        rows[d] = (xs.max() - xs.min()) if len(xs) else 0
    return rows


def hair_of(name, registered):
    seg = "long-red-hair" if name in ("00-bikini", "02-uniform-no-blazer") else "red-hair"
    im = Image.open(f"ref/risa-adult/segments/{name}/{seg}.png").convert("RGBA")
    if registered:
        im = Registration(f"ref/risa-adult/{name}.png").register(im, size=(W, HT))
    else:
        c = Image.new("RGBA", (W, HT), (0, 0, 0, 0))
        c.paste(im, (0, 0))
        im = c
    return np.array(im)[..., 3] > 60


def our_hair(svg_params):
    subprocess.run(["node", *svg_params], check=True, stderr=subprocess.DEVNULL)


our_hair(["harness/risa_adult/risa.ts", "out/gap/hairmark.svg", json.dumps({"hair_color": "#00ff00"})])
hm = np.array(ours("out/gap/hairmark.svg").convert("RGB")).astype(int)
our_hair_mask = (np.abs(hm - np.array([0, 255, 0])).sum(2) < 120)

t_ref = widths(bik_ref, hair_of("00-bikini", False))
t_ours = widths(bik_ours, our_hair_mask)
t_uni = widths(nob_ref, hair_of("02-uniform-no-blazer", True))
print("rows below chin (head heights): width without hair, px on the bikini grid")
print(f"{'d':>5} {'bikini ref':>10} {'ours':>6} {'ours/ref':>8} {'02 ref':>7} {'ours/02':>8}")
for d in t_ours:
    r, o, u = t_ref.get(d, 0), t_ours[d], t_uni.get(d, 0)
    print(f"{d:5.2f} {r:10d} {o:6d} {o / r if r else 0:8.3f} {u:7d} {o / u if u else 0:8.3f}")
