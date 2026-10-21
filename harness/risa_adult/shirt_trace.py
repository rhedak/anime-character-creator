"""Risa's long-sleeved shirt, from the blouse-and-briefs reference (ref/risa-adult/06-blouse-bikini.png and its `white-collared-shirt` layer).

    PYTHONPATH=.claude/skills/trace-reference ./harness/run.sh harness/risa_adult/shirt_trace.py [view]

The lesson of docs/risa-plan.md holds: trace nothing below the chin off a reference whose body is not ours. So the shirt's torso and sleeves are not traced; they are built in the garment
code from our own body's tables (the torso's side, the arm's two edges) with an ease. What the reference gives is what the body cannot: the hem's curve, the collar's lines, the placket,
the buttons and the cuffs, each as lines read off the picture (a valley detector on the luminance, as strands_auto.py and skirt_trace.py) and mapped onto our body landmark to landmark
(`to_body` in registration.py). Registered to the bikini's grid by the irises first (registration.py).

`view` writes out/risa_adult/shirt-view.png: the lines over the reference. The bare run writes ts/src/body-adult-shirt-data.ts.
"""

import sys
from collections import deque

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, ".claude/skills/trace-reference")
sys.path.insert(0, "harness/risa_adult")
import trace_lib as tl  # noqa: E402
from registration import Registration, to_body  # noqa: E402

REG = Registration("ref/risa-adult/06-blouse-bikini.png")
img = np.array(REG.register(Image.open("ref/risa-adult/06-blouse-bikini.png").convert("RGB"))).astype(float)
lum = img.mean(2)
shirt = np.array(REG.register(Image.open("ref/risa-adult/segments/06-blouse-bikini/white-collared-shirt.png").convert("RGBA"), Image.BILINEAR))[..., 3] > 200
Hh, Ww = lum.shape

SIG = 1.1
Lxx, Lyy, Lxy = (ndimage.gaussian_filter(lum, SIG, order=o) for o in ((0, 2), (2, 0), (1, 1)))
tr, det = Lxx + Lyy, Lxx * Lyy - Lxy**2
lam = tr / 2 + np.sqrt(np.maximum(tr**2 / 4 - det, 0))
nx, ny = Lxy, lam - Lxx
nn = np.maximum(np.hypot(nx, ny), 1e-9)
nx, ny = nx / nn, ny / nn
resp = lam * SIG**2
yy, xx = np.mgrid[0:Hh, 0:Ww].astype(float)
nms = (resp >= ndimage.map_coordinates(resp, [yy + ny, xx + nx], order=1)) & (resp >= ndimage.map_coordinates(resp, [yy - ny, xx - nx], order=1))
inner = ndimage.binary_erosion(shirt, iterations=2)
cand = nms & (resp > 2.5) & inner
lab, n = ndimage.label(cand, structure=np.ones((3, 3)))
mx = ndimage.maximum(resp, lab, range(1, n + 1))
keep = np.zeros(n + 1, bool)
keep[1:] = np.asarray(mx) > 6.0
ridge = keep[lab] & cand

NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def longest_paths(mask, min_len):
    out = []
    lab_, k = ndimage.label(mask, structure=np.ones((3, 3)))
    todo = [[(int(y), int(x)) for y, x in zip(*np.nonzero(lab_ == i))] for i in range(1, k + 1)]
    while todo:
        px = todo.pop()
        if len(px) < min_len:
            continue
        S_ = set(px)

        def bfs(src):
            par, q = {src: None}, deque([src])
            last = src
            while q:
                u = q.popleft()
                last = u
                for dy, dx in NB:
                    v = (u[0] + dy, u[1] + dx)
                    if v in S_ and v not in par:
                        par[v] = u
                        q.append(v)
            return last, par

        a, _ = bfs(px[0])
        b, par = bfs(a)
        path = []
        while b is not None:
            path.append(b)
            b = par[b]
        if len(path) >= min_len:
            out.append([(x, y) for y, x in path])
        halo = {(y + dy, x + dx) for y, x in path for dy in (-1, 0, 1) for dx in (-1, 0, 1)}
        rest = [p for p in px if p not in halo]
        if rest:
            sub = np.zeros(mask.shape, bool)
            for y, x in rest:
                sub[y, x] = True
            l2, k2 = ndimage.label(sub, structure=np.ones((3, 3)))
            todo.extend([[(int(y), int(x)) for y, x in zip(*np.nonzero(l2 == i))] for i in range(1, k2 + 1)])
    return out


def box(x0, y0, x1, y1):
    b = np.zeros((Hh, Ww), bool)
    b[y0:y1, x0:x1] = True
    return b


# The zones of the structural lines (reference px, the bikini's grid); the folds of the cloth, the shading creases, are not structure and stay out.
ZONES = {
    "collar": (588, 436, 790, 566),  # the collar's wings and its stand, the button on the stand
    "placket": (648, 566, 700, 1100),  # the two long lines of the button band
    "hem": (468, 1020, 842, 1135),  # the curved hem and the shirttail's front edge
    "cuff_l": (408, 1085, 500, 1150),
    "cuff_r": (838, 1085, 944, 1150),
}


def lines_in(zone, min_len, smooth_sig=1.5):
    m = ridge & box(*zone)
    out = []
    for p in longest_paths(m, min_len):
        a = np.array(p, float)
        if len(a) > 6:
            a = np.stack([ndimage.gaussian_filter1d(a[:, j], smooth_sig, mode="nearest") for j in (0, 1)], 1)
        out.append(a)
    return out


# buttons: the small rings, found as the compact ridge components of the placket's band that are round (their box about as wide as tall, under 20 px)
BUTTONS = []
band = ridge & box(640, 480, 705, 1000)
lab_b, nb = ndimage.label(band, structure=np.ones((3, 3)))
for i in range(1, nb + 1):
    ys_, xs_ = np.nonzero(lab_b == i)
    h, w_ = np.ptp(ys_) + 1, np.ptp(xs_) + 1
    if 8 <= h <= 20 and 8 <= w_ <= 20 and abs(h - w_) <= 4:
        BUTTONS.append((float(xs_.mean()), float(ys_.mean()), (h + w_) / 4.0))
BUTTONS.sort(key=lambda b: b[1])

if len(sys.argv) > 1 and sys.argv[1] == "view":
    box_ = (400, 430, 950, 1180)
    z = 2
    base = Image.fromarray(img.astype(np.uint8)).crop(box_).resize(((box_[2] - box_[0]) * z, (box_[3] - box_[1]) * z), Image.LANCZOS)
    d = ImageDraw.Draw(base)
    cols = [(255, 40, 40), (0, 160, 255), (0, 200, 90), (255, 140, 0), (200, 0, 255)]
    for (name, zone), col in zip(ZONES.items(), cols):
        for ln in lines_in(zone, 12 if name != "placket" else 80):
            d.line([((x - box_[0]) * z, (y - box_[1]) * z) for x, y in ln], fill=col, width=2)
        d.rectangle([(zone[0] - box_[0]) * z, (zone[1] - box_[1]) * z, (zone[2] - box_[0]) * z, (zone[3] - box_[1]) * z], outline=col)
    for bx, by, br in BUTTONS:
        d.ellipse([(bx - br - box_[0]) * z, (by - br - box_[1]) * z, (bx + br - box_[0]) * z, (by + br - box_[1]) * z], outline=(255, 255, 0), width=2)
    base.save("out/risa_adult/shirt-view.png")
    print("buttons", [(round(a), round(b), round(c, 1)) for a, b, c in BUTTONS], "wrote out/risa_adult/shirt-view.png")
    sys.exit(0)


# ---- the collar: points read off the gridded zoom of the reference (`$TMPDIR/grid.py`-style, 8x, reference px on the bikini's grid). A closed outline: the left wing's outer edge down
# to its tip and back up its lower edge to the stand, over the stand, the right wing's lower edge to its tip and its outer edge up, then the neck opening back along the collar's
# inner edge. The wings are sharp; the neck's edge is a curve, so it is a Catmull-Rom through its points.
LEFT_OUTER = [(641, 450), (632, 457), (625, 470), (617, 484), (614, 492), (617, 505), (622, 520), (626, 535), (630, 549)]
LEFT_LOWER = [(640, 543), (650, 535), (656, 528), (664, 520), (669, 511), (671, 503)]
STAND_TOP = [(671, 503), (679, 505), (688, 503)]
RIGHT_LOWER = [(690, 510), (696, 517), (706, 526), (718, 538), (730, 550)]
RIGHT_OUTER = [(742, 535), (748, 520), (752, 500), (753, 490), (742, 478), (735, 467), (727, 456), (725, 450)]
NECK = [(725, 452), (725, 466), (715, 478), (700, 488), (688, 498), (679, 503), (670, 498), (660, 490), (650, 479), (642, 468), (641, 451)]
STAND_LINES = []  # the stand's sides are the top of the band's two lines now
STAND_BUTTON = (679.0, 520.0, 6.0)  # a little below the collar's V (it was at 512, in the V), between the curved tops of the band's lines


def catmull(pts, n=6):
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2 * p[i][j]) + (-p[i - 1][j] + p[i + 1][j]) * t + (2 * p[i - 1][j] - 5 * p[i][j] + 4 * p[i + 1][j] - p[i + 2][j]) * t**2 + (-p[i - 1][j] + 3 * p[i][j] - 3 * p[i + 1][j] + p[i + 2][j]) * t**3) for j in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


# The collar is symmetric: the viewer's right side is the one traced well (the owner), so the left is its mirror about the collar's centre (x 679, the V and the stand's button).
CX0 = 679.0
mirror = lambda pts: [(2 * CX0 - x, y) for x, y in pts]  # noqa: E731
LEFT_OUTER = mirror(RIGHT_OUTER[::-1])  # from the top down to the tip
LEFT_LOWER = mirror(RIGHT_LOWER[::-1])  # from the tip in toward the stand
NECK_RIGHT = [p for p in NECK if p[0] >= CX0]  # the neck's opening from the right top down to the V
NECK = NECK_RIGHT + mirror(NECK_RIGHT[::-1])[1:]
collar = LEFT_OUTER + LEFT_LOWER + STAND_TOP[1:2] + RIGHT_LOWER + RIGHT_OUTER + catmull(NECK)

# One centre line, from the middle of the neck to the opening below the last button: the reference's drifts (the collar's V is at x 679, the buttons run from 675 down to 666), and this figure is
# symmetric about its centre, so the collar, its stand and its button are moved onto the centre line (668.2) and the buttons and the band's lines are put on it (below).
AXIS = 668.2
SHIFT = AXIS - 679.0  # the collar's V and the stand's button are at 679
collar = [(x + SHIFT, y) for x, y in collar]
collar_body = [to_body(x, y) for x, y in collar]
neck_body = [to_body(x + SHIFT, y) for x, y in catmull(NECK)]  # the collar's inner edge: the shirt's own neckline runs along it, under the collar

# ---- the hem: the shirt layer's lowest row in each column of the torso (the sleeves are outside 497 and 846), simplified to a pixel; the V of the shirttails' opening is in it
cols = list(range(497, 846))
hem_px = []
for x in cols:
    rows = np.nonzero(shirt[:1150, x])[0]
    rows = rows[rows > 960]
    hem_px.append((x, int(rows.max()) if len(rows) else None))
hem_px = [(x, y) for x, y in hem_px if y is not None]
keep_i = tl.simplify([(x, y) for x, y in hem_px], 1.0)
hem_px = [hem_px[i] for i in keep_i]
hem_body = [to_body(x, y) for x, y in hem_px]
# the V of the shirttails' opening, symmetric about the centre line: its apex, where the opening begins below the last button, and its two feet at the hem
apex = min(d for v, d in hem_body if abs(v) < 0.07)
foot = max(d for v, d in hem_body if abs(v) < 0.07)
hem_body = [p for p in hem_body if p[0] < -0.07] + [(-0.065, foot), (0.0, apex), (0.065, foot)] + [p for p in hem_body if p[0] > 0.07]

# ---- the placket's two lines, the buttons, the cuffs
plk = [ln for ln in lines_in(ZONES["placket"], 80) if len(ln) > 80]
plk.sort(key=lambda a: a[:, 0].mean())  # left to right: the button band's two edges (a third, shorter line is the right shirttail's edge and is dropped here)
band_lines = plk[:2] if len(plk) >= 2 else plk
GAP = 11.0  # half the distance between the button band's two lines: 661 and 683 in the reference
y_to = 1005  # to the V's apex; below it the two lines run on as the V's edges
# Each side is ONE line: the curve around the top button (from the stand's top, bowing out) running into the band's straight line down to the V (the owner: the curved lines around the top
# button and the straight lines around the buttons below it meet).
BTN_Y = 520.0  # the stand button's centre row (a little below the collar's V, which was where it sat before)
ARC_R = GAP  # the arc round the button has the band's half-width as its radius, so each straight line runs tangent into it at the button's centre row
placket_body = []
for sgn in (-1, 1):
    # from the arc's top end (45 degrees above the button's centre row, under the collar), round the button's side down to its centre row, then straight down to the V
    arc = [(AXIS + sgn * ARC_R * np.cos(np.radians(t)), BTN_Y - ARC_R * np.sin(np.radians(t))) for t in range(45, -1, -5)]
    pts_px = arc + [(AXIS + sgn * GAP, float(y_to))]
    placket_body.append([to_body(x, y) for x, y in pts_px])
mid = lambda y: float(np.mean([np.polyval(p, y) for p in polys]))  # noqa: E731
buttons = [b for b in BUTTONS if (b[1] >= 590 and 660 <= b[0] <= 685)]
buttons_body = [(*to_body(AXIS, by), br / 352.0) for bx, by, br in buttons]  # on the centre line, between the band's two lines
stand_btn = (*to_body(AXIS, STAND_BUTTON[1]), STAND_BUTTON[2] / 352.0)

from pathlib import Path  # noqa: E402

# ---- the ribbon (the bow at the collar), from 06's `blue-ribbon` layer: points read off an 12x gridded zoom of its right half (reference px on the bikini's grid), the left its mirror about the
# collar's centre (x 679), like the collar. Pieces, back to front: the band that tucks up behind the collar, the tail, the loop with its slit, the knot over them all.
RIB_BACK = [(687, 527), (700, 512), (706, 522), (697, 528), (690, 531)]
RIB_TAIL = [(687, 543), (690, 560), (693, 582), (697, 606), (700, 630), (698, 656), (714, 650), (712, 630), (708, 606), (704, 582), (699, 562), (695, 552)]
RIB_LOOP = [(687, 530), (698, 531), (708, 537), (718, 545), (727, 554), (734, 561), (735, 566), (731, 570), (727, 578), (720, 583), (715, 582), (708, 575), (702, 566), (696, 556), (691, 547), (687, 540)]
RIB_SLIT = [(705, 551), (712, 556), (719, 564), (720, 568), (716, 565), (707, 556)]
RIB_KNOT = [(672, 526), (686, 526), (687, 543), (672, 543)]  # symmetric: 672 to 686 about 679


def side(poly, sgn):
    """The right-hand polygon (sgn 1) or its mirror about the collar's centre (sgn -1), in body coordinates, the centre line shifted onto the body's (SHIFT)."""
    pts = poly if sgn > 0 else [(2 * 679.0 - x, y) for x, y in poly][::-1]
    return [to_body(x + SHIFT, y) for x, y in pts]


def ribbon_ts():
    out = []
    for name, poly, doc in (
        ("RIBBON_BACK", RIB_BACK, "The band that tucks up behind the collar, one per side."),
        ("RIBBON_TAIL", RIB_TAIL, "The tails that hang down over the placket, one per side."),
        ("RIBBON_LOOP", RIB_LOOP, "The loops of the bow, one per side."),
        ("RIBBON_SLIT", RIB_SLIT, "The slit in each loop where the cloth shows through."),
    ):
        out.append(f"/** {doc} The viewer's left, then right. */\nexport const {name}: readonly (readonly Pt[])[] = [{pts(side(poly, -1))}, {pts(side(poly, 1))}];\n")
    knot = [to_body(x + SHIFT, y) for x, y in RIB_KNOT]
    out.append(f"/** The knot over the loops and tails. */\nexport const RIBBON_KNOT: readonly Pt[] = {pts(knot)};\n")
    return "\n".join(out)


def pts(a, nd=4):
    return "[" + ", ".join(f"[{p[0]:.{nd}f}, {p[1]:.{nd}f}]" for p in a) + "]"


Path("ts/src/body-adult-shirt-data.ts").write_text(
    "// Generated by harness/risa_adult/shirt_trace.py from the shirt of ref/risa-adult/06-blouse-bikini.png. Do not edit by hand.\n"
    "// Points are [x, d]: x in head heights from the body's centre line (negative on the viewer's left), d in head heights below the chin, mapped from the reference landmark to landmark onto our\n"
    "// body (registration.py). Only what the body cannot give: the torso and the sleeves are built from our own body's tables in body-adult-garments.ts.\n\n"
    "export type Pt = readonly [number, number];\n\n"
    f"/** The collar: a closed outline, the wings' sharp tips and the neck's curve. */\nexport const SHIRT_COLLAR: readonly Pt[] = {pts(collar_body)};\n\n"
    f"/** The collar's inner edge, the neck's opening: the shirt's neckline, as the viewer reads it, from the left top, down to the V at the stand and up the right. */\nexport const SHIRT_NECK: readonly Pt[] = {pts(neck_body)};\n\n"
    f"/** The two edges of the collar's stand down to the knot of the ribbon. */\nexport const SHIRT_STAND: readonly (readonly Pt[])[] = [{', '.join(pts([to_body(x + SHIFT, y) for x, y in ln]) for ln in STAND_LINES)}];\n\n"
    f"/** The stand's button: [x, d, radius in head heights]. */\nexport const SHIRT_STAND_BUTTON: readonly [number, number, number] = [{stand_btn[0]:.4f}, {stand_btn[1]:.4f}, {stand_btn[2]:.4f}];\n\n"
    f"/** The hem along the torso, left to right: the shirt's lowest edge column by column, the V of the shirttails' opening in it. */\nexport const SHIRT_HEM: readonly Pt[] = {pts(hem_body)};\n\n"
    f"/** The two lines of the button band, from below the collar to the hem. */\nexport const SHIRT_PLACKET: readonly (readonly Pt[])[] = [{', '.join(pts(a) for a in placket_body)}];\n\n"
    f"/** The buttons below the ribbon: [x, d, radius in head heights]. */\nexport const SHIRT_BUTTONS: readonly (readonly [number, number, number])[] = [{', '.join(f'[{a:.4f}, {b:.4f}, {c:.4f}]' for a, b, c in buttons_body)}];\n\n"
    + ribbon_ts()
)
print("collar", len(collar_body), "hem", len(hem_body), "placket lines", len(placket_body), "buttons", len(buttons_body), "wrote ts/src/body-adult-shirt-data.ts")
