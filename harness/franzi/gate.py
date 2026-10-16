"""G0, the silhouette gate of the adult-body campaign (docs/adult-body-plan.md).

Compares the neck-down silhouette of a body type's underwear-only render with the fused Franzi target
(out/franzi/target.png, made by measure.py). Both silhouettes are measured by the same landmark rules and brought to
a common scale (chin to sole), then compared:

    IoU                  at least 0.93
    width at 10% steps   each within 5% (full ink width, and the body run where the arms are free)
    landmark heights     waist, hip, crotch each within 0.05 H of the target (H: the target's head height)

    ./harness/run.sh harness/franzi/gate.py BODY [HEIGHT] [--silhouette]   # renders it first; --silhouette: no underwear
    ./harness/run.sh harness/franzi/gate.py --self            # the target against itself: must pass

Exit status 0 on pass, 1 on a fail. The thresholds are fixed in the plan; change them only with a note in
docs/adult-body-status.md and the owner's say.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path("out/franzi")
IOU_MIN, WIDTH_TOL, LANDMARK_TOL_H = 0.93, 0.05, 0.05
TARGET_H_PX = 352  # the references' head height (top of hair to chin) on the common canvas


def runs(row):
    d = np.diff(np.concatenate([[0], row.astype(int), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def rows_of(m, y0, y1):
    """Per row: (outer width, body-run width, centre)."""
    out = []
    for y in range(y0, y1):
        r = runs(m[y])
        if not r:
            out.append((0, 0, 0.0))
            continue
        body = r[len(r) // 2] if len(r) >= 3 else max(r, key=lambda a: a[1] - a[0])
        out.append((r[-1][1] - r[0][0], body[1] - body[0], (r[0][0] + r[-1][1]) / 2))
    return out


def landmarks(m, y_sh, y_sole):
    """Waist, hip and crotch rows, found the same way on every silhouette."""
    n = y_sole - y_sh
    rw = rows_of(m, y_sh, y_sole)
    body = np.array([b for _, b, _ in rw], dtype=float)
    lo, hi = int(0.15 * n), int(0.35 * n)
    # An extremum is a plateau on a smooth outline: take the middle of the rows within 1.5% of it, not an argmin.
    def middle(a, lo_, extreme):
        near = np.where(np.abs(a - extreme) <= 0.015 * extreme)[0]
        return lo_ + int(np.median(near))

    seg = body[lo:hi]
    waist = middle(seg, lo, seg.min())
    seg = body[waist : int(0.5 * n)]
    hip = middle(seg, waist, seg.max())
    crotch = hip
    while crotch + 1 < len(body) and body[crotch + 1] > 0.7 * body[crotch]:
        crotch += 1
    return {"waist": y_sh + waist, "hip": y_sh + hip, "crotch": y_sh + crotch}


def silhouette(png, chin_row):
    m = np.array(Image.open(png))[..., 3] > 128
    ys = np.where(m.any(1))[0]
    return m, chin_row, int(ys.max())


def compare(rm, r_sh, r_sole, tm, t_sh, t_sole, h_target_px):
    # Resample the render onto the target's grid: scale chin-to-sole, centre the body columns.
    s = (t_sole - t_sh) / (r_sole - r_sh)
    rc = np.mean([c for _, _, c in rows_of(rm, r_sh, r_sole) if c])
    tc = np.mean([c for _, _, c in rows_of(tm, t_sh, t_sole) if c])
    img = Image.fromarray((rm * 255).astype(np.uint8))
    img = img.resize((round(rm.shape[1] * s), round(rm.shape[0] * s)), Image.LANCZOS)
    big = np.array(img) > 127
    dy, dx = round(t_sh - r_sh * s), round(tc - rc * s)
    r = np.zeros_like(tm)
    ys0, xs0 = max(0, -dy), max(0, -dx)
    ys1, xs1 = min(big.shape[0], tm.shape[0] - dy), min(big.shape[1], tm.shape[1] - dx)
    r[ys0 + dy : ys1 + dy, xs0 + dx : xs1 + dx] = big[ys0:ys1, xs0:xs1]
    band = np.zeros_like(tm)
    band[t_sh : t_sole + 1] = True
    a, b = r & band, tm & band
    iou = (a & b).sum() / max(1, (a | b).sum())
    rw, tw = rows_of(r, t_sh, t_sole), rows_of(tm, t_sh, t_sole)
    n = t_sole - t_sh
    worst = {"outer": (0.0, 0), "body": (0.0, 0)}
    for i in range(1, 10):
        y = int(i * 0.1 * n)
        for k, idx in (("outer", 0), ("body", 1)):
            if tw[y][idx] > 0:
                e = abs(rw[y][idx] - tw[y][idx]) / tw[y][idx]
                if e > worst[k][0]:
                    worst[k] = (e, i)
    if "--verbose" in sys.argv:
        for i in range(1, 10):
            y = int(i * 0.1 * n)
            print(f"{i * 10:3d}% outer t {tw[y][0]:4d} r {rw[y][0]:4d}   body t {tw[y][1]:4d} r {rw[y][1]:4d}")
    lr, lt = landmarks(r, t_sh, t_sole), landmarks(tm, t_sh, t_sole)
    dlm = {k: abs(lr[k] - lt[k]) / h_target_px for k in lt}
    return iou, worst, dlm, lt, lr, r


def main():
    args = [a for a in sys.argv[1:] if a != "--verbose"]  # --silhouette stays: the body only, no underwear
    if not args:
        sys.exit(__doc__)
    tm = np.array(Image.open(OUT / "target.png").convert("L")) > 128
    # The chin and the sole are the two rows both silhouettes know: the references' head height is 352 px (README).
    t_sh, t_sole = int(np.where(tm.any(1))[0].min() + TARGET_H_PX), int(np.where(tm.any(1))[0].max())
    if args[0] == "--self":
        rm, r_sh, r_sole = tm, t_sh, t_sole
    else:
        body = args[0]
        sil = "--silhouette" in args
        height = next((a for a in args[1:] if not a.startswith("--")), None)
        svg = OUT / f"{body}-{'silhouette' if sil else 'underwear'}.svg"
        cmd = ["node", "harness/franzi/underwear.ts", body, str(svg), height or "-"] + (["silhouette"] if sil else [])
        subprocess.run(cmd, check=True)
        subprocess.run([sys.executable, "harness/svg2png.py", str(svg), str(svg.with_suffix(".png")), "--scale", "2"], check=True)
        meta = json.loads(svg.with_suffix(".json").read_text())
        png = svg.with_suffix(".png")
        scale = Image.open(png).size[0] / meta["canvas_w"]
        rm, r_sh, r_sole = silhouette(png, round(meta["chin_y"] * scale))
    iou, worst, dlm, lt, lr, r = compare(rm, r_sh, r_sole, tm, t_sh, t_sole, TARGET_H_PX)
    # Overlay for the eye: target in blue, render in red, both in dark purple.
    ov = np.full(tm.shape + (3,), 255, np.uint8)
    ov[tm & ~r] = (40, 90, 230)
    ov[r & ~tm] = (230, 50, 50)
    ov[r & tm] = (70, 40, 90)
    name = "target" if args[0] == "--self" else args[0] + ("-silhouette" if "--silhouette" in args else "")
    Image.fromarray(ov).crop((250, 0, 1050, 2440)).resize((400, 1220)).save(OUT / f"{name}-overlay.png")
    ok_w = worst["outer"][0] <= WIDTH_TOL and worst["body"][0] <= WIDTH_TOL
    ok_l = all(v <= LANDMARK_TOL_H for v in dlm.values())
    print(f"IoU {iou:.3f} (min {IOU_MIN})  {'ok' if iou >= IOU_MIN else 'FAIL'}")
    for k, (e, i) in worst.items():
        print(f"worst {k} width error {e:.1%} at {i * 10}% of chin-to-sole (max {WIDTH_TOL:.0%})")
    if "--verbose" in sys.argv:
        print("landmark rows target", lt, "render", lr, "shoulder rows", t_sh, r_sh, "sole", t_sole, r_sole)
    print("landmark error in H: " + ", ".join(f"{k} {v:.3f}" for k, v in dlm.items()) + f" (max {LANDMARK_TOL_H})")
    passed = iou >= IOU_MIN and ok_w and ok_l
    print("G0 PASS" if passed else "G0 FAIL")
    sys.exit(0 if passed else 1)


main()
