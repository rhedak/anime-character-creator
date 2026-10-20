"""The interior of the open palm and the fist: nails, finger pieces, finger creases, the dark cavity, traced from the close-ups and Grok's segment cut-outs.

    ./harness/run.sh harness/franzi_hands/poses.py           (first: the outlines and out/franzi_hands/pose-*.json, which carry each hand's mapping)
    ./harness/run.sh harness/franzi_hands/poses_lines.py     writes out/franzi_hands/pose-lines-*-view.png and ts/src/body-adult-hand-poses-lines-data.ts

The segments are small cropped PNGs, not full-canvas layers, so each is found in its close-up by a masked sum of squared differences (as locate.py does for the relaxed hand), turned into
the hanging frame like the outline (poses.py: the open palm flipped vertically, the fist turned a half turn) and fitted as a closed quadratic chain in the same knot coordinates.

open     the palm's lines (OPEN_LINES: points read off a gridded, contrast-stretched view and snapped onto the drawn dark ridge, as trace_lines.py does for the relaxed hand) and the
         short crease ticks across the fingers (dark ridges inside Grok's five finger cut-outs, as one centre line each); both tapered, flat dark.
fist     nails: the four fingernail cut-outs; finger pieces: the five finger cut-outs, each drawn with a thin outline of its own so the separations between the curled fingers read;
         cavity: the dark wedge between the thumb and the curled fingers (the close-up's luminance under CAVITY_L inside the hand), drawn dark.
"""

import glob
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.signal import fftconvolve

sys.path.insert(0, ".claude/skills/trace-reference")
import trace_lib as tl  # noqa: E402

sys.path.insert(0, "harness/franzi_hands")
import poses  # noqa: E402

OUT = Path("out/franzi_hands")
CAVITY_L = 110  # lightness under this, inside the hand, is the cavity (lit skin is 205 to 220, the shaded fingers 150 to 190)


def load(name):
    img, tf = poses.HANDS[name]
    rgba = np.array(Image.open(f"ref/franzi/hands/{img}.png").convert("RGBA"))
    return rgba, tf


def locate(rgba, path):
    """Where the cropped segment sits in the close-up (masked SSD), and its full-canvas mask."""
    I = rgba[..., :3].astype(float)
    seg = np.array(Image.open(path).convert("RGBA")).astype(float)
    m = (seg[..., 3] > 200).astype(float)
    T = seg[..., :3]
    npx = m.sum()
    s_ii = sum(fftconvolve(I[..., c] ** 2, m[::-1, ::-1], mode="valid") for c in range(3))
    s_it = sum(fftconvolve(I[..., c], (m * T[..., c])[::-1, ::-1], mode="valid") for c in range(3))
    s_tt = float((m[..., None] * T**2).sum())
    score = np.real((s_ii - 2 * s_it + s_tt) / (3 * npx))
    y, x = np.unravel_index(int(np.argmin(score)), score.shape)
    full = np.zeros(rgba.shape[:2], bool)
    h, w = m.shape
    full[y : y + h, x : x + w] = m > 0
    return full, (int(x), int(y), float(score[y, x]) ** 0.5)


def fit_masks(mask, info, tf, blur, tol, min_px):
    """Closed chains of the components of `mask` (turned into the hanging frame), in knot coordinates, with the mapping of `info` (poses.py's pose-NAME.json)."""
    k, yw, xw = info["k"], info["yw"], info["xw"]
    m = tf(mask)
    out = []
    lab, n = ndimage.label(m)
    for i in range(1, n + 1):
        c = lab == i
        if c.sum() < min_px:
            continue
        pts = np.array(tl.boundary(c), float)
        sm = np.stack([ndimage.gaussian_filter1d(pts[:, j], blur, mode="wrap") for j in (0, 1)], 1)
        body = [(poses.V_WRIST - (x - xw) * k, poses.D_WRIST + (y - yw) * k) for x, y in sm]
        out.append(tl.fit_closed(body, tol))
    return out


SNAP_R, SNAP_PEN, ON_RIDGE = 7.0, 0.5, -5.0  # the palm's creases are hairlines: their difference of Gaussians is -5 to -14, against -18 and below for the relaxed hand's thick lines
# name: points in the turned open palm's pixels (read off out/franzi_hands gridded views: x then y), from the line's start outward
OPEN_LINES = {
    # the big arc round the ball of the thumb, from the wrist crease down to the thumb web
    "thenar": [(476, 444), (495, 466), (526, 506), (542, 550), (545, 594), (536, 650), (520, 706), (495, 762), (464, 800), (432, 837), (414, 862)],
    # the two palm creases running up to the right
    "crease-a": [(389, 894), (445, 872), (520, 844), (576, 812), (620, 775), (639, 749)],
    "crease-b": [(557, 900), (607, 875), (664, 850), (720, 828), (782, 803), (820, 784)],
    # the thumb's web line
    "web": [(251, 731), (270, 769), (289, 806), (301, 831)],
}


def densify(pts, step=2.0):
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        seg = np.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1])
        n = max(2, int(seg / step))
        for k in range(n):
            t = k / n
            out.append([0.5 * ((2 * p[i][j]) + (-p[i - 1][j] + p[i + 1][j]) * t + (2 * p[i - 1][j] - 5 * p[i][j] + 4 * p[i + 1][j] - p[i + 2][j]) * t**2 + (-p[i - 1][j] + 3 * p[i][j] - 3 * p[i + 1][j] + p[i + 2][j]) * t**3) for j in (0, 1)])
    out.append(list(pts[-1]))
    return np.array(out, float)


def normals(c):
    t = np.gradient(ndimage.gaussian_filter1d(c, 4, axis=0, mode="nearest"), axis=0)
    t /= np.maximum(np.hypot(t[:, 0], t[:, 1]), 1e-9)[:, None]
    return np.stack([-t[:, 1], t[:, 0]], 1)


class Ridge:
    """The difference of Gaussians of a close-up's lightness, to snap a hand-placed line onto the drawn dark ridge beside it."""

    def __init__(self, a):
        lum = a[..., :3].astype(float).mean(2)
        lum = np.where(a[..., 3] > 128, lum, 220.0)
        self.lum = lum
        self.hp = ndimage.gaussian_filter(lum, 1.5) - ndimage.gaussian_filter(lum, 5.0)

    def at(self, c):
        return ndimage.map_coordinates(self.hp, [c[:, 1], c[:, 0]], order=1, mode="nearest")

    def snap(self, pts):
        c = densify(pts)
        nrm = normals(c)
        offs = np.linspace(-SNAP_R, SNAP_R, 15)
        vals = np.stack([self.at(c + o * nrm) for o in offs], 1)
        best = ndimage.gaussian_filter1d(offs[np.argmin(vals + SNAP_PEN * np.abs(offs)[None, :], axis=1)], 4, mode="nearest")
        out = c + best[:, None] * nrm
        return out, self.at(out)

    def width(self, out, w_min=3.0, w_max=16.0):
        """Thickness across the line at nine points: darkness coverage along the normal, between lit skin and the line."""
        nrm = normals(out)
        res = []
        for i in np.linspace(0, len(out) - 1, 9).astype(int):
            offs = np.linspace(-14, 14, 57)
            v = ndimage.map_coordinates(self.lum, [out[i, 1] + offs * nrm[i, 1], out[i, 0] + offs * nrm[i, 0]], order=1, mode="nearest")
            res.append(float(np.clip((190 - v) / 130, 0, 1).sum() * (offs[1] - offs[0])))
        return ndimage.gaussian_filter1d(np.clip(res, w_min, w_max), 0.8, mode="nearest")


def to_knots(out, info):
    k, yw, xw = info["k"], info["yw"], info["xw"]
    return [(poses.V_WRIST - (x - xw) * k, poses.D_WRIST + (y - yw) * k) for x, y in out]


def line_chains(ridge, named, info, step=2):
    """Open chains and their thicknesses (in head radii, nine points) for hand-placed lines, snapped onto the ridge."""
    chains, widths = [], []
    k = info["k"]
    for name, pts in named.items():
        out, on = ridge.snap(pts)
        body = to_knots(out[::step], info)
        chains.append(tl.fit_chain(body, tl.simplify(body, 0.0016)))
        widths.append([float(w * k / (poses.H / 352 * 0.499)) for w in ridge.width(out)])
        print(f"line {name:9s}: {len(chains[-1][1])} segments, {100 * (on < ON_RIDGE).mean():.0f}% on a ridge")
    return chains, widths


def ticks(ridge, finger_masks, info, tf, min_px=15, max_px=500):
    """The short dark creases across the fingers: dark ridge pixels inside the finger cut-outs (eroded), each component as one straight-ish centre line with its thickness."""
    chains, widths = [], []
    k = info["k"]
    inside = ndimage.binary_erosion(tf(finger_masks), iterations=14)
    dark = (ridge.hp < -6) & inside
    lab, n = ndimage.label(dark)
    for i in range(1, n + 1):
        c = lab == i
        if not (min_px <= c.sum() <= max_px):
            continue
        ys, xs = np.nonzero(c)
        pts = np.stack([xs, ys], 1).astype(float)
        mu = pts.mean(0)
        u, sv, vt = np.linalg.svd(pts - mu, full_matrices=False)
        ax = vt[0]
        proj = (pts - mu) @ ax
        length = proj.max() - proj.min()
        if length < 14 or sv[1] / max(sv[0], 1e-9) > 0.4:  # too short, or a blob rather than a line
            continue
        mid = mu + ax * (proj.min() + proj.max()) / 2
        e0, e1 = mid - ax * length / 2, mid + ax * length / 2
        body = to_knots([e0, mid, e1], info)
        chains.append(tl.fit_chain(body, [0, 1, 2]))
        thick = float(c.sum() / length)
        widths.append([float(np.clip(thick, 3, 9) * k / (poses.H / 352 * 0.499))] * 9)
    return chains, widths


def pt(p):
    return f"[{p[0]:.4f}, {p[1]:.4f}]"


def chain_ts(c):
    st, sg = c
    return f"[{pt(st)}, [{', '.join(f'[{pt(cc)}, {pt(e)}]' for cc, e in sg)}]]"


def chains_ts(name, doc, chains):
    if not chains:
        return f"/** {doc} */\nexport const {name}: readonly Chain[] = [];\n\n"
    return f"/** {doc} */\nexport const {name}: readonly Chain[] = [\n  " + ",\n  ".join(chain_ts(c) for c in chains) + ",\n];\n\n"


def view(name, rgba, tf, chains, info, tag):
    """The fitted chains (red) over the turned close-up."""
    k, yw, xw = info["k"], info["yw"], info["xw"]
    a = tf(rgba)
    im = Image.fromarray(a[..., :3].astype(np.uint8)).convert("RGB")
    dr = ImageDraw.Draw(im)
    for ch in chains:
        pts = [((poses.V_WRIST - v) / k + xw, (d - poses.D_WRIST) / k + yw) for v, d in poses.chain_points(ch)]
        dr.line(pts + [pts[0]], fill=(230, 30, 30), width=3)
    ys = np.nonzero((a[..., 3] > 128).any(1))[0]
    im = im.crop((0, ys.min() + 150, im.width, ys.max() + 10))
    im = im.resize((im.width // 2, im.height // 2))
    im.save(OUT / f"pose-lines-{name}-{tag}-view.png")


def main():
    # ---- the open palm: the palm's lines and the finger creases
    rgba, tf = load("open")
    info = json.load(open(OUT / "pose-open.json"))
    ridge = Ridge(tf(rgba))
    open_lines, open_widths = line_chains(ridge, OPEN_LINES, info)
    fmask = np.zeros(rgba.shape[:2], bool)
    for path in sorted(glob.glob("ref/franzi/hands/segments/open-palm/finger-creases/*.png")):
        mask, (x, y, rms) = locate(rgba, path)
        fmask |= mask
    tick_chains, tick_widths = ticks(ridge, fmask, info, tf)
    print(f"open: {len(open_lines)} palm lines, {len(tick_chains)} finger creases")
    open_lines += tick_chains
    open_widths += tick_widths
    view("open", rgba, tf, [c for c in open_lines], info, "lines")

    # ---- the fist: nails, finger pieces, cavity
    rgba, tf = load("fist")
    info = json.load(open(OUT / "pose-fist.json"))
    nails, fingers = [], []
    for path in sorted(glob.glob("ref/franzi/hands/segments/fist/fingernails/*.png")):
        mask, (x, y, rms) = locate(rgba, path)
        print(f"{path.split('/')[-1]}: at ({x}, {y}) rms {rms:.1f}")
        nails += fit_masks(ndimage.binary_fill_holes(mask), info, tf, 2.5, 0.0025, 300)
    pieces = []
    for path in sorted(glob.glob("ref/franzi/hands/segments/fist/fingers/*.png")):
        mask, (x, y, rms) = locate(rgba, path)
        ys_, xs_ = np.nonzero(tf(mask))
        pieces.append((xs_.mean(), path, mask))
        print(f"{path.split('/')[-1]}: at ({x}, {y}) rms {rms:.1f}, centre x in the turned frame {xs_.mean():.0f}")
    # the thumb piece (leftmost once turned) has a ragged top edge where Grok cut it from the palm, which drew a wiggly line across the hand's base: left out, as the relaxed hand leaves out its ragged piece
    for cx_, path, mask in sorted(pieces)[1:]:
        fingers += fit_masks(ndimage.binary_fill_holes(mask), info, tf, 3.0, 0.0025, 3000)
    lum = rgba[..., :3].astype(float).mean(2)
    alpha = rgba[..., 3] > 128
    sil = ndimage.binary_fill_holes(alpha)
    cav = sil & ((lum < CAVITY_L) | ~alpha)
    cav = ndimage.binary_opening(cav, structure=np.ones((9, 9)))
    lab, n = ndimage.label(cav)
    sizes = ndimage.sum(cav, lab, range(1, n + 1))
    cav = np.isin(lab, [i + 1 for i, z in enumerate(sizes) if z > 800])
    cavity = fit_masks(cav, info, tf, 4.0, 0.003, 800)
    print(f"fist: {len(nails)} nails, {len(fingers)} finger pieces, {len(cavity)} cavity shapes (sizes {sorted(int(z) for z in sizes)})")
    view("fist", rgba, tf, nails + fingers + cavity, info, "details")

    Path("ts/src/body-adult-hand-poses-lines-data.ts").write_text(
        "// Generated by harness/franzi_hands/poses_lines.py from ref/franzi/hands/open-palm.png and fist.png and Grok's cut-outs of them. Do not edit by hand.\n"
        "// The interior of the open palm and the fist in the frame of body-adult-hand-poses-data.ts: knot coordinates [v, d] (head heights), the viewer's-left hand.\n\n"
        'import type { Chain } from "./tables.ts";\n\n'
        + chains_ts("HAND_OPEN_LINES", "The open palm's lines: the arc round the ball of the thumb, two palm creases, the thumb's web line, then the short creases across the fingers; open chains, tapered, drawn dark.", open_lines)
        + "/** Each open-palm line's thickness in head radii at nine evenly spaced points. */\nexport const HAND_OPEN_LINE_WIDTHS: readonly (readonly number[])[] = [\n  "
        + ",\n  ".join("[" + ", ".join(f"{w:.4f}" for w in ws) + "]" for ws in open_widths)
        + ",\n];\n\n"
        + chains_ts("HAND_FIST_NAILS", "The visible nails of the fist, closed rings with a lighter fill.", nails)
        + chains_ts("HAND_FIST_FINGERS", "The fist's finger pieces, each closed, drawn with a thin outline of its own so the separations show.", fingers)
        + chains_ts("HAND_FIST_CAVITY", "The dark wedge between the fist's thumb and curled fingers.", cavity)
    )
    print("wrote ts/src/body-adult-hand-poses-lines-data.ts")


if __name__ == "__main__":
    main()
