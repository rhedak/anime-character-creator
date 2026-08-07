#!/usr/bin/env python3
"""Measurement tools for comparing a render against reference art.

Run with the project venv, which has Pillow: `.venv/bin/python probe.py ...`
or `uv run python .claude/skills/gap-analysis/probe.py ...`.

Every subcommand normalises by **figure height**: the painted figure's bounding
box, ink top to sole, found by ignoring near-white background. That is the only
denominator that measures the same way on an antialiased JPEG reference and on
our own flat PNG, so positions and widths are all printed as fractions of it
and are directly comparable between the two. Nothing here normalises by a
measured face width or by any other derived landmark; see PITFALLS.md for why
that wrecked three earlier attempts.

Subcommands:

  strip     build a side-by-side image, panels scaled to a common height
  profile   silhouette width table, reference against ours, with bars
  column    colour runs down the centre column: the garment stack, with hex
  rows      per-row span of a given colour set: hair silhouette, a garment
  eyes      enclosed white blobs inside the head: the eye apertures
  sample    exact modal colour inside a box, for palette comparison
  skeleton  our own landmarks computed from build_skeleton, not measured

Use `--help` on any of them.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, deque
from pathlib import Path

from PIL import Image, ImageDraw

BG = 236  # a channel at or above this on all three counts as background


# --------------------------------------------------------------------------
# shared


def flatten(path: str) -> Image.Image:
    """Open an image with any transparency composited onto white.

    Our own renders are transparent as of 2026-08-07, and a straight
    `convert("RGB")` on those discards the alpha and leaves the background
    reading as **black**, which is the opposite of what `is_bg` looks for: the
    whole canvas would count as ink and every measurement here would come out
    silently wrong rather than failing. The references are opaque already, so
    flattening changes nothing for them and puts both sides on one footing.
    """
    im = Image.open(path)
    if im.mode in ("RGBA", "LA") or "transparency" in im.info:
        sheet = Image.new("RGB", im.size, "white")
        im = im.convert("RGBA")
        sheet.paste(im, (0, 0), im)
        return sheet
    return im.convert("RGB")


def pixels(path: str) -> tuple[int, int, object]:
    """Width, height and a pixel accessor. Callers that need the `Image` itself
    open it themselves, so nothing unpacks a value it does not use."""
    im = flatten(path)
    return im.size[0], im.size[1], im.load()


def is_bg(px) -> bool:
    return px[0] > BG and px[1] > BG and px[2] > BG


def figure_box(p, W: int, H: int, min_run: int = 6) -> tuple[int, int, int, int]:
    """Bounding box of the painted figure.

    A row counts as painted only once `min_run` non-background pixels have been
    seen in a row, which is what keeps JPEG speckle and stray antialiasing out
    of the box. The box is the one robust primitive in this file: the figure's
    own outline surrounds everything, so no colour classification is involved.
    """
    xs: list[tuple[int, int]] = []
    ys: list[int] = []
    for y in range(H):
        run = 0
        first = last = None
        for x in range(W):
            if not is_bg(p[x, y]):
                run += 1
                if run >= min_run:
                    if first is None:
                        first = x - min_run + 1
                    last = x
            else:
                run = 0
        if last is not None:
            ys.append(y)
            xs.append((first, last))
    if not ys:
        raise SystemExit("no figure found: is the background near-white?")
    return min(a for a, _ in xs), ys[0], max(b for _, b in xs), ys[-1]


def parse_hex(s: str) -> tuple[int, int, int]:
    s = s.strip().lstrip("#")
    return tuple(int(s[i : i + 2], 16) for i in (0, 2, 4))


def dist2(a, b) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def runs_in_row(p, W: int, y: int, hit) -> list[tuple[int, int]]:
    """Contiguous runs of at least 4px where `hit(pixel)` is true."""
    out = []
    start = None
    for x in range(W + 1):
        on = x < W and hit(p[x, y])
        if on and start is None:
            start = x
        elif not on and start is not None:
            if x - start >= 4:
                out.append((start, x - 1))
            start = None
    return out


# --------------------------------------------------------------------------
# strip


def normalised(path: str, height: int) -> Image.Image:
    im = flatten(path)
    W, H = im.size
    x0, y0, x1, y1 = figure_box(im.load(), W, H)
    crop = im.crop((x0, y0, x1 + 1, y1 + 1))
    s = height / crop.size[1]
    return crop.resize((max(1, round(crop.size[0] * s)), height), Image.LANCZOS)


def cmd_strip(a) -> None:
    """Panels cropped to their figures and scaled to one height, side by side.

    Scaling to a common figure height is the whole point: it is what makes a
    reference drawn at one size comparable to a render at another, and what
    turns "the hair looks narrow" into a difference you can point at.
    """
    lo, hi = (float(v) for v in a.band.split(",")) if a.band else (0.0, 1.0)
    panels = []
    for spec in a.panel:
        label, _, path = spec.partition("=")
        if not path:
            raise SystemExit(f"--panel wants LABEL=PATH, got {spec!r}")
        img = normalised(path, a.height)
        img = img.crop((0, int(lo * a.height), img.size[0], int(hi * a.height)))
        if a.zoom != 1:
            img = img.resize((img.size[0] * a.zoom, img.size[1] * a.zoom), Image.LANCZOS)
        panels.append((label, img))

    pad = 18
    Wt = sum(i.size[0] for _, i in panels) + pad * (len(panels) + 1)
    Ht = max(i.size[1] for _, i in panels) + 40
    canvas = Image.new("RGB", (Wt, Ht), "white")
    d = ImageDraw.Draw(canvas)
    x = pad
    for label, img in panels:
        canvas.paste(img, (x, 30))
        d.text((x + 2, 8), label, fill="black")
        if a.guides:
            for g in [i / 10 for i in range(1, 10)]:
                if lo <= g <= hi:
                    yy = 30 + int((g - lo) / (hi - lo) * img.size[1])
                    d.line([(x, yy), (x + img.size[0], yy)], fill=(255, 40, 40), width=1)
                    d.text((x + 4, yy + 2), f"{g:.1f}", fill=(255, 40, 40))
        x += img.size[0] + pad
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(a.out)
    print(f"{a.out}  {canvas.size[0]}x{canvas.size[1]}   LOOK AT IT before measuring anything")


# --------------------------------------------------------------------------
# profile

# fmt: off
MARKS = [
    0.02, 0.05, 0.08, 0.11, 0.14, 0.17, 0.20, 0.24, 0.28, 0.32, 0.36, 0.40,
    0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95,
]
# fmt: on


def width_profile(path: str) -> tuple[dict[float, float], int]:
    W, H, p = pixels(path)
    _, y0, _, y1 = figure_box(p, W, H)
    Hf = y1 - y0 + 1
    out = {}
    for y in range(y0, y1 + 1):
        run = 0
        first = last = None
        for x in range(W):
            if not is_bg(p[x, y]):
                run += 1
                if run >= 6:
                    if first is None:
                        first = x - 5
                    last = x
            else:
                run = 0
        if last is not None:
            out[(y - y0) / Hf] = (last - first + 1) / Hf
    return out, Hf


def cmd_profile(a) -> None:
    pa, ha = width_profile(a.ref)
    pb, hb = width_profile(a.ours)
    print(f"silhouette width as a fraction of figure height   (ref H={ha}px, ours H={hb}px)")
    print("  y/H     REF    OURS    delta")
    for m in MARKS:
        ka = min(pa, key=lambda k: abs(k - m))
        kb = min(pb, key=lambda k: abs(k - m))
        va, vb = pa[ka], pb[kb]
        bar_a = "#" * int(va * 70)
        bar_b = "#" * int(vb * 70)
        print(
            f"  {m:.2f}   {va:.3f}   {vb:.3f}   {(vb - va) / va * 100:+6.1f}%"
            f"   {bar_a:<36s}|{bar_b}"
        )


# --------------------------------------------------------------------------
# column


def cmd_column(a) -> None:
    """Colour runs down the vertical centre line.

    This is the reliable way to get a reference's garment stack: chin, collar,
    tunic, belt, apron, hem, and so on, each with the hex it is painted in. It
    reads one column, so nothing another row does can contaminate it, and it
    needs no palette handed to it in advance.

    It cannot tell you what a run *is*. A mouth line and a jaw stroke are both
    a few rows of dark; only looking can separate them. Confirm anything that
    matters with `strip --band` at a zoom.
    """
    W, H, p = pixels(a.image)
    x0, y0, x1, y1 = figure_box(p, W, H)
    Hf = y1 - y0 + 1
    cx = (x0 + x1) // 2 + a.offset
    print(f"centre column x={cx} (offset {a.offset:+d}), figure H={Hf}px")
    print("  y/H range        thickness  colour     note")
    i = y0
    while i <= y1:
        j = i
        while j + 1 <= y1 and dist2(p[cx, j + 1], p[cx, i]) <= a.tol**2:
            j += 1
        n = j - i + 1
        if n >= a.min_run:
            r, g, b = p[cx, (i + j) // 2]
            tag = (
                "background" if is_bg((r, g, b)) else ("dark, a line?" if max(r, g, b) < 80 else "")
            )
            print(
                f"  {(i - y0) / Hf:.3f}..{(j - y0) / Hf:.3f}   {n / Hf:.3f} H"
                f"    #{r:02x}{g:02x}{b:02x}   {tag}"
            )
        i = j + 1


# --------------------------------------------------------------------------
# rows


def cmd_rows(a) -> None:
    """Per-row extent of one colour set: how wide is the hair, or a garment.

    `--colors` are the tones you want measured and `--against` are the tones
    they could be confused with. A pixel counts only if it is closer to a
    wanted colour than to any competing one, which is a nearest-colour
    assignment rather than a tolerance ball. On flat output a tolerance is
    fine; on a reference it is not, because pale hair and light skin sit within
    any tolerance wide enough to survive JPEG, and a tolerance test silently
    merges them.

    Two numbers per row: the overall span (outer edge to outer edge, which is
    the silhouette of the mass) and the individual runs (the width of one
    lock, one fall, one leg). The second is usually the one that matters. A
    fall that holds its width down the drop and one that pinches in the middle
    can have the same span.
    """
    W, H, p = pixels(a.image)
    _, y0, _, y1 = figure_box(p, W, H)
    Hf = y1 - y0 + 1
    want = [parse_hex(c) for c in a.colors.split(",")]
    other = [parse_hex(c) for c in a.against.split(",")] if a.against else []

    def hit(px):
        if is_bg(px):
            return False
        dw = min(dist2(px, c) for c in want)
        if other and dw >= min(dist2(px, c) for c in other):
            return False
        return dw <= a.tol**2 * 3

    # fmt: off
    default_marks = [
        0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15, 0.18, 0.21, 0.25,
        0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70, 0.80,
    ]
    # fmt: on
    marks = [float(v) for v in a.at.split(",")] if a.at else default_marks
    print(
        f"figure H={Hf}px   colours {a.colors}" + (f"   against {a.against}" if a.against else "")
    )
    print("  y/H   span    runs (each as a fraction of H)")
    for m in marks:
        y = y0 + int(m * Hf)
        rs = runs_in_row(p, W, y, hit)
        if not rs:
            print(f"  {m:.2f}   .        .")
            continue
        span = (rs[-1][1] - rs[0][0] + 1) / Hf
        print(f"  {m:.2f}   {span:.3f}   " + "  ".join(f"{(b - aa + 1) / Hf:.3f}" for aa, b in rs))


# --------------------------------------------------------------------------
# eyes


def cmd_eyes(a) -> None:
    """Eye apertures, found as white regions enclosed by ink inside the head.

    No palette and no assumption about the eye's colour: flood the background
    whites from the border, and what is left above the chin is the sclera. The
    check that it worked is that the left and right come out the same size on a
    symmetric figure. If they do not, or if the blob is far from eye-shaped,
    it has found a highlight dot or a gap between hair strands instead, and the
    number is worthless: crop the head and read it off by eye.
    """
    W, H, p = pixels(a.image)
    x0, y0, x1, y1 = figure_box(p, W, H)
    Hf = y1 - y0 + 1
    lim = y0 + int((a.chin + 0.02) * Hf)

    white = [[all(v >= 238 for v in p[x, y]) for x in range(W)] for y in range(H)]
    seen = [[False] * W for _ in range(H)]
    q: deque = deque()
    for x in range(W):
        for y in (0, H - 1):
            if white[y][x] and not seen[y][x]:
                seen[y][x] = True
                q.append((x, y))
    for y in range(H):
        for x in (0, W - 1):
            if white[y][x] and not seen[y][x]:
                seen[y][x] = True
                q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and white[ny][nx] and not seen[ny][nx]:
                seen[ny][nx] = True
                q.append((nx, ny))

    blobs = []
    for yy in range(y0, lim):
        for xx in range(x0, x1 + 1):
            if white[yy][xx] and not seen[yy][xx]:
                seen[yy][xx] = True
                comp = [(xx, yy)]
                q.append((xx, yy))
                while q:
                    x, y = q.popleft()
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < W and 0 <= ny < H and white[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            comp.append((nx, ny))
                            q.append((nx, ny))
                if len(comp) >= a.min_area:
                    bx = [c[0] for c in comp]
                    by = [c[1] for c in comp]
                    blobs.append(
                        (len(comp), min(bx), min(by), max(bx) - min(bx) + 1, max(by) - min(by) + 1)
                    )
    blobs.sort(reverse=True)
    keep = sorted(blobs[:2], key=lambda b: b[1])
    print(f"figure H={Hf}px, searching above y={a.chin:.3f} H")
    if len(keep) < 2:
        print("  fewer than two apertures found: crop the head and read it by eye")
    for i, (area, _bx, by, w, h) in enumerate(keep):
        print(
            f"  aperture {i}: {w}x{h}px  aspect {w / h:.2f}  width {w / Hf:.4f} H"
            f"  centre y {(by + h / 2 - y0) / Hf:.3f} H  area {area}px"
        )
    if len(keep) == 2:
        gap = keep[1][1] - (keep[0][1] + keep[0][3])
        # Relative rather than a pixel count, and not tight, because a deliberate
        # asymmetry above the eyes makes the two apertures legitimately differ: an
        # off-centre parting drops more fringe over one of them, which clips a few
        # pixels off that aperture's top. A few percent apart is that. Wildly
        # apart means the detector found a highlight dot or a gap between hair
        # strands on one side, and then neither number means anything.
        dw = abs(keep[0][3] - keep[1][3]) / max(keep[0][3], keep[1][3])
        dh = abs(keep[0][4] - keep[1][4]) / max(keep[0][4], keep[1][4])
        close = dw <= 0.08 and dh <= 0.08
        print(f"  gap between apertures {gap}px = {gap / Hf:.4f} H")
        print(
            f"  left and right differ by {dw:.1%} in width, {dh:.1%} in height: "
            + (
                "consistent, trust these"
                if close
                else "TOO FAR APART, the detector found something else"
            )
        )
        print(f"  mean aperture width {(keep[0][3] + keep[1][3]) / 2 / Hf:.4f} H")
        # Symmetry alone cannot catch the other failure, because what it finds
        # instead is symmetric too: the pair of highlight dots inside the irises,
        # which on the adult references came out 12x17px and agreed with each
        # other perfectly. An aperture in this style is always wider than it is
        # tall, so anything taller than wide is not one, however neatly the two
        # sides match.
        if min(keep[0][3] / keep[0][4], keep[1][3] / keep[1][4]) < 1.0:
            print(
                "  TALLER THAN WIDE, so these are not apertures: highlight dots, or a"
                " gap between hair strands. Crop the head and read it by eye."
            )


# --------------------------------------------------------------------------
# sample


def cmd_sample(a) -> None:
    """Modal exact colour inside a box, given as fractions of the whole image.

    Exact, not quantised. A histogram bucketed at 16 is only good to eight
    points a channel, which is the same size as the palette differences worth
    arguing about, so a bucket centre cannot settle whether two palettes match.
    Put the box inside a flat patch, away from any outline or shadow.
    """
    W, H, p = pixels(a.image)
    x0, y0, x1, y1 = (float(v) for v in a.box.split(","))
    bx0, by0, bx1, by1 = int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)
    c: Counter = Counter()
    for y in range(by0, by1):
        for x in range(bx0, bx1):
            c[p[x, y]] += 1
    tot = sum(c.values())
    print(f"{a.image}  box {a.box}  ({bx1 - bx0}x{by1 - by0}px)")
    for (r, g, b), k in c.most_common(a.top):
        print(f"  #{r:02x}{g:02x}{b:02x}  {100 * k / tot:5.1f}%")


# --------------------------------------------------------------------------
# skeleton


def _report_skeleton(C, sk, name: str, heads: float, p, canvas: str) -> None:
    """One figure's landmark table. A function rather than a loop body so the
    two scalers below close over parameters instead of over loop variables."""
    style = C.HAIRSTYLES[p.hairstyle]
    length = C._hair_fall(sk, p)
    mass = style.mass(length)
    pts = [mass[0]] + [q for ctrl, end in mass[1] for q in (ctrl, end)]
    top = sk.head_cy + min(y for _, y in pts) * sk.head_r - C._stroke_w(sk) / 2
    Hf = sk.foot_y - top

    def Y(v: float) -> float:
        return (v - top) / Hf

    def D(v: float) -> float:
        return v / Hf

    print(f"\n{name} heads={heads}  canvas {canvas}  H={Hf:.1f}px")
    print(f"  head_r {sk.head_r:.1f}px, head height {D(2 * sk.head_r):.3f} H")
    for label, v in [
        ("chin y", Y(sk.head_cy + sk.head_r)),
        ("neck y", Y(sk.neck_y)),
        ("shoulder y", Y(sk.shoulder_y)),
        ("waist y", Y(sk.waist_y)),
        ("hip y", Y(sk.hip_y)),
        ("hem y", Y(sk.hem_y)),
        ("knee y", Y(sk.knee_y)),
        ("ankle y", Y(sk.ankle_y)),
    ]:
        print(f"  {label:12s} {v:.3f} H")
    for label, v in [
        ("shoulder w", D(2 * sk.shoulder_half_w)),
        ("waist w", D(2 * sk.waist_half_w)),
        ("hip w", D(2 * sk.hip_half_w)),
        ("hem w", D(2 * sk.hem_half_w)),
        ("arm w", D(2 * sk.arm_half_w)),
        ("leg w", D(2 * sk.leg_half_w)),
        ("stroke w", D(C._stroke_w(sk))),
    ]:
        print(f"  {label:12s} {v:.3f} H")
    print(
        f"  hair fall length {length:.3f} head-radii below the head centre"
        f" = y {Y(sk.head_cy + length * sk.head_r):.3f} H"
    )


def cmd_skeleton(a) -> None:
    """Our own landmarks, computed rather than measured.

    There is no reason to count pixels on our own output: the skeleton knows
    where every anchor is, and reading it means the number is exact and names
    the constant to change. Measure the reference, compute ours.
    """
    sys.path.insert(0, "src")
    from anime_character_creator import PRESETS, build_skeleton
    from anime_character_creator import character as C

    for name in a.preset:
        p = PRESETS[name]
        for heads in [float(h) for h in a.heads.split(",")]:
            sk = build_skeleton(a.width, a.height, heads=heads, frame=p.frame)
            _report_skeleton(C, sk, name, heads, p, f"{a.width:g}x{a.height:g}")


# --------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("strip", help="side-by-side panels at a common figure height")
    s.add_argument("--panel", action="append", required=True, metavar="LABEL=PATH")
    s.add_argument("--out", required=True)
    s.add_argument("--height", type=int, default=760, help="figure height in the strip")
    s.add_argument("--band", help="crop to lo,hi as fractions of figure height")
    s.add_argument("--zoom", type=int, default=1)
    s.add_argument("--guides", action="store_true", help="red lines every 0.1 H")
    s.set_defaults(fn=cmd_strip)

    s = sub.add_parser("profile", help="silhouette width table, ref against ours")
    s.add_argument("ref")
    s.add_argument("ours")
    s.set_defaults(fn=cmd_profile)

    s = sub.add_parser("column", help="colour runs down the centre column")
    s.add_argument("image")
    s.add_argument("--tol", type=int, default=10, help="how close two rows count as one run")
    s.add_argument("--min-run", type=int, default=5, dest="min_run")
    s.add_argument("--offset", type=int, default=0, help="shift the column off centre")
    s.set_defaults(fn=cmd_column)

    s = sub.add_parser("rows", help="per-row extent of a colour set")
    s.add_argument("image")
    s.add_argument("--colors", required=True, help="comma-separated hex")
    s.add_argument("--against", help="comma-separated hex these could be confused with")
    s.add_argument("--tol", type=int, default=14)
    s.add_argument("--at", help="comma-separated y fractions")
    s.set_defaults(fn=cmd_rows)

    s = sub.add_parser("eyes", help="eye apertures as enclosed white")
    s.add_argument("image")
    s.add_argument("--chin", type=float, required=True, help="chin as a fraction of H")
    s.add_argument("--min-area", type=int, default=60, dest="min_area")
    s.set_defaults(fn=cmd_eyes)

    s = sub.add_parser("sample", help="exact modal colour in a box")
    s.add_argument("image")
    s.add_argument("--box", required=True, metavar="x0,y0,x1,y1")
    s.add_argument("--top", type=int, default=4)
    s.set_defaults(fn=cmd_sample)

    s = sub.add_parser("skeleton", help="our landmarks, computed from build_skeleton")
    s.add_argument("--preset", action="append", default=None)
    s.add_argument("--heads", default="2.4,6.0")
    s.add_argument("--width", type=float, default=800)
    s.add_argument("--height", type=float, default=1000)
    s.set_defaults(fn=cmd_skeleton)

    a = ap.parse_args()
    if a.cmd == "skeleton" and not a.preset:
        a.preset = ["satoko", "satoshi"]
    a.fn(a)


if __name__ == "__main__":
    main()
