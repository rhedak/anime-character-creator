"""The traced hair against the segment it was traced from (the owner,
2026-09-29: the traced hair has a lot less detail and reads as a block).

The as-is trace (`hair_asis.json`) is taken back into the composite's pixels
(undoing the belt squeeze, y only) and drawn there on its own, filled and
stroked at the weights `preview.py` draws it at, so it lies over the segment
pixel for pixel. Measured, in the composite's pixels:

- **silhouette**: every seen outer edge pixel of the segment (page beyond it,
  as `fill.py` counts) and its distance to the traced outline;
- **lines**: recall, the share of the segment's line skeleton (`lines.py`'s
  black-hat and hysteresis) within 2 px of a traced line; precision, the
  share of traced line length within 2 px of the skeleton;
- **line weight**: the segment's lines' widths (twice the distance transform
  on the skeleton), against ours;
- **tones**: the segment's hair colours clustered (k-means on the black-hat's
  flat pixels), each cluster's share of the area;
- **tips**: pointed ends on the lower outline (local lowest points standing
  at least 0.1 head radii below both neighbours' highs), the segment's seen
  ones against the trace's.

Writes `out/trace_hair/audit.txt` and `audit.png`: the segment on white, our
traced hair alone, and the two overlaid (the segment's lines red, ours blue).
"""

import io
import json
import sys

sys.path.insert(0, "harness/trace_hair")

import cairosvg
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

import contrast as ct
import lines as L
from fill import page_mask
from occlusion import masks
from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/trace_hair"
CROP = (400, 180, 880, 800)


def unsqueeze(hair):
    """Undo the as-is belt squeeze: y below the cheek line stretched back."""
    k = hair["squeeze"]
    cheek = hair["cheek"]

    def u(q):
        return (q[0], cheek + (q[1] - cheek) / k if q[1] > cheek else q[1])

    def chain(ch):
        s0, segs = ch
        return u(s0), [(u(cq), u(e)) for cq, e in segs]

    return chain


def svg_path(ch, ox, oy, s, close):
    s0, segs = ch
    d = [f"M {ox + s0[0] * s:.2f} {oy + s0[1] * s:.2f}"]
    for cq, e in segs:
        d.append(f"Q {ox + cq[0] * s:.2f} {oy + cq[1] * s:.2f} {ox + e[0] * s:.2f} {oy + e[1] * s:.2f}")
    return " ".join(d) + (" Z" if close else "")


def main() -> None:
    hair = json.load(open(f"{OUT}/hair_asis.json"))
    un = unsqueeze(hair)
    (ox, oy), s = hair["calibration"]["origin"], hair["calibration"]["px_per_r"]
    a = np.asarray(Image.open(ct.REF).convert("RGB")).astype(float)
    H, W = a.shape[:2]
    lum = a @ np.array([0.299, 0.587, 0.114])
    m = ct.hair_mask((H, W))

    p = PRESETS["katherina"]
    sk = c.skeleton_for(p)
    sw_r = c._stroke_w(sk) / sk.head_r
    out_w, in_w = c._outline_w(sw_r * s), c._interior_w(sw_r * s, 0.55)
    colour = p.hair_color

    parts = []
    for key in ("mass", "front"):
        pieces = hair.get(f"{key}_parts") or [[hair[key], []]]
        d = " ".join(svg_path(un(ch), ox, oy, s, True) for outer, holes in pieces for ch in [outer, *holes])
        stroke = c.OUTLINE if key == "mass" else "none"
        parts.append(f'<path d="{d}" fill="{colour}" fill-rule="evenodd" stroke="{stroke}" stroke-width="{out_w:.2f}" />')
    for e in hair["front_edges"]:
        parts.append(f'<path d="{svg_path(un(e), ox, oy, s, False)}" fill="none" stroke="{c.OUTLINE}" stroke-width="{out_w:.2f}" stroke-linecap="round" />')
    line_d = [svg_path(un(ch), ox, oy, s, False) for ch in hair["lines"]]
    for d in line_d:
        parts.append(f'<path d="{d}" fill="none" stroke="{c.OUTLINE}" stroke-width="{in_w:.2f}" stroke-linecap="round" />')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="white" />{"".join(parts)}</svg>'
    ours = np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert("RGB")).astype(float)
    lines_only = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">' + "".join(
        f'<path d="{d}" fill="none" stroke="black" stroke-width="1" />' for d in line_d
    ) + "</svg>"
    ours_lines = np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=lines_only.encode()))).convert("RGBA"))[..., 3] > 60

    report = []

    # Silhouette.
    ours_hair = np.abs(ours - np.array([int(colour[i : i + 2], 16) for i in (1, 3, 5)])).sum(2) < 40
    ours_ink = ours.sum(2) < 200
    traced = (ours_hair | ours_ink) & ~(ours.sum(2) > 740)
    edge_ref = m & ~ndi.binary_erosion(m)
    occ_all = np.zeros_like(m)
    for k_, v_ in masks((H, W)).items():
        occ_all |= v_
    page = page_mask(a, occ_all)
    seen_edge = edge_ref & ndi.binary_dilation(page, iterations=4)
    traced_edge = traced & ~ndi.binary_erosion(traced)
    dt = ndi.distance_transform_edt(~traced_edge)
    dev = dt[seen_edge]
    report.append(f"silhouette: {seen_edge.sum()} seen edge px; distance to the traced outline: median {np.median(dev):.1f} px, 90th {np.percentile(dev, 90):.1f}, max {dev.max():.1f} (1 head radius = {s:.1f} px)")
    area_ref, area_ours = m.sum(), (traced & ndi.binary_dilation(m, iterations=6)).sum()
    report.append(f"  seen hair area {area_ref} px; traced area over it {area_ours} px")

    # Lines.
    disk = np.hypot(*np.mgrid[-L.R : L.R + 1, -L.R : L.R + 1]) <= L.R
    bh = ndi.grey_closing(lum, footprint=disk) - lum
    inner = ndi.binary_erosion(m, iterations=1)
    lo = inner & (bh > L.LO)
    lab, n = ndi.label(lo, structure=np.ones((3, 3)))
    strong = np.unique(lab[inner & (bh > L.HI)])
    ln = np.isin(lab, strong[strong > 0])
    skel = L.thin(ndi.binary_closing(ln, np.ones((3, 3))) & inner)
    near_edge = m & ~ndi.binary_erosion(m, iterations=L.EDGE + 1)
    skel_in = skel & ~near_edge
    d_ours = ndi.distance_transform_edt(~ours_lines)
    d_ref = ndi.distance_transform_edt(~skel)
    recall = (d_ours[skel_in] <= 2).mean()
    precision = (d_ref[ours_lines] <= 2).mean()
    report.append(f"lines: segment skeleton {skel_in.sum()} px (off the edge); recall {recall:.0%}, precision {precision:.0%}; traced lines {len(hair['lines'])}")
    widths = 2 * ndi.distance_transform_edt(ln)[skel]
    report.append(f"line weight: segment median {np.median(widths):.1f} px (25th {np.percentile(widths, 25):.1f}, 75th {np.percentile(widths, 75):.1f}); ours {in_w:.2f} px")
    edge_w = 2 * ndi.distance_transform_edt(~m & ~page)[ndi.binary_dilation(m) & ~m]
    report.append(f"outline weight: the segment's outer outline about {np.median(edge_w[edge_w > 0]):.1f} px (the page gap it sits in); ours {out_w:.2f} px")

    # Tones.
    flat = m & (bh < 6) & ndi.binary_erosion(m, iterations=3)
    px = a[flat]
    rng = np.random.default_rng(0)
    cen = px[rng.choice(len(px), 4, replace=False)]
    for _ in range(25):
        lab_k = np.argmin(((px[:, None, :] - cen[None]) ** 2).sum(2), 1)
        cen = np.array([px[lab_k == i].mean(0) if (lab_k == i).any() else cen[i] for i in range(4)])
    order = np.argsort(cen.sum(1))
    shares = [(lab_k == i).mean() for i in order]
    report.append("tones (flat hair pixels, k-means 4, dark to light): " + ", ".join(f"{tuple(int(v) for v in cen[i])} {sh:.0%}" for i, sh in zip(order, shares)))
    report.append(f"  ours: one tone, {colour}")

    # Tips.
    def tips(mask):
        ys = np.array([np.nonzero(mask[:, x])[0].max() if mask[:, x].any() else -1 for x in range(W)], float)
        ys[ys < 0] = np.nan
        n_tip, rise = 0, 0.1 * s
        for x in range(2, W - 2):
            y = ys[x]
            if np.isnan(y) or y < oy + 1.5 * s:
                continue
            win_l, win_r = ys[max(0, x - 25) : x], ys[x + 1 : x + 26]
            if np.all(np.isnan(win_l)) or np.all(np.isnan(win_r)):
                continue
            if y >= np.nanmax(ys[max(0, x - 3) : x + 4]) and y - np.nanmin(win_l) > rise and y - np.nanmin(win_r) > rise:
                n_tip += 1
        return n_tip

    report.append(f"tips on the lower outline: segment {tips(m)}, traced {tips(traced)}")
    txt = "\n".join(report)
    print(txt)
    open(f"{OUT}/audit.txt", "w").write(txt + "\n")

    x0, y0, x1, y1 = CROP
    seg_white = np.where(m[..., None], a, 255)
    over = np.full((H, W, 3), 255.0)
    over[m] = (225, 215, 235)
    over[ndi.binary_dilation(skel)] = (230, 40, 40)
    over[ours_lines] = (40, 90, 230)
    tiles = [Image.fromarray(v[y0:y1, x0:x1].clip(0, 255).astype(np.uint8)) for v in (seg_white, ours, over)]
    sheet = Image.new("RGB", (tiles[0].width * 3 + 8, tiles[0].height), (150, 150, 150))
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * (t.width + 4), 0))
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.LANCZOS)
    sheet.save(f"{OUT}/audit.png")
    print(f"{OUT}/audit.png", sheet.size)


if __name__ == "__main__":
    main()
