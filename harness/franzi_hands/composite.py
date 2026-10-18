"""Edit each hand close-up onto the full-body reference's hands, to compare which one to trace.

    ./harness/run.sh harness/franzi_hands/composite.py

The full-body reference (ref 04) has both hands hanging, relaxed, about 170 px from wrist to fingertip, too small to trace. The four close-ups
in ref/franzi/hands/ (1008 x 1792, not registered to it) are larger. For each candidate this script
  1. orients it for a hanging arm (the relaxed hand as it is; the open palm and the fist rotated half a turn so the fingers point down),
  2. finds its wrist (the narrowest row of the forearm above the hand) and its fingertip (the lowest row),
  3. scales it so that its wrist-to-fingertip length equals the reference's, and puts its wrist centre on the reference's,
  4. clears the reference's hand below the wrist and draws the candidate's hand from its wrist down in its place, blending 10 px across the join,
     and mirrors the same for the other hand.
The pointing close-up has no wrist (it is a foreshortened hand pointing at the camera), so it is left out.

Writes out/franzi/hands-compare.png (original, then each candidate, both hands, 2x) and prints each candidate's measured proportions
against the reference's: wrist width, hand width, hand length.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

OUT = Path("out/franzi")
ref = Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")
A = np.array(ref)[..., 3] > 128
CX = 668.2


def rows_width(mask, y0, y1):
    w = []
    for y in range(y0, y1):
        xs = np.nonzero(mask[y])[0]
        w.append((y, int(xs.min()), int(xs.max())) if len(xs) else (y, 0, -1))
    return w


# --- the reference's left hand (viewer's left): the arm is separated from the thigh by a gap of page, x under 462
arm = np.zeros_like(A)
arm[1090:1350, :462] = A[1090:1350, :462]
lab, _ = ndimage.label(arm)
arm = lab == lab[1200, 420]
# the right arm (viewer's right) has its own mask: the reference is not exactly symmetric about the centre line, and clearing by the mirrored
# left arm left fragments of the right hand's fingertips
armR = np.zeros_like(A)
armR[1090:1350, 875:] = A[1090:1350, 875:]
labR, _ = ndimage.label(armR)
armR = labR == labR[1200, 920]
prof = rows_width(arm, 1090, 1350)
ws = np.array([r - l + 1 for _, l, r in prof])
# the wrist: the narrowest row between 1140 and 1200 (the forearm narrows to the wrist and then the hand widens)
wr = int(np.argmin(ws[50:110])) + 50
wrist_y = 1090 + wr
wrist_w = int(ws[wr])
wrist_cx = (prof[wr][1] + prof[wr][2]) / 2
tip_y = int(np.nonzero(arm.any(1))[0].max())
hand_w = int(ws[wr:].max())
print(f"reference hand: wrist row {wrist_y}, wrist width {wrist_w}, centre x {wrist_cx:.0f}, fingertip row {tip_y}, length {tip_y - wrist_y}, widest {hand_w}")


def candidate(name, rot180):
    im = Image.open(f"ref/franzi/hands/{name}.png").convert("RGBA")
    if rot180:
        im = im.rotate(180)
    a = np.array(im)[..., 3] > 128
    ys = np.nonzero(a.any(1))[0]
    return im, a, int(ys.min()), int(ys.max())


def measure(a, rot180):
    """Wrist row, wrist width, wrist centre x, fingertip row, widest hand row width, in the candidate's pixels."""
    prof = rows_width(a, 0, a.shape[0])
    wd = np.array([r - l + 1 if r >= l else 0 for _, l, r in prof])
    ys = np.nonzero(a.any(1))[0]
    top, bottom = int(ys.min()), int(ys.max())
    if rot180:
        # fingers down, forearm above: search the forearm (top part) for the narrowest row before the hand widens
        lo, hi = top + 30, top + int(0.5 * (bottom - top))
    else:
        lo, hi = top + 40, top + int(0.5 * (bottom - top))
    return prof, wd, top, bottom, (lo, hi)


CANDS = [("relaxed", False), ("open-palm", True), ("fist", True)]
results = []
for name, rot in CANDS:
    im, a, top, bottom = candidate(name, rot)
    prof, wd, top, bottom, (lo, hi) = measure(a, rot)
    # the wrist is the narrowest row of the forearm; for the relaxed hand the forearm is its top rows (the hand widens below)
    if name == "relaxed":
        rng = range(top + 20, top + 420)
    else:
        rng = range(top + 20, top + int(0.45 * (bottom - top)))
    wy = min(rng, key=lambda y: wd[y] if wd[y] > 0 else 10**6)
    if name == "relaxed":
        wy = 250  # the close-up is cut mid-forearm and the forearm has no narrowing, so the wrist is where the hand starts to widen (width 331 at row 240, 348 at 300)
    # for open palm and fist (forearm first after rotation) the narrowest row sits in the forearm just above the palm's widening
    wl, wr_ = prof[wy][1], prof[wy][2]
    ww = wr_ - wl + 1
    length = bottom - wy
    s = (tip_y - wrist_y) / length
    widest = int(wd[wy:].max())
    print(f"{name:10s}: wrist row {wy}, wrist width {ww}, fingertip row {bottom}, length {length}, widest {widest}   scale to the reference {s:.3f}; scaled wrist {ww * s:.0f} (ref {wrist_w}), widest {widest * s:.0f} (ref {hand_w})")
    results.append((name, im, wy, (wl + wr_) / 2, s))


def paste_hand(base, name, im, wy, wcx, s, mirror):
    """Clear the reference's hand below its wrist and draw the candidate's, wrist centre on wrist centre."""
    out = base.copy()
    arr = np.array(out)
    if mirror:
        cx_w = 2 * CX - wrist_cx
        x0, x1 = int(2 * CX - 470), int(2 * CX - 370)
    else:
        cx_w = wrist_cx
        x0, x1 = 370, 470
    # clear the hand: the rows below the wrist, only the arm's own columns (not the thigh)
    clear = np.zeros(A.shape, bool)
    clear[wrist_y + 4 : 1352, x0 - 20 : x1 + 20] = True
    ar = np.zeros(A.shape, bool)
    ar[wrist_y + 4 : 1352, :] = (arm if not mirror else arm[:, ::-1][:, :])[wrist_y + 4 : 1352, :] if False else False
    src = armR if mirror else arm
    hand_mask = np.zeros(A.shape, bool)
    hand_mask[wrist_y + 4 : 1352] = ndimage.binary_dilation(src, iterations=5)[wrist_y + 4 : 1352]
    arr[hand_mask & clear] = (0, 0, 0, 0)
    base2 = Image.fromarray(arr)
    # scale the candidate, mirror it if needed, and place its wrist centre on the reference's
    w, h = im.size
    sc = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    if mirror:
        sc = sc.transpose(Image.FLIP_LEFT_RIGHT)
        px = (w * s) - wcx * s  # the wrist centre after the flip
    else:
        px = wcx * s
    ox = round(cx_w - px)
    oy = round(wrist_y - wy * s)
    # keep from the wrist down, blended over 10 px so the join is not a hard line
    layer = Image.new("RGBA", base2.size, (0, 0, 0, 0))
    layer.paste(sc, (ox, oy), sc)
    la = np.array(layer)
    fade = np.clip((np.arange(la.shape[0]) - (wrist_y - 4)) / 10.0, 0, 1)[:, None]
    la[..., 3] = (la[..., 3] * fade).astype(np.uint8)
    la[: wrist_y - 4, :, 3] = 0
    res = base2.copy()
    res.alpha_composite(Image.fromarray(la))
    return res


def white(img):
    bg = Image.new("RGBA", img.size, "white")
    bg.alpha_composite(img)
    return bg.convert("RGB")


BOXL, BOXR = (340, 1080, 560, 1400), (776, 1080, 996, 1400)


def pair(img):
    w = white(img)
    l, r = w.crop(BOXL), w.crop(BOXR)
    z = 2
    out = Image.new("RGB", (l.width * z * 2 + 10, l.height * z), "white")
    out.paste(l.resize((l.width * z, l.height * z), Image.LANCZOS), (0, 0))
    out.paste(r.resize((r.width * z, r.height * z), Image.LANCZOS), (l.width * z + 10, 0))
    return out


tiles = [("original (full-body reference)", pair(ref))]
for name, im, wy, wcx, s in results:
    e = paste_hand(ref, name, im, wy, wcx, s, False)
    e = paste_hand(e, name, im, wy, wcx, s, True)
    e.save(OUT / f"hands-edit-{name}.png")
    tiles.append((f"{name} close-up scaled in" + (" (rotated to hang)" if name != "relaxed" else ""), pair(e)))

pad = 40
W = max(t.width for _, t in tiles)
sheet = Image.new("RGB", (W * 2 + 20, (tiles[0][1].height + pad) * 2), "white")
d = ImageDraw.Draw(sheet)
for i, (label, t) in enumerate(tiles):
    x, y = (i % 2) * (W + 20), (i // 2) * (t.height + pad)
    d.text((x + 6, y + 10), label, fill=(0, 0, 0))
    sheet.paste(t, (x, y + pad))
sheet.save(OUT / "hands-compare.png")
print("wrote out/franzi/hands-compare.png", sheet.size)
