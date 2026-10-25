"""The silhouette gate of the Risa polish campaign (docs/risa-polish-plan.md, stage 1): Risa's body outline against her target from the bikini image.

    ./harness/run.sh harness/risa_adult/gate.py ['{"bust":-0.18}'] [--verbose]    renders body_outline.ts with the overrides first
    ./harness/run.sh harness/risa_adult/gate.py --self [--stretch 1.08]           the target against itself (must pass), or widened (must fail)

Run target.py first. Unlike Franzi's gate (harness/franzi/gate.py) this one registers by the head, not chin to sole: the bikini image ends at mid-thigh, and the head is already
on the reference's grid (compare_head.py's mapping: a head height of 352 px, the centre line at 668.2, the chin at 434). Both silhouettes are measured from the neck's top
(0.12 H below the chin) to the image's lower edge, with the target's unknown zone (target-unknown.png) counted neither way. The thresholds are Franzi's, fixed before any
shape is tuned:

    IoU                      at least 0.93
    widths every 0.1 H       0.3 to 3.0 H, the outer extent and the run through the centre line (the torso; below the crotch, each leg), each within 5%
    landmark heights         waist, hip, crotch, each within 0.05 H

The reference's body is centred 7 to 12 px right of the head's centre line (her head is turned; ours was made straight, `body-adult-cut-level.ts`), so ours is shifted
sideways onto the target's body centre (the mean midpoint of the outer extent, 1.0 to 3.0 H) before anything is compared, as Franzi's gate centres the body columns; the shift
is printed. A width is skipped where one of its edges lies in the unknown zone, or where the runs do not separate the same way in both (an arm merged with the torso in one and not the
other is a difference of shape the IoU and the outer width already see). The arms' widths are printed but not gated. Writes out/risa_adult/gate-overlay.png (the target in blue,
ours in red, both in dark purple, the unknown zone grey). Exit status 0 on pass, 1 on a fail. Change a threshold only with a note in the plan and the owner's say.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path("out/risa_adult")
IOU_MIN, WIDTH_TOL, LANDMARK_TOL_H = 0.93, 0.05, 0.05
CHIN, H, CX = 434.0, 352.0, 668.2
TOP_D, ROWS_D = 0.12, [round(0.3 + 0.1 * i, 1) for i in range(28)]
EDGE_PX = 2  # an edge within this many px of the unknown zone is not measured


def render(overrides):
    svg = OUT / "gate-body.svg"
    subprocess.run(["node", "harness/risa_adult/body_outline.ts", str(svg), overrides], check=True, stderr=subprocess.DEVNULL)
    meta = json.loads(svg.with_suffix(".json").read_text())
    scale = H / (2 * meta["head_r"])
    png = svg.with_suffix(".png")
    subprocess.run([sys.executable, "harness/svg2png.py", str(svg), str(png), "--scale", f"{scale:.5f}"], check=True, stdout=subprocess.DEVNULL)
    im = Image.open(png).convert("RGBA")
    ox, oy = round((meta["canvas_w"] / 2) * scale - CX), round(meta["chin_y"] * scale - CHIN)
    return np.array(im.crop((ox, oy, ox + 1312, oy + 1504)))[..., 3] > 127


def runs(row):
    d = np.diff(np.concatenate([[0], row.astype(int), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def body_centre(m):
    mids = []
    for d in np.arange(1.0, 3.0, 0.05):
        y = int(round(CHIN + d * H))
        rs = runs(m[y]) if y < m.shape[0] else []
        if rs:
            mids.append((rs[0][0] + rs[-1][1]) / 2)
    return float(np.mean(mids))


def measure(m, unk, y):
    """Outer extent, the centre run (or each leg's) and the arms at row y, each as a width or None where an edge is unknown."""
    rs = runs(m[y])
    if not rs:
        return None
    near = ndimage.binary_dilation(unk[y - 1 : y + 2], iterations=EDGE_PX)[1]
    ok = lambda a, b: not (near[max(0, a - 1)] or near[min(len(near) - 1, b)])  # the pixel just outside each end
    w = lambda run: (run[1] - run[0]) if ok(*run) else None
    centre = [r for r in rs if r[0] <= CX < r[1]]
    out = {"n": len(rs), "outer": (rs[-1][1] - rs[0][0]) if ok(rs[0][0], rs[-1][1]) else None}
    if centre:
        c = centre[0]
        out["torso"] = w(c)
        others = [r for r in rs if r != c]
    else:  # the legs: the runs either side of the gap at the centre line
        left = [r for r in rs if r[1] <= CX]
        right = [r for r in rs if r[0] > CX]
        out["legL"] = w(left[-1]) if left else None
        out["legR"] = w(right[0]) if right else None
        others = left[:-1] + right[1:]
    out["armL"] = w(others[0]) if others and others[0][1] <= CX else None
    out["armR"] = w(others[-1]) if others and others[-1][0] > CX else None
    return out


def landmarks(m):
    """Waist (the narrowest torso, 1.0 to 1.7 H), hip (the widest torso below it, above the crotch), crotch (the first row whose centre is not body), in H below the chin."""
    def torso(y):
        rs = [r for r in runs(m[y]) if r[0] <= CX < r[1]]
        return (rs[0][1] - rs[0][0]) if rs else 0

    ys = range(int(CHIN + 1.0 * H), int(CHIN + 2.8 * H))
    t = np.array([torso(y) for y in ys], float)
    crotch_i = next(i for i, v in enumerate(t) if v == 0)
    def middle(lo, hi, fn):
        seg = t[lo:hi]
        e = fn(seg)
        return lo + int(np.median(np.where(np.abs(seg - e) <= 0.015 * e)[0]))
    w_hi = int(0.7 * H)  # the waist is looked for in the first 0.7 H (1.0 to 1.7; the target's is at 1.2, its hips widen from 1.3)
    waist = middle(0, w_hi, np.min)
    hip = middle(waist, crotch_i, np.max)
    to_d = lambda i: (ys[0] + i - CHIN) / H
    return {"waist": to_d(waist), "hip": to_d(hip), "crotch": to_d(crotch_i)}


def main():
    global CX
    args = [a for a in sys.argv[1:] if a != "--verbose"]
    tm = np.array(Image.open(OUT / "target.png")) > 127
    unk = np.array(Image.open(OUT / "target-unknown.png")) > 127
    top, bottom = int(CHIN + TOP_D * H), tm.shape[0] - 4
    if args and args[0] == "--self":
        rm = tm.copy()
        if "--stretch" in args:
            s = float(args[args.index("--stretch") + 1])
            img = Image.fromarray((tm * 255).astype(np.uint8))
            wide = np.array(img.resize((round(tm.shape[1] * s), tm.shape[0]), Image.NEAREST)) > 127
            x0 = round(CX * s - CX)
            rm = wide[:, x0 : x0 + tm.shape[1]]
    else:
        rm = render(args[0] if args else "{}")
    tc = body_centre(tm)
    shift = round(tc - body_centre(rm))
    rm = np.roll(rm, shift, axis=1)
    CX = tc  # the centre run and the gap between the legs are found about the body's centre, not the head's
    rm[:top] = False
    band = np.zeros_like(tm)
    band[top:bottom] = True
    a, b = rm & band & ~unk, tm & band & ~unk
    iou = (a & b).sum() / max(1, (a | b).sum())

    worst = (0.0, None, None)
    lines = []
    for d in ROWS_D:
        y = int(round(CHIN + d * H))
        if y >= bottom:
            continue
        mt, mr = measure(tm, unk, y), measure(rm, np.zeros_like(unk), y)
        if mt is None or mr is None:
            continue
        cells = []
        for k in ("outer", "torso", "legL", "legR", "armL", "armR"):
            vt, vr = mt.get(k), mr.get(k)
            if vt is None or vr is None:
                cells.append(f"{k} {'-' if vt is None else vt:>4}/{'-' if vr is None else vr:<4}       ")
                continue
            e = (vr - vt) / vt
            cells.append(f"{k} {vt:>4}/{vr:<4} {e:+6.1%}")
            if k in ("outer", "torso", "legL", "legR") and abs(e) > abs(worst[0]):
                worst = (e, k, d)
        lines.append(f"{d:4.1f} H  " + "  ".join(c for c in cells if not c.startswith(("legL -", "legR -", "torso -/-"))))
    lt, lr = landmarks(tm), landmarks(rm)
    dlm = {k: lr[k] - lt[k] for k in lt}

    ov = np.full(tm.shape + (3,), 255, np.uint8)
    ov[tm & ~rm] = (40, 90, 230)
    ov[rm & ~tm] = (230, 50, 50)
    ov[rm & tm] = (70, 40, 90)
    ov[unk] = (170, 170, 170)
    ov[:top] = 255
    Image.fromarray(ov).crop((280, 400, 1060, 1504)).save(OUT / "gate-overlay.png")

    if "--verbose" in sys.argv:
        print("target/ours px and ours against the target; - is unknown or not separated")
        print("\n".join(lines))
    ok_i, ok_w, ok_l = iou >= IOU_MIN, abs(worst[0]) <= WIDTH_TOL, all(abs(v) <= LANDMARK_TOL_H for v in dlm.values())
    print(f"ours shifted {shift:+d} px onto the target's body centre ({tc:.1f})")
    print(f"IoU {iou:.3f} (min {IOU_MIN})  {'ok' if ok_i else 'FAIL'}")
    print(f"worst width error {worst[0]:+.1%} ({worst[1]} at {worst[2]} H, max {WIDTH_TOL:.0%})  {'ok' if ok_w else 'FAIL'}")
    print("landmarks, ours minus the target in H: " + ", ".join(f"{k} {v:+.3f} (at {lt[k]:.2f})" for k, v in dlm.items()) + f" (max {LANDMARK_TOL_H})  {'ok' if ok_l else 'FAIL'}")
    passed = ok_i and ok_w and ok_l
    print("RISA GATE PASS" if passed else "RISA GATE FAIL")
    sys.exit(0 if passed else 1)


main()
