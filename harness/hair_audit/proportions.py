"""Hair-trace audit, test 1: is the body under the hair the same body?

Measures, row by row in head radii from the head centre, the hair's outer
half-width and the body's half-width on four sources, each on the calibration
the harness already established for it:

- `katherina_grok_real` (the realistic reference D5 traced): the hair is the
  pixel-exact `purple-hair` segment, the body the `dark-blue-dress` and
  `yellow-collar` segments; D0's calibration, (636, 290) and 88.7 px per head
  radius.
- the hair-only reference (`ref-local/katherina_hair/`): `register.py`'s
  scale and offset into `katherina_grok_real`'s pixels, then the same
  calibration. Its body is the hole cut in `hair_with_human_shape.png`, read
  per row as the run of no hair around the centre line, so where hair does
  not touch the body it is an upper bound.
- `katherina_grok` (the tall-chibi design reference `tall_chibi` was measured
  off): the witch hat's calibration, (650, 481) and 173.7 px per head radius.
  Hair is classified by colour (purple: R >= 45, R - G >= 14, B >= 65,
  B > 1.1 R, which leaves skin out), the body as every other lit pixel below
  the chin; both read on the viewer's right, away from the staff.
- ours: Katherina as the preset draws her (height 1.0) and at 1.3, the body
  rendered with the hair stood out, the hair as `long_traced`'s mass.

Prints a table at fixed heights and writes `out/hair_audit/proportions.png`:
half-width against height for each source, hair solid and body dashed.

    ./harness/run.sh harness/hair_audit/proportions.py
"""

import io
import json
import os
from dataclasses import replace

import cairosvg
import numpy as np
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/hair_audit"
REAL = "ref-local/katherina_grok_real"
SEG = {
    "purple-hair": (435, 200),
    "dark-blue-dress": (404, 417),
    "yellow-collar": (580, 403),
}
REAL_CAL = (636.0, 290.0, 88.7)
CHIBI = "ref-local/katherina_grok/katherina_grok.jpg"
CHIBI_CAL = (650.0, 481.0, 173.7)
HAIR_DIR = "ref-local/katherina_hair"
REG = "out/hair_only/register.json"
ROWS = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.4]


def seg_mask(name, shape):
    s = np.asarray(Image.open(f"{REAL}/segments/{name}.png").convert("RGBA"))[..., 3] > 128
    m = np.zeros(shape, bool)
    x, y = SEG[name]
    h, w = min(s.shape[0], shape[0] - y), min(s.shape[1], shape[1] - x)
    m[y : y + h, x : x + w] = s[:h, :w]
    return m


def extent(mask, cx):
    """Per row: (left, right) distance in pixels from `cx` to the outermost set
    pixel on each side, NaN where the side is empty."""
    h, w = mask.shape
    xs = np.arange(w)
    left = np.full(h, np.nan)
    right = np.full(h, np.nan)
    for y in range(h):
        row = mask[y]
        lx = xs[row & (xs < cx)]
        rx = xs[row & (xs >= cx)]
        if lx.size:
            left[y] = cx - lx.min()
        if rx.size:
            right[y] = rx.max() - cx
    return left, right


def hole(mask, cx):
    """Per row: half-width of the run of unset pixels around `cx` (the body
    cut out of the hair), NaN where the run reaches the image edge on a side
    (no hair to bound it)."""
    h, w = mask.shape
    out = np.full(h, np.nan)
    c0 = int(round(cx))
    for y in range(h):
        row = mask[y]
        if row[c0]:
            continue
        lx = np.nonzero(row[:c0])[0]
        rx = np.nonzero(row[c0:])[0]
        if lx.size and rx.size:
            out[y] = ((c0 - lx.max()) + rx.min()) / 2
    return out


def to_r(pix_rows, vals, cal):
    """Rows and pixel widths to head radii on calibration `cal`."""
    ox, oy, s = cal
    return (pix_rows - oy) / s, vals / s


def at(ys, vs, y):
    ok = ~np.isnan(vs)
    if not ok.any():
        return np.nan
    i = np.argmin(np.abs(ys - y) + np.where(ok, 0, 1e9))
    return vs[i] if abs(ys[i] - y) < 0.05 else np.nan


def real_ref():
    im = Image.open(f"{REAL}/katherina_grok_real.png")
    shape = (im.height, im.width)
    hair = seg_mask("purple-hair", shape)
    body = seg_mask("dark-blue-dress", shape) | seg_mask("yellow-collar", shape)
    ox, oy, s = REAL_CAL
    hl, hr = extent(hair, ox)
    bl, br = extent(body, ox)
    rows = np.arange(shape[0])
    ys, hw = to_r(rows, hl, REAL_CAL)
    _, bw = to_r(rows, br, REAL_CAL)
    # The bat sits on the viewer's right shoulder and the staff arm on the
    # left, so the hair is read on the left and the body on the right.
    _, hwl = to_r(rows, hl, REAL_CAL)
    _, bwl = to_r(rows, bl, REAL_CAL)
    return ys, {"hair": hw, "hair_left": hwl, "body": bw, "body_left": bwl}


def hair_only_ref():
    reg = json.load(open(REG))
    sc, (dx, dy) = reg["scale"], reg["offset"]
    full = np.asarray(Image.open(f"{HAIR_DIR}/hair_only.png").convert("RGBA"))[..., 3] > 128
    front = np.asarray(Image.open(f"{HAIR_DIR}/hair_with_human_shape.png").convert("RGBA"))[..., 3] > 128
    ox, oy, s = REAL_CAL
    # The head centre in the hair-only image's own pixels.
    hcx = (ox - dx) / sc
    rows = np.arange(full.shape[0])
    fl, fr = extent(full, hcx)
    body = hole(front, hcx)
    # Hair-only pixels -> grok_real pixels -> head radii.
    yr = ((rows * sc + dy) - oy) / s
    k = sc / s
    return yr, {"hair": np.fmax(fl, fr) * k, "body": body * k, "front_present": front.any(axis=1)}


def chibi_ref():
    im = np.asarray(Image.open(CHIBI).convert("RGB")).astype(int)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    purple = (r >= 45) & (r - g >= 14) & (b >= 65) & (b > r * 1.1)
    lit = im.sum(2) > 60
    ox, oy, s = CHIBI_CAL
    rows = np.arange(im.shape[0])
    ys = (rows - oy) / s
    # Body: lit, not hair, below the chin; the staff and the hand that holds
    # it are left of x = 420 px, so they are cut off.
    body = lit & ~purple & (ys[:, None] > 1.0)
    body[:, :430] = False
    hl, hr = extent(purple, ox)
    bl, br = extent(body, ox)
    Image.fromarray((np.dstack([purple, body, np.zeros_like(body)]) * 255).astype(np.uint8)).save(
        f"{OUT}/chibi_masks.png"
    )
    return ys, {"hair": hr / s, "body": br / s, "hair_left": hl / s}


def ours(height):
    p = PRESETS["katherina"]
    p = replace(
        p,
        height=height,
        familiar_color=None, hair_tail=0.0,
        outfit=replace(p.outfit, hat_color=None, hat_band_color=None, staff_color=None),
    )
    sk = c.skeleton_for(p)
    orig = (c._hair_mass, c._hair_front)
    c._hair_mass = lambda sk, p: ""
    c._hair_front = lambda sk, p: ""
    try:
        svg = c.render_character(p, sk)
    finally:
        c._hair_mass, c._hair_front = orig
    a = _alpha(svg)
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r
    _, br = extent(a, cx)
    rows = np.arange(a.shape[0])
    ys = (rows - cy) / r
    fall = c._hair_fall(sk, p)
    d = c._curve(cx, cy, r, *c.HAIRSTYLES[p.hairstyle].mass(fall))
    hair_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{sk.canvas_w}" height="{sk.canvas_h}">'
        f'<path d="{d}" fill="black" /></svg>'
    )
    _, hr = extent(_alpha(hair_svg), cx)
    anchors = {
        "chin": 1.0,
        "shoulder": (sk.shoulder_y - cy) / r,
        "shoulder_half_w": sk.shoulder_half_w / r,
        "waist": (sk.waist_y - cy) / r,
        "waist_half_w": sk.waist_half_w / r,
        "neck_half_w": sk.neck_half_w / r,
        "arm_x": sk.arm_x / r,
        "arm_half_w": sk.arm_half_w / r,
        "hair_tip": fall,
    }
    return ys, {"hair": hr / r, "body": br / r}, anchors


def _alpha(svg):
    png = cairosvg.svg2png(bytestring=svg.encode())
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"))[..., 3] > 128


def c_sample(chain, n=12):
    (x0, y0), segs = chain
    out, p = [(x0, y0)], (x0, y0)
    for (qx, qy), (ex, ey) in segs:
        for i in range(1, n + 1):
            t = i / n
            out.append(
                (
                    (1 - t) ** 2 * p[0] + 2 * (1 - t) * t * qx + t * t * ex,
                    (1 - t) ** 2 * p[1] + 2 * (1 - t) * t * qy + t * t * ey,
                )
            )
        p = (ex, ey)
    return out


def plot(series, path):
    """Half-width (x) against height (y, down), head radii; one colour per
    source, hair solid, body dotted."""
    PX, X0, Y0 = 120, 40, 40
    W, H = int(3.0 * PX) + 2 * X0 + 260, int(6.5 * PX) + 2 * Y0
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    for xr in np.arange(0, 3.01, 0.5):
        d.line([(X0 + xr * PX, Y0), (X0 + xr * PX, H - Y0)], fill=(225, 225, 225))
        d.text((X0 + xr * PX - 8, 8), f"{xr:.1f}", fill="black")
    for yr in np.arange(-1.5, 5.01, 0.5):
        yy = Y0 + (yr + 1.5) * PX
        d.line([(X0, yy), (X0 + 3 * PX, yy)], fill=(225, 225, 225))
        d.text((4, yy - 6), f"{yr:.1f}", fill="black")
    for i, (label, ys, vs, col, dotted) in enumerate(series):
        prev = None
        for y, v in zip(ys, vs):
            if np.isnan(v) or y < -1.5 or y > 5.0:
                prev = None
                continue
            q = (X0 + v * PX, Y0 + (y + 1.5) * PX)
            if prev is not None and (not dotted or int(y * 40) % 2 == 0):
                d.line([prev, q], fill=col, width=2)
            prev = q
        d.line([(X0 + 3 * PX + 20, Y0 + 20 * i), (X0 + 3 * PX + 50, Y0 + 20 * i)], fill=col, width=3)
        d.text((X0 + 3 * PX + 56, Y0 + 20 * i - 6), label, fill="black")
    im.save(path)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    ry, real = real_ref()
    oy_, only = hair_only_ref()
    cy_, chibi = chibi_ref()
    sources = [("real", ry, real), ("hair_only", oy_, only), ("chibi_ref", cy_, chibi)]
    anchors = {}
    for h in (1.0, 1.3):
        ys, v, a = ours(h)
        sources.append((f"ours h{h}", ys, v))
        anchors[h] = a
    print("anchors, ours (head radii from the head centre):")
    for h, a in anchors.items():
        print(f"  h{h}: " + ", ".join(f"{k} {v:.3f}" for k, v in a.items()))
    print()
    print("half-widths in head radii: hair / body / hair - body")
    print("    y  " + "".join(f"{name:>22}" for name, _, _ in sources))
    for y in ROWS:
        cells = []
        for _, ys, v in sources:
            hw, bw = at(ys, v["hair"], y), at(ys, v["body"], y)
            cells.append(f"{hw:6.2f} {bw:6.2f} {hw - bw:6.2f}  ")
        print(f"{y:5.2f}  " + "".join(f"{s:>22}" for s in cells))
    # The hair-only reference's body, row by row near its shoulders, to find
    # where the silhouette's shoulder is.
    print()
    print("hair_only body hole by row (r):")
    for y in np.arange(0.9, 2.6, 0.1):
        print(f"  {y:4.1f}: {at(oy_, only['body'], y):5.2f}")
    print()
    print("chibi reference hair, left side (r):")
    for y in np.arange(0.9, 4.0, 0.2):
        print(f"  {y:4.1f}: hair {at(cy_, chibi['hair_left'], y):5.2f}  body {at(cy_, chibi['body'], y):5.2f}")
    cols = {
        "real": (200, 40, 40),
        "hair_only": (150, 60, 200),
        "chibi_ref": (40, 140, 60),
        "ours h1.0": (30, 90, 220),
        "ours h1.3": (0, 180, 200),
    }
    series = []
    for name, ys, v in sources:
        series.append((f"{name} hair", ys, v["hair"], cols[name], False))
        series.append((f"{name} body", ys, v["body"], cols[name], True))
    plot(series, f"{OUT}/proportions.png")
    print(f"\n{OUT}/proportions.png, {OUT}/chibi_masks.png")


if __name__ == "__main__":
    main()
