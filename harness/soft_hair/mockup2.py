"""Round 2 of the Phase 0 mock-up (`docs/soft-hair-plan.md`, section 11).

    ./harness/run.sh harness/soft_hair/mockup2.py                  writes out/soft/v3/
    ./harness/run.sh harness/soft_hair/mockup2.py --seed 5         a different shuffle

Not production code. Same Risa guides as `mockup.py`, rebuilt after the method review:

  * the lit side is chosen once per guide (round 1 flipped it mid-guide on four right side guides);
  * widths and lengths get deterministic jitter, so the clumps are not a comb;
  * tones are hue-true (value up, saturation kept, hue nudged warm), drawn as solid steps, not as
    translucent white washes, and a lit clump has one highlight, with no paired near-black line;
  * light and grey hair get a shadow-led treatment, because value cannot rise past white.

Variants, all on r3 (soft without the gloss arc, the depth wash or the jaw shading):

    r3      control, and `r3b`, an identical second copy that is never labelled (the judge's own noise)
    today   control: `finish="soft"` as committed
    SS      value steps only: shadow clumps with a soft separation, no lit tone at all
    SH      one sheen on the crown, nothing else
    S2      three solid tones: shadow clumps, lit clumps, one highlight in each lit clump
    LS2     S2 plus the ring highlight
    P2      LS2 with the pointed fringe (a contour change, soft only)
"""

from __future__ import annotations

import argparse
import colorsys
import io
import json
import math
import random
import re
import sys
from dataclasses import replace
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "src")
import mockup as M  # noqa: E402
from anime_character_creator import HAIRSTYLES, PRESETS, render_character  # noqa: E402
from anime_character_creator import character as C  # noqa: E402
from anime_character_creator.colorutil import hex_to_rgb01, rgb01_to_hex, shade  # noqa: E402

Pt = tuple[float, float]
GROUND = M.GROUND
LIGHT = M.LIGHT

# The clump tones, by guide: shadow clumps, lit clumps, and the rest left as the base colour.
ROLE = {
    "b1": "shadow", "b2": "lit", "b3": "shadow", "o2": "lit", "o1": "shadow", "c1": "shadow",
    "b4": "base", "b5": "lit", "b6": "shadow", "o4": "lit", "o3": "shadow", "c2": "shadow",
}  # fmt: skip

# Four hair colours besides Risa's own, from the cast: dark, light, grey, orange.
PALETTE = {"red": None, "dark": "#16131a", "blond": "#c2b58a", "grey": "#c9c6c2", "orange": "#b5602b"}

# --- tones -------------------------------------------------------------------------------------


def _hsv(hex_color: str) -> tuple[float, float, float]:
    return colorsys.rgb_to_hsv(*hex_to_rgb01(hex_color))


def lit_tone(hair: str, dv: float) -> str:
    """Lighter, keeping the saturation, hue nudged a little warm. When value would pass white the
    saturation gives way instead, by part of the overshoot."""
    h, s, v = _hsv(hair)
    v2 = v + dv
    if v2 > 1.0:
        s = max(0.0, s - (v2 - 1.0) * 0.6)
        v2 = 1.0
    h = (h + 4.0 / 360.0) % 1.0
    return rgb01_to_hex(colorsys.hsv_to_rgb(h, s, v2))


def dv_high(hair: str) -> float:
    """How far the strongest highlight rises: more on dark hair, little on light."""
    v = _hsv(hair)[2]
    return min(0.28, max(0.06, 0.30 * (1.0 - v) + 0.08))


def shadow_tone(hair: str) -> str:
    v = _hsv(hair)[2]
    return shade(hair, 0.80 - 0.15 * v, saturation_boost=1.3)


# --- shapes ------------------------------------------------------------------------------------


def light_side(pts: list[Pt]) -> float:
    line = M.catmull(pts)
    total = sum(nx * LIGHT[0] + ny * LIGHT[1] for nx, ny in M.normals(line))
    return 1.0 if total >= 0 else -1.0


def lens2(f: M.Frame, pts: list[Pt], width: float, side: float, t0: float = 0.0, t1: float = 1.0, power: float = 0.75, offset: float = 0.0) -> str:
    """A tapered shape along `pts`, `side` fixed for the whole length (+1 toward the light,
    -1 away), `offset` a share of the local width toward that side."""
    line = M.catmull(pts)
    nrm = M.normals(line)
    n = len(line)
    left: list[Pt] = []
    right: list[Pt] = []
    for i, ((x, y), (nx, ny)) in enumerate(zip(line, nrm, strict=True)):
        t = i / (n - 1)
        if t < t0 or t > t1:
            continue
        u = (t - t0) / (t1 - t0)
        w = width * math.sin(math.pi * u) ** power
        cx, cy = x + nx * side * offset * w, y + ny * side * offset * w
        left.append((cx + nx * w / 2, cy + ny * w / 2))
        right.append((cx - nx * w / 2, cy - ny * w / 2))
    ring = left + right[::-1]
    return "M " + " L ".join(f.px(q) for q in ring) + " Z"


def jitter(name: str) -> tuple[float, float]:
    """Deterministic (width factor, length factor) per guide."""
    rng = random.Random(f"r2-{name}")
    return rng.uniform(0.80, 1.28), rng.uniform(0.86, 1.0)


def clumps(f: M.Frame, hair: str, lit_clumps: bool, streaks: bool) -> str:
    """Solid tone steps. A shadow clump, a lit clump, and (with `streaks`) one tapered highlight
    inside each lit clump, on its light side, ending before the tip. A shadow clump gets one soft
    separation on its dark edge. Nothing is drawn in pairs."""
    shadow = shadow_tone(hair)
    dv = dv_high(hair)
    mid = lit_tone(hair, dv * 0.42)
    hi = lit_tone(hair, dv)
    sep = shade(hair, 0.62)
    parts = []
    for name, (pts, w) in M.GUIDES.items():
        role = ROLE[name]
        if role == "base":
            continue
        wf, lf = jitter(name)
        side = light_side(pts)
        t1 = lf
        if role == "shadow":
            parts.append(f'<path d="{lens2(f, pts, w * wf, side, t1=t1, power=0.55)}" fill="{shadow}" />')
            parts.append(f'<path d="{lens2(f, pts, 0.035, side, t0=0.10, t1=min(t1, 0.9), power=0.5, offset=-1.7)}" fill="{sep}" opacity="0.75" />')
        elif lit_clumps:
            parts.append(f'<path d="{lens2(f, pts, w * wf, side, t1=t1, power=0.55)}" fill="{mid}" />')
            if streaks:
                parts.append(f'<path d="{lens2(f, pts, w * wf * 0.34, side, t0=0.10, t1=0.66, power=0.8, offset=0.45)}" fill="{hi}" />')
    return "".join(parts)


def ring(f: M.Frame, hair: str) -> str:
    """A broad band across the crown, concentric with the skull, in two pieces split at the part,
    tapered at each end and softer than the clump highlights so it reads as light on the whole
    head and not as one more stripe."""
    tone = lit_tone(hair, dv_high(hair) * 0.55)
    radius = 1.30
    parts = []
    for a0, a1, w in ((-150, -102, 0.22), (-86, -44, 0.17)):
        pts = [(radius * math.cos(math.radians(a)), radius * math.sin(math.radians(a))) for a in (a0 + (a1 - a0) * k / 5 for k in range(6))]
        parts.append(f'<path d="{lens2(f, pts, w, 1.0, power=0.7)}" fill="{tone}" opacity="0.75" />')
    return "".join(parts)


def sheen(f: M.Frame, hair: str) -> str:
    """The same band on its own, over r3."""
    return ring(f, hair)


# --- rendering ---------------------------------------------------------------------------------


def render(variant: str, hair_override: str | None = None) -> str:
    p = PRESETS[M.NAME]
    if hair_override:
        p = replace(p, hair_color=hair_override)
    f = M.Frame()
    hair = p.hair_color
    line = shade(hair, C._SOFT_HAIR_LINE_VALUE)
    knobs: dict[str, object] = {}
    treat = ""
    strands_off = False
    extend = False
    if variant != "today":
        knobs = {
            "_SOFT_GLOSS_LAYERS": (),
            "_SOFT_HAIR_DEPTH_TOP": (C._SOFT_HAIR_DEPTH_TOP[0], 0.0),
            "_SOFT_HAIR_DEPTH_BOTTOM": (C._SOFT_HAIR_DEPTH_BOTTOM[0], 0.0),
            "_SOFT_FACE_EDGE_OPACITY": 0.0,
        }
    if variant == "SS":
        treat, strands_off = clumps(f, hair, lit_clumps=False, streaks=False), True
    elif variant == "SH":
        treat = sheen(f, hair)
    elif variant == "S2":
        treat, strands_off = clumps(f, hair, True, True), True
    elif variant == "LS2":
        treat, strands_off = clumps(f, hair, True, True) + ring(f, hair), True
    elif variant == "P2":
        treat, strands_off, extend = clumps(f, hair, True, True) + ring(f, hair), True, True

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
        if style.openings is not None:
            sw = C._stroke_w(sk)
            for chain in style.openings(C._hair_fall(sk, pp)):
                group += (
                    f'<path d="{C._curve(sk.head_cx, sk.head_cy, sk.head_r, *chain)}" fill="{pp.skin_tone}" '
                    f'stroke="{C.OUTLINE}" stroke-width="{C._interior_w(sw):.2f}" stroke-linejoin="round" />'
                )
        if extend:
            group += M.pointed_fringe(f, hair, line)
        return out + group

    try:
        with M.patched(**knobs):
            C._hair_front = front
            if strands_off:
                HAIRSTYLES[p.hairstyle] = replace(original_style, strands=None)
            return render_character(replace(p, finish="soft"))
    finally:
        C._hair_front = original_front
        HAIRSTYLES[p.hairstyle] = original_style


VARIANTS = ["r3", "r3b", "today", "SS", "SH", "S2", "LS2", "P2"]
# Not the crops of round 1, so the sheet cannot be matched to the old one by position.
VIEWS = {"close": ("75 0 250 290", (400, 464)), "face": ("130 20 140 150", (560, 600))}


def draw(variant: str, view: str, hair: str | None = None) -> Image.Image:
    box, (w, h) = VIEWS[view]
    svg = render("r3" if variant == "r3b" else variant, hair)
    svg = re.sub(r'viewBox="[^"]+"', f'viewBox="{box}"', svg, count=1)
    svg = re.sub(r'width="400" height="\d+"', f'width="{w}" height="{h}"', svg, count=1)
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), background_color=GROUND))).convert("RGB")


def sheet(out: Path, tag: str, hair: str | None, seed: int, font: ImageFont.ImageFont) -> dict[str, str]:
    order = VARIANTS[:]
    random.Random(f"{seed}-{tag}").shuffle(order)
    for view in VIEWS:
        w, h = VIEWS[view][1]
        cols = 4
        img = Image.new("RGB", (cols * w + (cols - 1) * 6, 2 * h + 6), "white")
        for i, v in enumerate(order):
            im = draw(v, view, hair)
            x, y = (i % cols) * (w + 6), (i // cols) * (h + 6)
            img.paste(im, (x, y))
            ImageDraw.Draw(img).text((x + 10, y + 8), "ABCDEFGH"[i], fill="white", font=font)
            if view == "face":
                im.save(out / f"face-{tag}-{v}.png")
        img.save(out / f"{tag}-{view}-sheet.png")
    return {"ABCDEFGH"[i]: v for i, v in enumerate(order)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--out", default="out/soft/v3")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
    except OSError:
        font = ImageFont.load_default()
    keys = {tag: sheet(out, tag, hair, args.seed, font) for tag, hair in PALETTE.items()}
    (out / "key.json").write_text(json.dumps(keys, indent=1))
    print("wrote sheets to", out, "and the keys in key.json (do not open it before choosing)")


if __name__ == "__main__":
    main()
