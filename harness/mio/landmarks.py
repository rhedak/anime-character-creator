"""Mio's calibration and body landmarks, measured off `ref-local/mio/mio.png`
(`docs/mio-plan.md`, M2).

Every segment is a true pixel crop of the composite (`crops.py`), so each is
placed at its verified offset and its alpha is that garment's own extent. The
offsets are re-checked here on every run at a cost of a few pixels of search.

**Calibration.** Her head is not ours, which this script makes visible rather
than papering over. Measured in our own head radii, four independent features
give four different pixels-per-radius:

    ear tip to ear tip     299 px over our 1.76          about 170
    hair top to chin       352 px over our 2.19          about 161
    visible face width     226 px over our 1.60          about 141
    eye line to chin       108 px over our 0.84          about 128

The first two measure the skull and agree within 5%. The last two measure the
face, and a face in this style is a matter of eye size and cheek, which differ
from ours (her ears sit about 0.5 head radii above her chin, ours about 1.0:
a wide, short-faced head against our long one). So the head scale is taken from
the skull, **R = 165 px per head radius**, and the face is left to M9. The head
centre is placed by the chin (`CY = chin - 1.02 R`, our chin standing 1.02 head
radii below our centre), which also leaves the hair top within 10 px of hers.

The estimate is good to about 4% for garment work and no better. Every cut is
mapped landmark to landmark, which is what keeps it wearable if the calibration
is a little off, so no conclusion here rests on the third digit.

    ./harness/run.sh harness/mio/landmarks.py
"""

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

BASE = "ref-local/mio"
comp = Image.open(f"{BASE}/mio.png").convert("RGBA")
arr = np.asarray(comp).astype(int)
H, W = arr.shape[:2]
alpha = arr[:, :, 3:4] / 255.0
rgb = (arr[:, :, :3] * alpha + 255 * (1 - alpha)).astype(int)
opaque = arr[:, :, 3] > 128

# Offsets found by `crops.py` (x, y of the crop's top-left corner).
OFFSETS = {
    "anime-girl.png": (416, 47),
    "school-blazer.png": (440, 410),
    "white-collared-shirt.png": (447, 401),
    "pleated-skirt.png": (475, 836),
    "blue-ribbon.png": (593, 435),
    "brown-loafers/brown-loafers-1.png": (531, 1388),
    "brown-loafers/brown-loafers-2.png": (650, 1388),
    "long-black-hair.png": (417, 47),
    "bangs.png": (511, 101),
}


def place(name):
    ox, oy = OFFSETS[name]
    seg = np.asarray(Image.open(f"{BASE}/segments/{name}").convert("RGBA")).astype(int)
    sh, sw = seg.shape[:2]
    m = seg[:, :, 3] > 250
    d = np.abs(rgb[oy : oy + sh, ox : ox + sw] - seg[:, :, :3] * 1).sum(2)[m].mean() / 3
    full = np.zeros((H, W), bool)
    full[oy : oy + sh, ox : ox + sw] = seg[:, :, 3] > 128
    if d > 8:
        print(f"WARNING {name}: offset ({ox}, {oy}) no longer matches, difference {d:.2f}")
    return full


# --- calibration -------------------------------------------------------------
R = 165.0
# Our chin stands 1.02 head radii below our head centre (the skin's lowest row on
# the short-haired renders). Her chin is the face skin's lowest row.
skin_seed = rgb[350, 560]
skin = np.abs(rgb - skin_seed).sum(2) <= 30
skin[:150] = False
skin[560:] = False
lab, n = ndi.label(skin)
face = lab == (np.argmax(ndi.sum(skin, lab, range(1, n + 1))) + 1)
fy, fx = np.nonzero(face)
CHIN = int(fy.max())
CX = 630.0
CY = CHIN - 1.02 * R


def hy(y):
    return (y - CY) / R


def hx(x):
    return (x - CX) / R


print(
    f"skin sampled {tuple(skin_seed)}; face skin y {fy.min()} to {CHIN}, x {fx.min()} to {fx.max()}"
)
print(f"calibration: centre ({CX:.0f}, {CY:.1f}), R = {R:.0f} px per head radius")
ys_a = np.nonzero(opaque.any(1))[0]
print(f"hair top {hy(ys_a.min()):+.3f}, chin {hy(CHIN):+.3f}")

# --- the figure --------------------------------------------------------------
figure = place("anime-girl.png")
fig_ys = np.nonzero(figure.any(1))[0]
sole = fig_ys.max()
print(f"\nfigure: top {hy(fig_ys.min()):+.3f}, sole {hy(sole):+.3f} head radii")
# The convention `build_skeleton` and the tall chibi use: crown (head centre
# minus one radius) to sole, over the head's diameter.
heads = (hy(sole) + 1) / 2
print(f"  stands {heads:.3f} heads (crown to sole over a head diameter)")


def extent(mask, y):
    xs = np.nonzero(mask[y])[0]
    return (xs.min(), xs.max()) if len(xs) else None


def half_w(mask, y):
    e = extent(mask, y)
    return None if e is None else (e[1] - e[0]) / 2 / R


# --- the blazer: shoulder, torso and sleeve ----------------------------------
blazer = place("school-blazer.png")
b_ys = np.nonzero(blazer.any(1))[0]
print(f"\nblazer: top {hy(b_ys.min()):+.3f}, hem {hy(b_ys.max()):+.3f}")
print("  half-width of its extent, every 0.2 hr (an outer envelope: it includes the sleeve):")
for want in np.arange(0.9, 4.0, 0.2):
    y = int(round(CY + want * R))
    if y < b_ys.min() or y > b_ys.max():
        continue
    e = extent(blazer, y)
    if e:
        print(
            f"    y {want:+.2f}: x {hx(e[0]):+.3f} to {hx(e[1]):+.3f}  half {half_w(blazer, y):.3f}"
        )
# The torso alone, between the sleeves: the blazer's body is the run containing
# the centre line.
print("  the torso run (the part of the row holding the centre line), every 0.4 hr:")
for want in np.arange(1.2, 3.7, 0.4):
    y = int(round(CY + want * R))
    row = blazer[y]
    if not row[int(CX)]:
        continue
    rl, _ = ndi.label(row)
    run = np.nonzero(rl == rl[int(CX)])[0]
    print(
        f"    y {want:+.2f}: x {hx(run.min()):+.3f} to {hx(run.max()):+.3f}  half {(run.max() - run.min()) / 2 / R:.3f}"
    )

# --- the skirt ----------------------------------------------------------------
skirt = place("pleated-skirt.png")
s_ys = np.nonzero(skirt.any(1))[0]
print(f"\nskirt (the visible part): top {hy(s_ys.min()):+.3f}, hem {hy(s_ys.max()):+.3f}")
for want in np.arange(2.7, 4.2, 0.15):
    y = int(round(CY + want * R))
    if skirt[y].any():
        e = extent(skirt, y)
        print(
            f"    y {want:+.2f}: x {hx(e[0]):+.3f} to {hx(e[1]):+.3f}  half {half_w(skirt, y):.3f}"
        )
n_pleats = None

# --- the legs, socks and shoes -----------------------------------------------
sock_seed = rgb[1300, 580]
print(f"\nsock colour sampled {tuple(sock_seed)} at (580, 1300)")
sock = (np.abs(rgb - sock_seed).sum(2) <= 40) & figure
sock[: int(CY + 4.5 * R)] = False
sock[sole - 80 :] = False
sl, sn = ndi.label(sock)
big = [i for i in range(1, sn + 1) if (sl == i).sum() > 300]
print(f"  sock components: {len(big)}")
for i in big:
    m = sl == i
    ys, xs = np.nonzero(m)
    print(
        f"    y {hy(ys.min()):+.3f} to {hy(ys.max()):+.3f}  x {hx(xs.min()):+.3f} to {hx(xs.max()):+.3f}"
    )
sock_top = min(np.nonzero(sl == i)[0].min() for i in big) if big else None
if sock_top is not None:
    print(f"  sock top: y {hy(sock_top):+.3f}")
    for want in (hy(sock_top) + 0.05, 5.0, 5.4, 5.8):
        y = int(round(CY + want * R))
        row = sock[y]
        if row.any():
            rl, rn = ndi.label(row)
            for j in range(1, rn + 1):
                xs = np.nonzero(rl == j)[0]
                if len(xs) > 5:
                    print(
                        f"    y {want:+.2f}: sock x {hx(xs.min()):+.3f} to {hx(xs.max()):+.3f}  half {(xs.max() - xs.min()) / 2 / R:.3f}"
                    )

# Bare leg skin between the skirt hem and the sock top.
leg = (np.abs(rgb - skin_seed).sum(2) <= 30) & figure
leg[: int(CY + 3.5 * R)] = False
leg[sock_top if sock_top else sole :] = False
print("\nbare leg skin (each leg a separate run), every 0.25 hr:")
for want in np.arange(3.6, hy(sock_top) if sock_top else 5.0, 0.25):
    y = int(round(CY + want * R))
    row = leg[y]
    rl, rn = ndi.label(row)
    runs = [np.nonzero(rl == j)[0] for j in range(1, rn + 1)]
    runs = [r for r in runs if len(r) > 8]
    if runs:
        print(
            f"    y {want:+.2f}: "
            + "  ".join(
                f"x {hx(r.min()):+.3f} to {hx(r.max()):+.3f} (half {(r.max() - r.min()) / 2 / R:.3f})"
                for r in runs
            )
        )

for name in ("brown-loafers/brown-loafers-1.png", "brown-loafers/brown-loafers-2.png"):
    m = place(name)
    ys, xs = np.nonzero(m)
    print(
        f"\n{name}: y {hy(ys.min()):+.3f} to {hy(ys.max()):+.3f}  x {hx(xs.min()):+.3f} to {hx(xs.max()):+.3f}  (width {(xs.max() - xs.min()) / R:.3f})"
    )

# --- the arms ------------------------------------------------------------------
# The sleeve's outer edge below the shoulder is the blazer's own extent. The hand
# and the wrist: the lowest rows of the blazer's sleeves and the cuff pieces in
# the shirt layer.
shirt = place("white-collared-shirt.png")
sh_ys = np.nonzero(shirt.any(1))[0]
print(
    f"\nshirt layer: top {hy(sh_ys.min()):+.3f}, bottom {hy(sh_ys.max()):+.3f} (the cuffs at the wrists)"
)
cl, cn = ndi.label(shirt)
for i in range(1, cn + 1):
    m = cl == i
    if m.sum() < 80:
        continue
    ys, xs = np.nonzero(m)
    print(
        f"    part {i}: {m.sum():5d}px  y {hy(ys.min()):+.3f} to {hy(ys.max()):+.3f}  x {hx(xs.min()):+.3f} to {hx(xs.max()):+.3f}"
    )

# --- the neck and the collar, for the throat -----------------------------------
ribbon = place("blue-ribbon.png")
r_ys, r_xs = np.nonzero(ribbon)
print(
    f"\nribbon: y {hy(r_ys.min()):+.3f} to {hy(r_ys.max()):+.3f}  x {hx(r_xs.min()):+.3f} to {hx(r_xs.max()):+.3f}"
)
