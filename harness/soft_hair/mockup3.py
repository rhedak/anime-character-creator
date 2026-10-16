"""Round 3 of the soft hair mock-up (`docs/soft-hair-plan.md`, section 11 and the round 3 note).

    ./harness/run.sh harness/soft_hair/mockup3.py --pairs --seed 31     writes out/soft/v4/pairs-31/
    ./harness/run.sh harness/soft_hair/mockup3.py                       writes variant sheets to out/soft/v4/

Not production code. Built on `mockup2.py`, after the owner's round 2 pairs: the structure variants lost
because they lacked hairlines (round 2 switched the cut's own strand dashes off) and their highlights
were too strong, while the subtle crown sheen (SH) won. Two changes only:

  * the cut's strand dashes stay on, and a few fine dark hairlines are added along the clump edges,
    each stopping before the tip, drawn last;
  * clump highlights drop to about the strength of SH's band.

All variants sit on the package's soft finish (r3), which now has no gloss arc, depth wash or jaw shading.

    r3      reference (and `r3b`, an identical second copy, the judge's own noise)
    SH      the round 2 winner: r3 plus a soft band across the crown
    H       r3 plus the added hairlines
    SSh     value steps only (shadow clumps, soft separations) plus hairlines
    S2h     shadow and lit clumps with one faint highlight each, plus hairlines
    LS2h    S2h plus the crown band
    SSn, S2n, LS2n   the same three without the added hairlines (the cut's strand dashes only)
"""

from __future__ import annotations

import argparse
import io
import json
import math
import random
import re
import sys
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "harness/soft_hair")
sys.path.insert(0, "src")
import mockup as M  # noqa: E402
import mockup2 as K  # noqa: E402
from anime_character_creator.colorutil import shade  # noqa: E402

# Session 2: the added hairlines clashed with the cut's own strand dashes in session 1 (H lost, the
# others won in spite of them), so the three winners come back without the added hairlines, with S2h
# kept as the bridge to show whether those hairlines help or hurt.
CANDIDATES = ["SSn", "S2n", "LS2n", "S2h"]
HAIRLINE_VALUE = 0.50  # a dark tone of the hair, not the black outline


def hairlines(f: M.Frame, hair: str) -> str:
    """Fine dark tapered lines along the clump edges of the fringe and the inner curtains: one or two
    per clump, starting below the crown and stopping before the tip. Not on the outer clumps, where
    they ran parallel to the contour and doubled it, and not evenly spaced."""
    h, s, v = K._hsv(hair)
    light = v > 0.6
    tone = shade(hair, 0.66 if light else HAIRLINE_VALUE)
    opacity = 0.55 if light else 0.7
    parts = []
    for name, (pts, w) in M.GUIDES.items():
        if name.startswith("o"):
            continue
        rng = random.Random(f"hl3-{name}")
        side = K.light_side(pts)
        for _ in range(rng.choice((1, 2))):
            t0 = rng.uniform(0.12, 0.42)
            t1 = min(0.96, t0 + rng.uniform(0.26, 0.46))
            edge = rng.uniform(-0.30, 0.30)  # a share of the clump's width from its centre line
            width = rng.uniform(0.014, 0.024)
            parts.append(
                f'<path d="{K.lens2(f, pts, width, side, t0=t0, t1=t1, power=0.5, offset=edge * w / width)}" '
                f'fill="{tone}" opacity="{opacity}" />'
            )
    return "".join(parts)


def clumps_subtle(f: M.Frame, hair: str, lit: bool) -> str:
    """Round 2's clumps with the highlights cut to about the strength of the crown band."""
    shadow = K.shadow_tone(hair)
    dv = K.dv_high(hair)
    mid = K.lit_tone(hair, dv * 0.12)
    hi = K.lit_tone(hair, dv * 0.38)
    sep = shade(hair, 0.74)
    parts = []
    for name, (pts, w) in M.GUIDES.items():
        role = K.ROLE[name]
        if role == "base" or name in M.RIM:  # the rim clumps hugged the contour and read as a seam
            continue
        wf, lf = K.jitter(name)
        side = K.light_side(pts)
        if role == "shadow":
            parts.append(f'<path d="{K.lens2(f, pts, w * wf, side, t1=lf, power=0.55)}" fill="{shadow}" />')
            parts.append(f'<path d="{K.lens2(f, pts, 0.035, side, t0=0.10, t1=min(lf, 0.9), power=0.5, offset=-1.7)}" fill="{sep}" opacity="0.6" />')
        elif lit:
            parts.append(f'<path d="{K.lens2(f, pts, w * wf, side, t1=lf, power=0.55)}" fill="{mid}" />')
            parts.append(f'<path d="{K.lens2(f, pts, w * wf * 0.30, side, t0=0.10, t1=0.62, power=0.8, offset=0.45)}" fill="{hi}" />')
    return "".join(parts)


BUILDERS = {
    "r3": None,
    "r3b": None,
    "SH": K.sheen,
    "H": hairlines,
    "SSh": lambda f, h: clumps_subtle(f, h, lit=False) + hairlines(f, h),
    "S2h": lambda f, h: clumps_subtle(f, h, lit=True) + hairlines(f, h),
    "LS2h": lambda f, h: clumps_subtle(f, h, lit=True) + K.ring(f, h) + hairlines(f, h),
    "SSn": lambda f, h: clumps_subtle(f, h, lit=False),
    "S2n": lambda f, h: clumps_subtle(f, h, lit=True),
    "LS2n": lambda f, h: clumps_subtle(f, h, lit=True) + K.ring(f, h),
}

# One pattern for every sheet, as in round 2: row N is the same comparison on every colour, with the
# same side first. Slots 1 to 4 are the candidates against the sheet's reference; the fifth is a
# control (r3b against r3 on the r3 sheets, SH against r3 on the SH sheets).
PAIR_SHEETS = {
    "red-vs-r3": ("red", "r3", ("r3b", "r3")),
    "dark-vs-r3": ("dark", "r3", ("r3b", "r3")),
    "blond-vs-r3": ("blond", "r3", ("r3b", "r3")),
    "grey-vs-r3": ("grey", "r3", ("r3b", "r3")),
    "red-vs-SH": ("red", "SH", ("SH", "r3")),
    "dark-vs-SH": ("dark", "SH", ("SH", "r3")),
}
VIEWS = K.VIEWS


def draw(variant: str, view: str, hair: str | None) -> Image.Image:
    box, (w, h) = VIEWS[view]
    svg = K.render_treated(BUILDERS[variant], strands_off=False, hair_override=hair)
    svg = re.sub(r'viewBox="[^"]+"', f'viewBox="{box}"', svg, count=1)
    svg = re.sub(r'width="400" height="\d+"', f'width="{w}" height="{h}"', svg, count=1)
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), background_color=K.GROUND))).convert("RGB")


def pair_sheets(out: Path, seed: int, font: ImageFont.ImageFont) -> None:
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(f"pairs3-{seed}")
    slots = [*CANDIDATES, "control"]
    rng.shuffle(slots)
    first_left = {slot: rng.random() < 0.5 for slot in slots}
    key: dict[str, dict[str, dict[str, str]]] = {}
    for name, (tag, other, control) in PAIR_SHEETS.items():
        sides = []
        for slot in slots:
            a, b = control if slot == "control" else (slot, other)
            sides.append((a, b) if first_left[slot] else (b, a))
        key[name] = {str(i + 1): {"left": left, "right": right} for i, (left, right) in enumerate(sides)}
        for view, suffix in (("close", "app"), ("face", "zoom")):
            w, h = VIEWS[view][1]
            if view == "face":
                w, h = w // 2, h // 2
            img = Image.new("RGB", (2 * w + 6, len(sides) * (h + 6) - 6), "white")
            for i, (left, right) in enumerate(sides):
                y = i * (h + 6)
                for x, v in ((0, left), (w + 6, right)):
                    im = draw(v, view, K.PALETTE[tag])
                    img.paste(im.resize((w, h), Image.LANCZOS) if im.size != (w, h) else im, (x, y))
                ImageDraw.Draw(img).text((10, y + 8), str(i + 1), fill="white", font=font)
            img.save(out / f"{name}-{suffix}.png")
    (out / "pairs-key.json").write_text(json.dumps(key, indent=1))
    print("wrote pair sheets to", out, "and pairs-key.json (do not open it before choosing)")


def faces(out: Path) -> None:
    """Each variant's head on its own, by name, for looking at while building (not for the owner)."""
    out.mkdir(parents=True, exist_ok=True)
    for tag, hair in K.PALETTE.items():
        for v in BUILDERS:
            draw(v, "face", hair).save(out / f"face-{tag}-{v}.png")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--seed", type=int, default=31)
    ap.add_argument("--pairs", action="store_true", help="write the forced-choice pair sheets to <out>/pairs-<seed>/")
    ap.add_argument("--out", default="out/soft/v4")
    args = ap.parse_args()
    out = Path(args.out)
    if args.pairs:
        pair_sheets(out / f"pairs-{args.seed}", args.seed, ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30))
    else:
        faces(out)
        print("wrote each variant's face to", out)


if __name__ == "__main__":
    main()
