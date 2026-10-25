"""Risa's eye from ref/risa-adult/00-bikini.png (docs/risa-polish-plan.md, stage 7), in the adult eye model's frame: reference pixels about the iris centre, x outward (away from the nose),
y down, at the head's calibration (175.7 px a head radius, as Franzi's eye in body-adult-eyes.ts).

    ./harness/run.sh harness/risa_adult/eye_trace.py      # then: node harness/risa_adult/eye_data.ts

Her face is drawn straight and symmetric (body-adult-cut-level.ts), but the reference's head is tilted (the eye line slopes 6.3 degrees) and a little turned, so its two eyes differ. Each eye is
levelled (turned about its iris centre by the tilt), the viewer's left one mirrored into the frame of the right, and the two are averaged, as masks sampled on a 0.25 px grid: one frontal eye.

From the `green-eyes-1` layer (the whole eye: the lid, the white and the iris) and the colours under it:
    silhouette   the layer
    lid          its dark pixels (luminance under 85), the component along the top, with the wing and the lashes beside it that run outside the layer
    aperture     the silhouette less the lid
    iris         green or yellow-green pixels: its centre, half width at the centre row and drop to its lowest pixel; its tones along the centre line (a dark top band, the colour, a light crescent)
    pupil        the darkest pixels inside the iris
    highlights   the near-white blobs inside the iris, in IMAGE orientation about the iris centre (the light comes from the viewer's upper left for both eyes, so they are not mirrored)
Writes out/risa_adult/eye.json and out/risa_adult/eye-check.png (each eye's masks, the mean outlines over both, 6x).
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

OUT = Path("out/risa_adult")
REF = "ref/risa-adult/00-bikini.png"
IRISES = {-1: (617.3, 319.9), 1: (727.1, 307.8)}  # viewer's left, right (docs/risa-adult-plan.md)
TILT = math.atan2(IRISES[1][1] - IRISES[-1][1], IRISES[1][0] - IRISES[-1][0])  # the eye line's slope, about -6.3 degrees
STEP = 0.25
U = np.arange(-62, 62 + 1e-9, STEP)  # frame x, outward
V = np.arange(-46, 40 + 1e-9, STEP)  # frame y, down

img = np.array(Image.open(REF).convert("RGB")).astype(float)
L = img @ np.array([0.299, 0.587, 0.114])
r, g, b = img[..., 0], img[..., 1], img[..., 2]
layer = np.array(Image.open("ref/risa-adult/segments/00-bikini/green-eyes/green-eyes-1.png"))[..., 3] > 127
greenish = (g > r + 6) & (g > b + 6)
# the lid's ink is brown-black; the iris's dark top band is dark green, and must not count
dark = (L < 85) & ~(g > r + 2)
white = (L > 205) & ((img.max(2) - img.min(2)) < 40)


def sample(field, side):
    """`field` (an image-sized array) on the eye frame of `side`: levelled about the iris centre, x outward."""
    cx, cy = IRISES[side]
    uu, vv = np.meshgrid(U, V)
    ix = side * uu  # outward is image-right for the right eye, image-left for the left
    c, s = math.cos(TILT), math.sin(TILT)
    x = cx + ix * c - vv * s
    y = cy + ix * s + vv * c
    return ndimage.map_coordinates(field.astype(float), [y, x], order=1, mode="constant")


def frame_mask(field, side):
    return sample(field, side) > 0.5


per = {}
for side in (-1, 1):
    sil = frame_mask(layer, side)
    near = ndimage.binary_dilation(sil, iterations=int(8 / STEP))
    d = frame_mask(dark, side) & near
    # the lid: the dark component that touches the silhouette's top
    lab, n = ndimage.label(d)
    top_rows = np.zeros_like(sil)
    rows = np.nonzero(sil.any(1))[0]
    top_rows[rows.min() : rows.min() + int(6 / STEP)] = True
    keep = {k for k in np.unique(lab[top_rows & d]) if k}
    lid = np.isin(lab, list(keep))
    iris = frame_mask(greenish, side) & sil
    lab, n = ndimage.label(iris)
    if n:
        iris = lab == (1 + int(np.argmax(ndimage.sum(iris, lab, range(1, n + 1)))))
    iris = ndimage.binary_fill_holes(iris)
    # the pupil is near-black and lies inside the iris: whatever of the "lid" lies in the iris's filled region below its top band is the pupil, not the lid
    lid &= ~(ndimage.binary_dilation(iris, iterations=2) & (V[:, None] > -10))
    lab, n = ndimage.label(lid)
    keep = {k for k in np.unique(lab[top_rows & lid]) if k}
    lid = np.isin(lab, list(keep))
    per[side] = {"sil": sil, "lid": lid, "iris": iris, "L": sample(L, side), "white": frame_mask(white, side) & sil}

mean = {k: (per[-1][k].astype(float) + per[1][k].astype(float)) / 2 for k in ("sil", "lid", "iris")}
sil = ndimage.binary_fill_holes(mean["sil"] > 0.5)
lid = (mean["lid"] > 0.5) & ndimage.binary_dilation(sil, iterations=int(10 / STEP))
lab, n = ndimage.label(lid)
lid = lab == (1 + int(np.argmax(ndimage.sum(lid, lab, range(1, n + 1)))))
aperture = ndimage.binary_opening(sil & ~lid, iterations=2)
lab, n = ndimage.label(aperture)
aperture = ndimage.binary_fill_holes(lab == (1 + int(np.argmax(ndimage.sum(aperture, lab, range(1, n + 1))))))
iris = mean["iris"] > 0.5


def to_frame(rc):
    """mask (row, col) to frame (x, y)"""
    return (float(U[0] + rc[1] * STEP), float(V[0] + rc[0] * STEP))


def outline(mask, tol=0.6, every=4):
    pts = [to_frame((rr, cc)) for cc, rr in tl.boundary(mask)]
    pts = pts[::every]
    # a light smoothing along the outline (3 px), then keep it as a closed polygon
    a = np.array(pts)
    k = 5
    sm = np.array([a[(np.arange(len(a)) + j) % len(a)] for j in range(-k, k + 1)]).mean(0)
    return [[round(float(x), 2), round(float(y), 2)] for x, y in sm]


ys, xs = np.nonzero(iris)
ix = U[0] + xs * STEP
iy = V[0] + ys * STEP
centre_row = np.abs(iy) < 1.0
iris_info = {
    "c": [round(float(np.median(ix)), 2), 0.0],
    "rx": round(float((ix[centre_row].max() - ix[centre_row].min()) / 2), 2),
    "ry": round(float(iy.max()), 2),
}
# the iris's tones down its centre line (both eyes' luminance, levelled and averaged): where the dark top band ends and where the light crescent begins
col = np.abs(U - iris_info["c"][0]) < 3
prof = ((per[-1]["L"] + per[1]["L"]) / 2)[:, col].mean(1)
inside = (V > -iris_info["ry"]) & (V < iris_info["ry"]) & iris[:, col].any(1)
vin, pin = V[inside], prof[inside]
mid = np.median(pin)
lightFrom = float(vin[np.argmax((pin > mid * 1.25) & (vin > 2))]) if ((pin > mid * 1.25) & (vin > 2)).any() else None
pupil = (per[-1]["L"] + per[1]["L"]) / 2 < 40
pupil &= iris & (np.abs(V)[:, None] < 14) & (np.abs(U - iris_info["c"][0])[None, :] < 10)
py, px = np.nonzero(pupil)
pupil_info = {"c": [round(float(U[0] + px.mean() * STEP), 2), round(float(V[0] + py.mean() * STEP), 2)], "rx": round(float((px.max() - px.min()) * STEP / 2), 2), "ry": round(float((py.max() - py.min()) * STEP / 2), 2)}


def iris_tones():
    """The iris's three tones, as shifts from its middle band (hue in turns, saturation and value as factors), both eyes' pixels pooled: the top band (above -5, under the lid's shadow), the
    middle (to the crescent) and the light crescent (below `lightFrom`), the highlights and the pupil left out."""
    import colorsys
    bands = {"top": [], "mid": [], "low": []}
    for side in (-1, 1):
        rgb = np.stack([sample(img[..., k], side) for k in range(3)], -1)
        m = per[side]["iris"] & ~per[side]["white"] & (per[side]["L"] > 45)
        for name, sel in (("top", V < -5), ("mid", (V >= -2) & (V < (lightFrom or 7))), ("low", V >= (lightFrom or 7) + 2)):
            bands[name].append(rgb[m & sel[:, None]])
    hsv = {k: colorsys.rgb_to_hsv(*(np.concatenate(v).mean(0) / 255)) for k, v in bands.items()}
    mid = hsv["mid"]
    rel = lambda t: {"dh": round(t[0] - mid[0], 4), "s": round(t[1] / mid[1], 3), "v": round(t[2] / mid[2], 3)}
    return {"mid_rgb": [round(c * 255) for c in colorsys.hsv_to_rgb(*mid)], "top": rel(hsv["top"]), "low": rel(hsv["low"])}


def highlights():
    """near-white blobs inside each iris, in image orientation about its centre (x to the image's right), the two eyes averaged blob by blob (largest first)"""
    out = {}
    for side in (-1, 1):
        cx, cy = IRISES[side]
        box = (slice(int(cy - 30), int(cy + 30)), slice(int(cx - 30), int(cx + 30)))
        # near-white and unsaturated (the iris's light crescent is bright but yellow), in the iris's upper part
        m = white[box] & (np.hypot(np.arange(60)[None, :] - 30, (np.arange(60)[:, None] - 30) * 0.85) < 16) & (np.arange(60)[:, None] < 33)
        lab, n = ndimage.label(m)
        blobs = []
        for k in range(1, n + 1):
            yy, xx = np.nonzero(lab == k)
            if len(xx) >= 6:
                blobs.append((len(xx), float(xx.mean() - 30), float(yy.mean() - 30), float((xx.max() - xx.min() + 1) / 2), float((yy.max() - yy.min() + 1) / 2)))
        out[side] = sorted(blobs, reverse=True)[:2]
    res = []
    for a, b in zip(out[-1], out[1]):
        res.append({"c": [round((a[1] + b[1]) / 2, 2), round((a[2] + b[2]) / 2, 2)], "rx": round((a[3] + b[3]) / 2, 2), "ry": round((a[4] + b[4]) / 2, 2)})
    return res


data = {
    "silhouette": outline(sil),
    "lid": outline(lid),
    "aperture": outline(aperture),
    "iris": iris_info,
    "iris_light_from": None if lightFrom is None else round(lightFrom, 2),
    "pupil": pupil_info,
    "highlights": highlights(),
    "tones": iris_tones(),
}
json.dump(data, open(OUT / "eye.json", "w"), indent=1)
print(json.dumps({k: (v if not isinstance(v, list) or k == "highlights" else f"{len(v)} points") for k, v in data.items()}, indent=1))

# check: each eye's frame image with the mean outlines over it, 6x
Z = 6
tiles = []
for side in (-1, 1):
    rgb = np.stack([sample(img[..., k], side) for k in range(3)], -1).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(rgb).resize((rgb.shape[1] * Z // 4, rgb.shape[0] * Z // 4), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    f = lambda q: ((q[0] - U[0]) / STEP * Z / 4, (q[1] - V[0]) / STEP * Z / 4)
    for key, colr in (("lid", (255, 0, 255)), ("aperture", (0, 255, 255))):
        pts = [f(q) for q in data[key]]
        d.line(pts + [pts[0]], fill=colr, width=2)
    c = f(iris_info["c"])
    d.ellipse([c[0] - iris_info["rx"] * Z, c[1] - iris_info["ry"] * Z, c[0] + iris_info["rx"] * Z, c[1] + iris_info["ry"] * Z], outline=(255, 255, 0), width=2)
    if lightFrom is not None:
        d.line([(c[0] - iris_info["rx"] * Z, f((0, lightFrom))[1]), (c[0] + iris_info["rx"] * Z, f((0, lightFrom))[1])], fill=(255, 128, 0), width=2)
    for hl in data["highlights"]:
        hx = side * hl["c"][0] + iris_info["c"][0]  # image orientation back to this eye's frame
        q = f((hx, hl["c"][1]))
        d.ellipse([q[0] - hl["rx"] * Z, q[1] - hl["ry"] * Z, q[0] + hl["rx"] * Z, q[1] + hl["ry"] * Z], outline=(0, 255, 0), width=2)
    tiles.append(im)
st = Image.new("RGB", (tiles[0].width * 2 + 16, tiles[0].height), "white")
st.paste(tiles[0], (0, 0)); st.paste(tiles[1], (tiles[0].width + 16, 0))
st.save(OUT / "eye-check.png")
