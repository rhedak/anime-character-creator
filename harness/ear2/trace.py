"""Trace the canon's ear off the sheet, using the owner's crop only as a mask.

The crop is a 4.3x resample of a 76x110 patch, so it carries nothing the sheet
does not, plus the resampler's ringing and a hand-cut alpha edge that clips the
rim at the bottom left. So the boundary comes from the original pixels and the
crop's alpha only says which ink is ear and which is the hair lock beside it.
`place.py` is what put the two in register.

The outer arc is the rightmost ink in each row rather than a radial sweep from
the middle. The ear's attach side runs near vertical and a sweep cannot describe
it, which is the same thing that broke the first reading of Satoko's fall.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "ref"
SHEET = REF / "satoshi-chibi.jpg"

# From place.py: where the crop sits on the sheet, and at what scale.
AT_X, AT_Y, SCALE = 579, 355, 0.132
# From out/trace/chibi.py: the sheet's own head, by the eye-to-chin fit.
CX, EYE_Y, CHIN_Y = 434.0, 380.0, 528.0
R = (CHIN_Y - EYE_Y) / 0.84
CY = EYE_Y - 0.16 * R

INK_SUM = 330
PAD = 6
# Chosen by the two-stroke-width rule below, not by taste.
TOL = 0.080


def _thin(chords: list[float]) -> str:
    """How many edges land under two stroke widths, at each build."""
    import sys

    sys.path.insert(0, str(ROOT / "src"))
    from anime_character_creator import character as C
    from anime_character_creator.skeleton import BUILDS, build_skeleton

    out = []
    for name in ("chibi", "realistic"):
        sk = build_skeleton(heads=BUILDS[name])
        n = sum(1 for c in chords if c * sk.head_r / C._stroke_w(sk) < 2)
        out.append(f"{name[:5]} {n}")
    return ", ".join(out)


def masks() -> tuple[list[list[bool]], int, int, int, int]:
    """Ear ink on the sheet, inside the crop's selection grown by a pixel."""
    crop = Image.open(REF / "satoshi-ear.png")
    w, h = round(crop.width * SCALE), round(crop.height * SCALE)
    sel = crop.getchannel("A").resize((w, h), Image.LANCZOS).point(lambda v: 255 if v > 100 else 0)
    grown = [[False] * (w + 2 * PAD) for _ in range(h + 2 * PAD)]
    s = sel.load()
    for y in range(h):
        for x in range(w):
            if s[x, y]:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        grown[y + PAD + dy][x + PAD + dx] = True

    sheet = Image.open(SHEET).convert("RGB")
    px = sheet.load()
    ox, oy = AT_X - PAD, AT_Y - PAD
    W, H = w + 2 * PAD, h + 2 * PAD
    ink = [
        [grown[y][x] and sum(px[ox + x, oy + y]) < INK_SUM for x in range(W)] for y in range(H)
    ]
    return ink, ox, oy, W, H


def filled(ink: list[list[bool]], W: int, H: int) -> list[list[bool]]:
    """Ink plus whatever it encloses, by flooding the outside and inverting.

    The ear is drawn as a closed ring of line with skin inside it, so the ring
    alone is not the shape: the silhouette is the ring and its contents.
    """
    seen = [[False] * W for _ in range(H)]
    stack = [(x, y) for x in range(W) for y in (0, H - 1) if not ink[y][x]]
    stack += [(x, y) for y in range(H) for x in (0, W - 1) if not ink[y][x]]
    while stack:
        x, y = stack.pop()
        if seen[y][x] or ink[y][x]:
            continue
        seen[y][x] = True
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and not seen[ny][nx] and not ink[ny][nx]:
                stack.append((nx, ny))
    return [[ink[y][x] or not seen[y][x] for x in range(W)] for y in range(H)]


def to_head(x: float, y: float, ox: int, oy: int) -> tuple[float, float]:
    """Sheet pixel to head radii, origin the head centre, y down."""
    return ((ox + x - CX) / R, (oy + y - CY) / R)


def simplify(pts: list[tuple[float, float]], tol: float) -> list[int]:
    def walk(lo: int, hi: int) -> list[int]:
        if hi - lo < 2:
            return [lo]
        ax, ay = pts[lo]
        bx, by = pts[hi]
        dx, dy = bx - ax, by - ay
        n = math.hypot(dx, dy) or 1e-9
        worst, at = -1.0, lo
        for i in range(lo + 1, hi):
            px, py = pts[i]
            d = abs(dx * (ay - py) - (ax - px) * dy) / n
            if d > worst:
                worst, at = d, i
        return [lo] if worst <= tol else walk(lo, at) + walk(at, hi)

    return walk(0, len(pts) - 1) + [len(pts) - 1]


def fit(pts: list[tuple[float, float]], keep: list[int]):
    """Least-squares control per span, endpoints pinned.

    Chord-length parameter, and the control clamped into the span's own bounding
    box. Both were learned on the fringe: indexed by sample, a near-vertical run
    piles dozens of points at one x and drags the control sideways until the
    curve leaves the data, and a quadratic never leaves the convex hull of its
    three points, so a control inside the box keeps the curve inside it too.
    """
    segs = []
    for a, b in zip(keep, keep[1:], strict=False):
        p0, p2 = pts[a], pts[b]
        run = [0.0]
        for i in range(a + 1, b + 1):
            run.append(run[-1] + math.dist(pts[i - 1], pts[i]))
        total = run[-1] or 1.0
        nx = ny = den = 0.0
        for i in range(a + 1, b):
            t = run[i - a] / total
            w = 2 * (1 - t) * t
            rx = pts[i][0] - (1 - t) ** 2 * p0[0] - t**2 * p2[0]
            ry = pts[i][1] - (1 - t) ** 2 * p0[1] - t**2 * p2[1]
            nx += w * rx
            ny += w * ry
            den += w * w
        if den > 1e-9:
            c = (nx / den, ny / den)
        else:
            c = ((p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2)
        xs = [q[0] for q in pts[a : b + 1]]
        ys = [q[1] for q in pts[a : b + 1]]
        segs.append(
            ((min(max(c[0], min(xs)), max(xs)), min(max(c[1], min(ys)), max(ys))), p2)
        )
    return pts[keep[0]], segs


def main() -> None:
    ink, ox, oy, W, H = masks()
    sil = filled(ink, W, H)
    rows = [y for y in range(H) if any(sil[y])]
    y0, y1 = rows[0], rows[-1]
    print(f"ear spans {y1 - y0 + 1} sheet rows, {sum(sum(r) for r in sil)} px of silhouette")

    # Attach points: the outer end of the top and bottom rows. The arc has to
    # start and finish on them, since the code welds the ear by closing a chord
    # between exactly these two points, and a chord that does not meet the arc
    # leaves the fill open.
    def span(y: int) -> tuple[int, int]:
        xs = [x for x in range(W) if sil[y][x]]
        return xs[0], xs[-1]

    top = (span(y0)[1], y0)
    bot = (span(y1)[1], y1)

    arc = []
    for y in range(y0, y1 + 1):
        _, right = span(y)
        f = (y - y0) / (y1 - y0)
        chord_x = top[0] + (bot[0] - top[0]) * f
        arc.append((f, right - chord_x))
    widest = max(o for _, o in arc)
    at = max(range(len(arc)), key=lambda i: arc[i][1]) / (len(arc) - 1)
    print(f"widest stand-out {widest * SCALE if False else widest:.1f}px at {at:.2f} of its height")

    hx_top, hy_top = to_head(*top, ox, oy)
    hx_bot, hy_bot = to_head(*bot, ox, oy)
    print(f"attach top ({hx_top:+.3f}, {hy_top:+.3f})  bottom ({hx_bot:+.3f}, {hy_bot:+.3f})")
    print(f"height {hy_bot - hy_top:.3f} r,  stand-out {widest / R:.3f} r"
          f",  stand-out / height {widest / R / (hy_bot - hy_top):.3f}")

    # Normalised: y from 0 at the top attach to 1 at the bottom, offset from 0 on
    # the chord to 1 at the widest. Placement and width stay the code's own
    # knobs; what the trace carries is the shape between them.
    norm = [(f, o / widest) for f, o in arc]
    # Pick the finest simplification with no edge under two stroke widths, the
    # same rule the hair silhouette settled on. An edge shorter than that is
    # detail the line weight swallows at the build it has to survive, and the
    # figure-relative stroke makes the ratio the same at both.
    height_r = hy_bot - hy_top
    for tol in (0.004, 0.008, 0.015, 0.030, 0.050, 0.080):
        keep = simplify(norm, tol)
        anchors = [
            (norm[i][0] * height_r, norm[i][1] * widest / R) for i in keep
        ]
        chords = [math.dist(anchors[i], anchors[i + 1]) for i in range(len(anchors) - 1)]
        thin = _thin(chords)
        print(f"  tol {tol:.3f} -> {len(keep) - 1:3d} segments, shortest {min(chords):.3f} r,"
              f" under two stroke widths: {thin}")
    keep = simplify(norm, TOL)
    start, segs = fit(norm, keep)
    print("\n_EAR_ARC_START = (%.3f, %.3f)" % start)
    print("_EAR_ARC = [")
    for c, e in segs:
        print(f"    ((%.3f, %.3f), (%.3f, %.3f))," % (c[0], c[1], e[0], e[1]))
    print("]")

    # Drawn back on the sheet, the check every trace here gets.
    box = (ox - 30, oy - 30, ox + W + 30, oy + H + 30)
    z = 6
    im = Image.open(SHEET).convert("RGB").crop(box)
    im = im.resize((im.width * z, im.height * z), Image.LANCZOS)
    d = ImageDraw.Draw(im)

    def place(f: float, o: float) -> tuple[float, float]:
        x = top[0] + (bot[0] - top[0]) * f + o * widest
        y = y0 + (y1 - y0) * f
        return ((ox + x - box[0]) * z, (oy + y - box[1]) * z)

    pts = [place(*start)]
    prev = start
    for c, e in segs:
        for i in range(1, 21):
            t = i / 20
            pts.append(
                place(
                    (1 - t) ** 2 * prev[0] + 2 * (1 - t) * t * c[0] + t**2 * e[0],
                    (1 - t) ** 2 * prev[1] + 2 * (1 - t) * t * c[1] + t**2 * e[1],
                )
            )
        prev = e
    d.line(pts, fill=(255, 0, 255), width=3)
    d.line([place(0, 0), place(1, 0)], fill=(0, 170, 255), width=2)
    im.save(Path(__file__).resolve().parent / "check.png")
    print("\nwrote out/ear2/check.png  (magenta = the fit, blue = the attach chord)")


if __name__ == "__main__":
    main()
