"""Risa's body widths, reference 00 against ours in the bikini, on the bikini's grid (docs/risa-polish-plan.md). The body is the skin and underwear pixels, not the hair or the ink.

    ./harness/run.sh harness/risa_adult/gap_widths.py      # after gap_strips.py, which renders the two SVGs

Prints, per row (head heights below the chin), the outer extent, the run through the centre line (the torso, or a leg below the crotch) and each arm's run, then the uniform's
vertical landmarks (the skirt, the socks, the figure) from 02 registered against ours. The runs split where a line or the bikini's edge crosses the body (the last column says
how many), so only rows with three runs are a clean torso and two arms; the socks' colour also matches hair pixels, so their top is not a reading.
"""

import json
import subprocess
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, "harness/risa_adult")
from registration import Registration  # noqa: E402

meta = json.load(open("out/franzi/al-meta.json"))
H, CX, CHIN = 352.0, 668.2, 434.0
scale = H / (2 * meta["head_r"])
W, HT = 1312, 2300


def ours(svg):
    png = svg[:-4] + ".png"
    subprocess.run([sys.executable, "harness/svg2png.py", svg, png, "--scale", f"{scale:.5f}"], check=True, stdout=subprocess.DEVNULL)
    im = Image.open(png).convert("RGBA")
    ox = round((meta["canvas_w"] / 2) * scale - CX)
    oy = round(meta["chin_y"] * scale - CHIN)
    return np.array(im.crop((ox, oy, ox + W, oy + HT)))


def near(a, hexes, tol):
    m = np.zeros(a.shape[:2], bool)
    for h in hexes:
        c = np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)])
        m |= np.abs(a[..., :3].astype(int) - c).sum(2) < tol
    return m & (a[..., 3] > 127)


o = ours("out/gap/risa_bikini.svg")
ours_body = near(o, ["#fac4a8", "#f5ebea"], 40)

r = np.array(Image.open("ref/risa-adult/00-bikini-transparent.png").convert("RGBA"))
hair = np.array(Image.open("ref/risa-adult/segments/00-bikini/long-red-hair.png").convert("RGBA"))[..., 3] > 60
rgb = r[..., :3].astype(int)
# skin and the white bikini: bright, not red-dominant hair
ref_body = (r[..., 3] > 127) & ~hair & (rgb.sum(2) > 330) & ((rgb[..., 0] - rgb[..., 1]) < 90)
ref_body = np.pad(ref_body, ((0, HT - ref_body.shape[0]), (0, W - ref_body.shape[1])))


def runs(row, minlen=6):
    xs = np.flatnonzero(np.diff(np.r_[0, row.astype(int), 0]))
    return [(a, b) for a, b in zip(xs[::2], xs[1::2]) if b - a >= minlen]


def describe(m, y):
    rs = runs(m[y])
    if not rs:
        return None
    torso = min(rs, key=lambda t: 0 if t[0] <= CX < t[1] else min(abs(t[0] - CX), abs(t[1] - CX)))
    left = [t for t in rs if t[1] <= torso[0]]
    right = [t for t in rs if t[0] >= torso[1]]
    return dict(outer=rs[-1][1] - rs[0][0], torso=torso[1] - torso[0], armL=(left[0][1] - left[0][0]) if left else 0, armR=(right[-1][1] - right[-1][0]) if right else 0, n=len(rs))


print(f"{'d':>5} | {'outer':>11} | {'torso/legs run':>15} | {'arm L':>9} | {'arm R':>9} | runs")
for d in np.arange(0.4, 3.01, 0.1):
    y = int(round(CHIN + d * H))
    a, b = describe(ref_body, y), describe(ours_body, y)
    if a is None or b is None:
        continue
    print(f"{d:5.2f} | {a['outer']:4d} {b['outer']:4d} {b['outer'] / a['outer']:4.2f}x | {a['torso']:4d} {b['torso']:4d} {b['torso'] / a['torso']:5.2f}x | {a['armL']:3d} {b['armL']:3d}  | {a['armR']:3d} {b['armR']:3d}  | {a['n']} {b['n']}")

# narrowest torso between the bust and the briefs, and widest hips
def extreme(m, d0, d1, fn):
    vals = []
    for y in range(int(CHIN + d0 * H), int(CHIN + d1 * H)):
        t = describe(m, y)
        if t and t["n"] >= 3:
            vals.append((t["torso"], (y - CHIN) / H))
    return fn(vals) if vals else None


for name, m in (("ref", ref_body), ("ours", ours_body)):
    print(name, "waist (min torso, d 1.1-1.8):", extreme(m, 1.1, 1.8, min), " hips (max torso, d 1.8-2.3):", extreme(m, 1.8, 2.3, max))

# vertical landmarks in the uniform: 02 registered vs ours
u = Registration("ref/risa-adult/02-uniform-no-blazer.png")
segs = "ref/risa-adult/segments/02-uniform-no-blazer"


def reg_alpha(p):
    im = u.register(Image.open(p).convert("RGBA"), size=(W, HT))
    return np.array(im)[..., 3] > 127


def rows_of(m):
    ys = np.flatnonzero(m.any(1))
    return (ys.min(), ys.max()) if len(ys) else (None, None)


skirt = reg_alpha(f"{segs}/blue-pleated-skirt.png")
socks = reg_alpha(f"{segs}/black-knee-high-socks/black-knee-high-socks-1.png") | reg_alpha(f"{segs}/black-knee-high-socks/black-knee-high-socks-2.png")
fig = reg_alpha("ref/risa-adult/02-uniform-no-blazer-transparent.png")
uo = ours("out/gap/risa_uniform.svg")
o_skirt = near(uo, ["#697897"], 30)
o_sock = near(uo, ["#2a292c"], 30)
o_fig = uo[..., 3] > 127
for label, (a, b) in (("skirt", (rows_of(skirt), rows_of(o_skirt))), ("socks", (rows_of(socks), rows_of(o_sock))), ("figure", (rows_of(fig), rows_of(o_fig)))):
    f = lambda v: f"{(v - CHIN) / H:5.2f}" if v is not None else "  -  "
    print(f"{label:7s} ref top {f(a[0])} bottom {f(a[1])}   ours top {f(b[0])} bottom {f(b[1])}  (head heights below chin)")
