"""Hair-trace audit, test 2: does mapping the reference's body onto ours fix it?

The intervention for hypothesis 1 (the hair is drawn on a different body). The
hair-only reference's pixels are warped from `katherina_grok_real`'s body onto
ours and laid behind our Katherina (rendered without hair, bat or staff); the
front piece's head part (`hair_with_human_shape.png` above the chin) goes over
her face. This is a look at the reference's shape on our figure, never output.

Heights move piecewise through landmarks, the reference's as `trace_hair.py`
measured them (cheek 0.6, chin 1.2285, shoulder 1.8, belt 4.398) onto ours
(cheek 0.6, chin 1.0, our shoulder, our belt), the last span carried on past
the belt. Widths are what the three models differ on, each blended in from
the identity at the chin to full at our shoulder:

- **as traced**: x unchanged, which is what D5 did (y squeezed onto our belt);
- **scaled**: x times `k`, our body's outer half-width (arms included) over the
  reference's at the same landmark-relative height, the median below the
  shoulder: `_garment_placement`'s rule, the hair scaled with the body;
- **offset**: hair over the body maps proportionally, hair beyond it keeps its
  distance past the body's outer edge in head radii: the hair as body plus a
  thickness.

The prediction, if the body is the whole story: as traced shows the cape D5
saw, and one of the other two takes it away with the hair sitting on our body
as it sits on the reference's. If the hair on a chibi hangs from the head
rather than from the shoulders, scaling pinches it in behind the body.

Written to `out/hair_audit/retarget.png`, Katherina at height 1.0 and 1.3,
beside `katherina_grok` (the tall-chibi design reference) at the same head
radius.

    ./harness/run.sh harness/hair_audit/retarget.py
"""

import io
import json
from dataclasses import replace

import cairosvg
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/hair_audit"
PX = 70  # px per head radius in the sheet
BOX = (-2.8, -1.7, 2.8, 4.4)
REAL_CAL = (636.0, 290.0, 88.7)
REF_LM = {"cheek": 0.6, "chin": 1.2285, "shoulder": 1.8, "belt": 4.398}
MODELS = ("as traced", "scaled", "offset")
CHIBI = ("ref-local/katherina_grok/katherina_grok.jpg", (650.0, 481.0, 173.7))


def ref_body_w():
    """The reference's outer body half-width per head-radius row, the right
    side of the dress segment (the staff arm is on the left)."""
    s = np.asarray(Image.open("ref-local/katherina_grok_real/segments/dark-blue-dress.png").convert("RGBA"))[..., 3] > 128
    m = np.zeros((1568, 1264), bool)
    m[417 : 417 + s.shape[0], 404 : 404 + s.shape[1]] = s[: 1568 - 417, : 1264 - 404]
    ox, oy, S = REAL_CAL
    ys, ws = [], []
    for y in range(m.shape[0]):
        xs = np.nonzero(m[y])[0]
        if xs.size:
            ys.append((y - oy) / S)
            ws.append((xs.max() - ox) / S)
    return np.array(ys), np.array(ws)


def figure(height):
    p = PRESETS["katherina"]
    p = replace(
        p,
        height=height,
        familiar_color=None, hair_tail=0.0,
        outfit=replace(p.outfit, hat_color=None, hat_band_color=None, staff_color=None),
    )
    sk = c.skeleton_for(p)
    orig = (c._hair_mass, c._hair_front)
    c._hair_mass, c._hair_front = (lambda sk, p: ""), (lambda sk, p: "")
    try:
        svg = c.render_character(p, sk)
    finally:
        c._hair_mass, c._hair_front = orig
    k = PX / sk.head_r
    png = cairosvg.svg2png(bytestring=svg.encode(), scale=k)
    body = Image.open(io.BytesIO(png)).convert("RGBA")
    # Into the sheet's frame: head centre at (-BOX[0], -BOX[1]) * PX.
    W, H = round((BOX[2] - BOX[0]) * PX), round((BOX[3] - BOX[1]) * PX)
    frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    frame.paste(body, (round(-BOX[0] * PX - sk.head_cx * k), round(-BOX[1] * PX - sk.head_cy * k)))
    a = np.asarray(frame)[..., 3] > 128
    cx = -BOX[0] * PX
    ys, ws = [], []
    for y in range(H):
        xs = np.nonzero(a[y, int(cx) :])[0]
        if xs.size:
            ys.append(y / PX + BOX[1])
            ws.append(xs.max() / PX)
    lm = {
        "cheek": 0.6,
        "chin": 1.0,
        "shoulder": (sk.shoulder_y - sk.head_cy) / sk.head_r,
        "belt": (sk.waist_y - sk.head_cy) / sk.head_r,
    }
    return frame, lm, (np.array(ys), np.array(ws))


def piecewise(v, xs, ys):
    """Piecewise-linear, carried on past the last knot at the last slope."""
    if v <= xs[-1]:
        return float(np.interp(v, xs, ys))
    slope = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
    return ys[-1] + (v - xs[-1]) * slope


def smooth_w(ys, ws, lo):
    """Outer half-width as a function of height, from `lo` down: a running
    median over 0.15 head radii, so a collar point or a cuff does not steer it."""
    keep = ys >= lo
    ys, ws = ys[keep], ws[keep]
    out = np.array([np.median(ws[np.abs(ys - y) < 0.075]) for y in ys])
    return ys, out


def warp(src, src_cal, lm_ours, xmap):
    """Backward-warp `src` (RGBA, own pixels, `src_cal` its head centre and
    px per head radius) into the sheet's frame on our landmarks. `xmap(row
    height in our frame, |x| ours)` gives |x| in the reference."""
    names = ("cheek", "chin", "shoulder", "belt")
    ours_y = [lm_ours[n] for n in names]
    ref_y = [REF_LM[n] for n in names]
    W, H = round((BOX[2] - BOX[0]) * PX), round((BOX[3] - BOX[1]) * PX)
    gy, gx = np.mgrid[0:H, 0:W].astype(float)
    yo = gy / PX + BOX[1]
    xo = gx / PX + BOX[0]
    flat = yo[:, 0]
    yr = np.array([v if v <= 0.6 else piecewise(v, ours_y, ref_y) for v in flat])
    xr = np.empty_like(xo)
    for i, v in enumerate(flat):
        xr[i] = np.sign(xo[i]) * xmap(v, np.abs(xo[i]))
    yr2 = np.repeat(yr[:, None], W, axis=1)
    ox, oy, s = src_cal
    sx = ox + xr * s
    sy = oy + yr2 * s
    arr = np.asarray(src.convert("RGBA")).astype(float)
    out = np.zeros((H, W, 4))
    for ch in range(4):
        out[..., ch] = ndi.map_coordinates(arr[..., ch], [sy, sx], order=1, cval=0)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")


def models(lm, ours_w, ref_w):
    """The three x maps for one figure: our |x| at our row height -> the
    reference's |x|."""
    oy_, ow = smooth_w(*ours_w, lm["shoulder"] + 0.1)
    ry_, rw = smooth_w(*ref_w, 1.95)

    def ref_row(v):
        tb = (v - lm["shoulder"]) / (lm["belt"] - lm["shoulder"])
        return REF_LM["shoulder"] + tb * (REF_LM["belt"] - REF_LM["shoulder"])

    def widths(v):
        v2 = max(v, lm["shoulder"] + 0.1)
        wo = np.interp(min(v2, lm["belt"]), oy_, ow)
        wr = np.interp(min(ref_row(v2), REF_LM["belt"]), ry_, rw)
        return wo, wr

    below = [v for v in oy_ if v <= lm["belt"]]
    k = float(np.median([widths(v)[0] / widths(v)[1] for v in below]))

    def blend(v):
        return float(np.clip((v - lm["chin"]) / (lm["shoulder"] - lm["chin"]), 0, 1))

    def as_traced(v, ax):
        return ax

    def scaled(v, ax):
        f = 1 + (k - 1) * blend(v)
        return ax / f

    def offset(v, ax):
        b = blend(v)
        if b == 0:
            return ax
        wo, wr = widths(v)
        inside = ax * wr / wo
        beyond = wr + (ax - wo)
        full = np.where(ax <= wo, inside, beyond)
        return ax + b * (full - ax)

    return k, {"as traced": as_traced, "scaled": scaled, "offset": offset}


def hair_only_cal():
    reg = json.load(open("out/hair_only/register.json"))
    sc, (dx, dy) = reg["scale"], reg["offset"]
    ox, oy, s = REAL_CAL
    return ((ox - dx) / sc, (oy - dy) / sc, s / sc)


def chibi_tile():
    path, (ox, oy, s) = CHIBI
    im = Image.open(path).convert("RGBA")
    k = PX / s
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    W, H = round((BOX[2] - BOX[0]) * PX), round((BOX[3] - BOX[1]) * PX)
    out = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    out.paste(im, (round(-BOX[0] * PX - ox * k), round(-BOX[1] * PX - oy * k)))
    return out


def rules(im, label):
    d = ImageDraw.Draw(im)
    W, H = im.size
    for yr in range(-1, 5):
        y = (yr - BOX[1]) * PX
        d.line([(0, y), (W, y)], fill=(170, 170, 170), width=1)
        d.text((2, y - 11), f"{yr}", fill=(200, 0, 0))
    d.text((4, 4), label, fill=(200, 0, 0))
    return im


def main() -> None:
    ref_w = ref_body_w()
    full = Image.open("ref-local/katherina_hair/hair_only.png")
    front = Image.open("ref-local/katherina_hair/hair_with_human_shape.png")
    cal = hair_only_cal()
    rows = []
    for height in (1.0, 1.3):
        body, lm, ours_w = figure(height)
        k, maps = models(lm, ours_w, ref_w)
        print(f"h{height}: k {k:.2f}; landmarks " + ", ".join(f"{n} {v:.3f}" for n, v in lm.items()))
        tiles = []
        for name in MODELS:
            back = warp(full, cal, lm, maps[name])
            fr = warp(front, cal, lm, maps[name])
            # The front piece's head part only: above our chin.
            fa = np.asarray(fr).copy()
            cut = round((lm["chin"] - BOX[1]) * PX)
            fa[cut:, :, 3] = 0
            W, H = back.size
            sheet = Image.new("RGBA", (W, H), (255, 255, 255, 255))
            sheet.alpha_composite(back)
            sheet.alpha_composite(body)
            sheet.alpha_composite(Image.fromarray(fa, "RGBA"))
            tiles.append(rules(sheet, f"h{height} {name}"))
        tiles.append(rules(chibi_tile(), "katherina_grok (tall chibi ref)"))
        rows.append(tiles)
    W, H = rows[0][0].size
    out = Image.new("RGB", (W * len(rows[0]) + 6 * (len(rows[0]) - 1), H * len(rows) + 6), (120, 120, 120))
    for j, tiles in enumerate(rows):
        for i, t in enumerate(tiles):
            out.paste(t.convert("RGB"), (i * (W + 6), j * (H + 6)))
    out.save(f"{OUT}/retarget.png")
    print(f"{OUT}/retarget.png {out.size}")


if __name__ == "__main__":
    main()
