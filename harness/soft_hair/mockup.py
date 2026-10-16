"""Phase 0 of `docs/soft-hair-plan.md`: Risa's visible hair drawn by hand, as variants.

    ./harness/run.sh harness/soft_hair/mockup.py            writes out/soft/mockup-*.png
    ./harness/run.sh harness/soft_hair/mockup.py --seed 3   a different shuffle of the sheet

Not production code. Every guide below is a hand-placed centre line in head radii (x right, y
down, origin at the head centre: read them off `harness/soft_hair/grid.py`), turned into tapered
lens shapes by `lens`, and laid over the front piece of today's soft finish. The question it
answers is whether any treatment reads as clearly more like hair than today's soft finish, before
anyone builds a generator.

Variants (the sheet shows them shuffled and unlabelled by name, with the key in a separate file):

    flat    the house style
    today   `finish="soft"` as committed in 02e3095
    r1      today without the gloss arc
    r2      r1 without the depth wash
    r3      r2 without the jaw shading (the "repaired" soft base the treatments sit on)
    L       r3 + light and shadow only: one lit band, lit streaks, hard shadows along the curtains
    S       r3 + structure: tapered clumps in alternating tones, dark separations, each with a lit
            edge; the old hairline dashes are off
    LS      both
    D       r3 + fibre control: many thin tapered strokes, no structure
    P       LS with the fringe tips drawn as longer, pointed locks (a contour change, soft only)
"""

from __future__ import annotations

import argparse
import io
import json
import math
import random
import re
import sys
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "src")
from anime_character_creator import HAIRSTYLES, PRESETS, render_character, skeleton_for  # noqa: E402
from anime_character_creator import character as C  # noqa: E402
from anime_character_creator.colorutil import shade, tint  # noqa: E402

NAME = "risa"
GROUND = "#2b1a55"
LIGHT = (-0.55, -0.83)  # towards the light: up and to the left

Pt = tuple[float, float]

# --- guides, in head radii -------------------------------------------------------------------
# (centre line, widest width in head radii). Left side; the right is the mirror with its own
# small differences, below. Bangs end at the tips of the traced fringe's own bumps.
LEFT: dict[str, tuple[list[Pt], float]] = {
    "b1": ([(-0.10, -1.50), (-0.14, -1.10), (-0.22, -0.65), (-0.30, -0.28)], 0.17),
    "b2": ([(-0.14, -1.46), (-0.36, -1.15), (-0.50, -0.70), (-0.56, -0.27)], 0.17),
    "b3": ([(-0.18, -1.42), (-0.56, -1.22), (-0.80, -0.82), (-0.88, -0.30), (-0.85, 0.06)], 0.18),
    "o2": ([(-0.30, -1.48), (-0.68, -1.30), (-0.94, -0.90), (-1.05, -0.30), (-1.10, 0.50), (-1.12, 1.30), (-1.20, 2.20), (-1.28, 3.00)], 0.20),
    "o1": ([(-0.46, -1.50), (-0.84, -1.28), (-1.04, -0.95), (-1.15, -0.30), (-1.19, 0.50), (-1.24, 1.40), (-1.33, 2.20), (-1.42, 3.05)], 0.18),
    "c1": ([(-0.84, -0.10), (-0.94, 0.30), (-1.00, 0.90), (-1.03, 1.50), (-1.10, 2.30), (-1.17, 3.05)], 0.15),
}
RIGHT: dict[str, tuple[list[Pt], float]] = {
    "b4": ([(-0.04, -1.50), (0.02, -1.10), (0.12, -0.62), (0.22, -0.20)], 0.17),
    "b5": ([(0.06, -1.47), (0.30, -1.15), (0.50, -0.68), (0.60, -0.14)], 0.18),
    "b6": ([(0.20, -1.42), (0.62, -1.20), (0.88, -0.80), (0.98, -0.28), (0.96, 0.10)], 0.19),
    "o4": ([(0.30, -1.48), (0.72, -1.28), (0.98, -0.88), (1.08, -0.30), (1.13, 0.50), (1.17, 1.30), (1.27, 2.20), (1.36, 3.05)], 0.20),
    "o3": ([(0.46, -1.50), (0.88, -1.26), (1.08, -0.92), (1.19, -0.30), (1.24, 0.50), (1.30, 1.40), (1.40, 2.25), (1.50, 3.10)], 0.18),
    "c2": ([(0.84, -0.10), (0.95, 0.30), (1.01, 0.90), (1.06, 1.50), (1.13, 2.30), (1.22, 3.00)], 0.15),
}
GUIDES = {**LEFT, **RIGHT}
BANGS = ("b1", "b2", "b3", "b4", "b5", "b6")
RIM = ("o1", "o3")


def catmull(points: list[Pt], per: int = 14) -> list[Pt]:
    """A smooth curve through `points`."""
    p = [points[0], *points, points[-1]]
    out: list[Pt] = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(
                tuple(
                    0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)
                    for j in (0, 1)
                )  # type: ignore[arg-type]
            )
    out.append(points[-1])
    return out


def normals(pts: list[Pt]) -> list[Pt]:
    out = []
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        out.append((-dy / n, dx / n))
    return out


class Frame:
    """Head-radius units to the figure's pixels."""

    def __init__(self) -> None:
        sk = skeleton_for(PRESETS[NAME])
        self.cx, self.cy, self.r = sk.head_cx, sk.head_cy, sk.head_r

    def px(self, p: Pt) -> str:
        return f"{self.cx + p[0] * self.r:.2f} {self.cy + p[1] * self.r:.2f}"


def lens(f: Frame, pts: list[Pt], width: float, t0: float = 0.0, t1: float = 1.0, power: float = 0.75, offset: float = 0.0, flat_end: bool = False) -> str:
    """A tapered shape along `pts`: nothing at either end, `width` at the widest, `offset` (a
    share of the local width) toward the light side. With `flat_end` the lower end stays wide."""
    line = catmull(pts)
    nrm = normals(line)
    n = len(line)
    left: list[Pt] = []
    right: list[Pt] = []
    for i, ((x, y), (nx, ny)) in enumerate(zip(line, nrm, strict=True)):
        t = i / (n - 1)
        if t < t0 or t > t1:
            continue
        u = (t - t0) / (t1 - t0)
        w = width * (math.sin(math.pi * u) ** power if not (flat_end and u > 0.5) else 1.0)
        side = 1.0 if nx * LIGHT[0] + ny * LIGHT[1] >= 0 else -1.0
        cx, cy = x + nx * side * offset * w, y + ny * side * offset * w
        left.append((cx + nx * w / 2, cy + ny * w / 2))
        right.append((cx - nx * w / 2, cy - ny * w / 2))
    ring = left + right[::-1]
    return "M " + " L ".join(f.px(q) for q in ring) + " Z"


# --- overlays --------------------------------------------------------------------------------


def overlay_L(f: Frame, hair: str) -> str:
    lit = tint(hair, 0.55)
    dark = shade(hair, 0.45)
    parts = []
    # The lit band across the crown, in pieces with gaps at the locks, broader on the light side.
    for pts, w, op in (
        ([(-1.08, -0.50), (-0.96, -0.92), (-0.62, -1.28), (-0.30, -1.40)], 0.24, 0.55),
        ([(-0.20, -1.42), (0.10, -1.40), (0.36, -1.30)], 0.16, 0.45),
        ([(0.52, -1.20), (0.82, -0.95), (1.00, -0.55)], 0.14, 0.32),
    ):
        parts.append(f'<path d="{lens(f, pts, w, power=0.6)}" fill="{lit}" opacity="{op}" />')
    # Lit streaks following the fall of the hair beside the face, one hard edge each.
    for pts, w, op in (
        ([(-1.02, 0.35), (-1.06, 1.1), (-1.13, 1.9), (-1.22, 2.7)], 0.07, 0.55),
        ([(-1.16, 0.2), (-1.2, 1.1), (-1.28, 2.0), (-1.36, 2.8)], 0.05, 0.45),
        ([(1.02, 0.35), (1.08, 1.1), (1.17, 1.9), (1.28, 2.7)], 0.05, 0.35),
    ):
        parts.append(f'<path d="{lens(f, pts, w)}" fill="{lit}" opacity="{op}" />')
    # Hard shadows where hair meets the face and falls behind the shoulders.
    for pts, w, op in (
        ([(-0.90, 0.10), (-0.95, 0.7), (-0.98, 1.3), (-1.02, 1.9)], 0.16, 0.45),
        ([(0.90, 0.10), (0.96, 0.7), (1.01, 1.3), (1.07, 1.9)], 0.16, 0.45),
        ([(-0.75, -0.95), (-0.55, -0.55), (-0.30, -0.32)], 0.12, 0.30),
        ([(0.10, -0.80), (0.38, -0.50), (0.62, -0.25)], 0.12, 0.30),
    ):
        parts.append(f'<path d="{lens(f, pts, w, power=0.5)}" fill="{dark}" opacity="{op}" />')
    return "".join(parts)


def overlay_S(f: Frame, hair: str, extend: bool = False) -> str:
    lit = tint(hair, 0.5)
    mid_lit = tint(hair, 0.18)
    mid_dark = shade(hair, 0.78)
    sep = shade(hair, 0.35)
    parts = []
    for i, (name, (pts, w)) in enumerate(GUIDES.items()):
        tone, op = (mid_lit, 0.30) if i % 2 == 0 else (mid_dark, 0.34)
        if name in RIM:  # the outermost clumps stay dark: a pale clump on the silhouette reads as a second outline
            tone, op = mid_dark, 0.34
        parts.append(f'<path d="{lens(f, pts, w, power=0.55)}" fill="{tone}" opacity="{op}" />')
    for name, (pts, w) in GUIDES.items():
        # a dark separation along each guide's edge, shorter than the clump and ending before its tip
        parts.append(f'<path d="{lens(f, pts, 0.045, t0=0.08, t1=0.92, power=0.5, offset=-1.9)}" fill="{sep}" opacity="0.85" />')
        # and a lit edge on the side facing the light
        parts.append(f'<path d="{lens(f, pts, w * 0.30, t0=0.10, t1=0.80, power=0.8, offset=0.55)}" fill="{lit}" opacity="0.60" />')
    return "".join(parts)


def pointed_fringe(f: Frame, hair: str, line: str) -> str:
    """The fringe's tips as longer, sharper locks drawn over the face, hair colour and a thin line."""
    parts = []
    for name in BANGS:
        pts, w = GUIDES[name]
        tip = pts[-1]
        prev = pts[-2]
        dx, dy = tip[0] - prev[0], tip[1] - prev[1]
        n = math.hypot(dx, dy) or 1.0
        ext = 0.20
        longer = [*pts[-3:-1], tip, (tip[0] + dx / n * ext, tip[1] + dy / n * ext)]
        d = lens(f, longer, w * 0.9, t0=0.0, t1=1.0, power=0.9, flat_end=False)
        parts.append(f'<path d="{d}" fill="{hair}" stroke="{line}" stroke-width="0.5" stroke-linejoin="round" />')
    return "".join(parts)


def overlay_D(f: Frame, hair: str) -> str:
    """Fibre control: density without structure."""
    rng = random.Random(11)
    lit, dark = tint(hair, 0.5), shade(hair, 0.4)
    parts = []
    names = list(GUIDES)
    for _ in range(150):
        pts, _w = GUIDES[rng.choice(names)]
        jitter = rng.uniform(-0.18, 0.18)
        a = rng.uniform(0.0, 0.5)
        b = a + rng.uniform(0.25, 0.5)
        seg = [(x + jitter, y) for x, y in pts]
        tone, op = (lit, 0.45) if rng.random() < 0.5 else (dark, 0.55)
        parts.append(f'<path d="{lens(f, seg, rng.uniform(0.012, 0.03), t0=min(a, 0.7), t1=min(b, 1.0), power=0.5)}" fill="{tone}" opacity="{op}" />')
    return "".join(parts)


# --- rendering with variants -----------------------------------------------------------------


@contextmanager
def patched(**attrs: object):
    old = {k: getattr(C, k) for k in attrs}
    for k, v in attrs.items():
        setattr(C, k, v)
    try:
        yield
    finally:
        for k, v in old.items():
            setattr(C, k, v)


def render(variant: str) -> str:
    p = PRESETS[NAME]
    f = Frame()
    hair = p.hair_color
    line = shade(hair, C._SOFT_HAIR_LINE_VALUE)
    knobs: dict[str, object] = {}
    treat = ""
    strands_off = False
    extend = False
    finish = "soft"
    if variant == "flat":
        finish = "flat"
    elif variant == "today":
        pass
    else:
        knobs = {"_SOFT_GLOSS_LAYERS": ()}
        if variant != "r1":
            knobs["_SOFT_HAIR_DEPTH_TOP"] = (C._SOFT_HAIR_DEPTH_TOP[0], 0.0)
            knobs["_SOFT_HAIR_DEPTH_BOTTOM"] = (C._SOFT_HAIR_DEPTH_BOTTOM[0], 0.0)
        if variant not in ("r1", "r2"):
            knobs["_SOFT_FACE_EDGE_OPACITY"] = 0.0
        if variant == "L":
            treat = overlay_L(f, hair)
        elif variant == "S":
            treat, strands_off = overlay_S(f, hair), True
        elif variant == "LS":
            treat, strands_off = overlay_L(f, hair) + overlay_S(f, hair), True
        elif variant == "D":
            treat = overlay_D(f, hair)
        elif variant == "P":
            treat, strands_off, extend = overlay_L(f, hair) + overlay_S(f, hair), True, True

    original_front = C._hair_front
    original_style = HAIRSTYLES[p.hairstyle]

    def front(sk, pp):  # type: ignore[no-untyped-def]
        out = original_front(sk, pp)
        if not treat:
            return out
        style = HAIRSTYLES[pp.hairstyle]
        start, ln, back = style.hairline(C._hair_fall(sk, pp))
        fill_d = C._curve(sk.head_cx, sk.head_cy, sk.head_r, start, ln + back)
        group = f'<defs><clipPath id="mock-clip"><path d="{fill_d}" /></clipPath></defs><g clip-path="url(#mock-clip)">{treat}</g>'
        # The skin patches (the ears show through them) go back over the overlay, as they would
        # if the overlay were drawn before them.
        if style.openings is not None:
            sw = C._stroke_w(sk)
            for chain in style.openings(C._hair_fall(sk, pp)):
                group += (
                    f'<path d="{C._curve(sk.head_cx, sk.head_cy, sk.head_r, *chain)}" fill="{pp.skin_tone}" '
                    f'stroke="{C.OUTLINE}" stroke-width="{C._interior_w(sw):.2f}" stroke-linejoin="round" />'
                )
        if extend:
            group += pointed_fringe(f, hair, line)
        return out + group

    try:
        with patched(**knobs):
            C._hair_front = front
            if strands_off:
                HAIRSTYLES[p.hairstyle] = replace(original_style, strands=None)
            return render_character(replace(p, finish=finish))
    finally:
        C._hair_front = original_front
        HAIRSTYLES[p.hairstyle] = original_style


VARIANTS = ["flat", "today", "r1", "r2", "r3", "L", "S", "LS", "D", "P"]
VIEWS = {"close": ("55 0 290 330", (400, 455)), "face": ("120 5 160 170", (560, 595))}


def draw(variant: str, view: str) -> Image.Image:
    box, (w, h) = VIEWS[view]
    svg = render(variant)
    svg = re.sub(r'viewBox="[^"]+"', f'viewBox="{box}"', svg, count=1)
    svg = re.sub(r'width="400" height="\d+"', f'width="{w}" height="{h}"', svg, count=1)
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), background_color=GROUND))).convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="out/soft")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    order = VARIANTS[:]
    random.Random(args.seed).shuffle(order)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
    except OSError:
        font = ImageFont.load_default()
    for view in VIEWS:
        w, h = VIEWS[view][1]
        cols = 5
        sheet = Image.new("RGB", (cols * w + (cols - 1) * 6, 2 * (h + 6) + 0), "white")
        for i, v in enumerate(order):
            im = draw(v, view)
            x, y = (i % cols) * (w + 6), (i // cols) * (h + 6)
            sheet.paste(im, (x, y))
            ImageDraw.Draw(sheet).text((x + 10, y + 8), "ABCDEFGHIJ"[i], fill="white", font=font)
            if view == "face":
                im.save(out / f"mockup-face-{v}.png")
        sheet.save(out / f"mockup-{view}-sheet.png")
    (out / "mockup-key.json").write_text(json.dumps({"ABCDEFGHIJ"[i]: v for i, v in enumerate(order)}, indent=1))
    print("wrote", out / "mockup-close-sheet.png", "and the key in mockup-key.json (do not open it before choosing)")


if __name__ == "__main__":
    main()
