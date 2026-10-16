"""A cut's traced pieces over the figure, on a grid in head radii, for authoring by hand.

    ./harness/run.sh harness/soft_hair/grid.py risa

Writes `out/soft/grid-<preset>.png`: the flat figure's head and hair, a grid every half head
radius (x to the right, y down, origin at the head centre, the units every hair chain is in),
the front piece's outline in cyan, strands yellow, `locks` blue (shadow) or white (lit) with their widths, `front_shade` magenta, the underside region
green, openings orange. Numbers read off it go straight into chains.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from dataclasses import replace
from pathlib import Path

import cairosvg
from PIL import Image

sys.path.insert(0, "src")
from anime_character_creator import HAIRSTYLES, PRESETS, render_character, skeleton_for  # noqa: E402
from anime_character_creator.character import _curve, _hair_fall  # noqa: E402

SCALE = 4.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("preset", choices=sorted(PRESETS))
    ap.add_argument("--x", type=float, nargs=2, default=(-1.9, 1.9), help="x range, head radii")
    ap.add_argument("--y", type=float, nargs=2, default=(-1.7, 3.5), help="y range, head radii")
    ap.add_argument("--out", default="out/soft")
    args = ap.parse_args()
    p = PRESETS[args.preset]
    sk = skeleton_for(p)
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r
    style = HAIRSTYLES[p.hairstyle]
    fall = _hair_fall(sk, p)

    def d(chain: tuple, close: bool = True) -> str:
        return _curve(cx, cy, r, chain[0], chain[1], close=close)

    x0, x1 = cx + args.x[0] * r, cx + args.x[1] * r
    y0, y1 = cy + args.y[0] * r, cy + args.y[1] * r
    marks = []
    for k in range(int(args.x[0] * 2) - 1, int(args.x[1] * 2) + 2):
        u = k / 2
        x = cx + u * r
        marks.append(
            f'<line x1="{x:.2f}" y1="{y0:.2f}" x2="{x:.2f}" y2="{y1:.2f}" stroke="white" stroke-opacity="{0.7 if k % 2 == 0 else 0.3}" stroke-width="0.25" />'
            f'<text x="{x + 0.6:.2f}" y="{y0 + 4:.2f}" font-size="3.2" fill="white">{u:g}</text>'
        )
    for k in range(int(args.y[0] * 2) - 1, int(args.y[1] * 2) + 2):
        v = k / 2
        y = cy + v * r
        marks.append(
            f'<line x1="{x0:.2f}" y1="{y:.2f}" x2="{x1:.2f}" y2="{y:.2f}" stroke="white" stroke-opacity="{0.7 if k % 2 == 0 else 0.3}" stroke-width="0.25" />'
            f'<text x="{x0 + 0.6:.2f}" y="{y - 0.6:.2f}" font-size="3.2" fill="white">{v:g}</text>'
        )
    start, line, back = style.hairline(fall)
    marks.append(f'<path d="{d((start, line + back))}" fill="none" stroke="cyan" stroke-width="0.5" />')
    if style.strands:
        for ch in style.strands(fall):
            marks.append(f'<path d="{d(ch, False)}" fill="none" stroke="yellow" stroke-width="0.6" />')
    if style.front_shade:
        for ch in style.front_shade(fall):
            marks.append(f'<path d="{d(ch)}" fill="magenta" fill-opacity="0.25" stroke="magenta" stroke-width="0.4" />')
    if style.locks:
        from anime_character_creator.character import _lock_line

        for role, pts, w, _ln in style.locks(fall):
            line_pts = _lock_line(pts)
            path = "M " + " L ".join(f"{cx + x * r:.2f} {cy + y * r:.2f}" for x, y in line_pts)
            colour = "deepskyblue" if role == "shadow" else "white"
            marks.append(f'<path d="{path}" fill="none" stroke="{colour}" stroke-width="{w * r:.2f}" stroke-opacity="0.35" stroke-linecap="round" />')
            marks.append(f'<path d="{path}" fill="none" stroke="{colour}" stroke-width="0.4" stroke-dasharray="1.2 0.8" />')
    if style.underside:
        marks.append(f'<path d="{d(style.underside(fall)[0])}" fill="none" stroke="lime" stroke-width="0.4" />')
    if style.openings:
        for ch in style.openings(fall):
            marks.append(f'<path d="{d(ch)}" fill="none" stroke="orange" stroke-width="0.5" />')

    svg = render_character(replace(p, finish="flat"))
    svg = re.sub(r'viewBox="[^"]+"', f'viewBox="{x0:.2f} {y0:.2f} {x1 - x0:.2f} {y1 - y0:.2f}"', svg, count=1)
    svg = re.sub(
        r'width="400" height="\d+"',
        f'width="{int((x1 - x0) * SCALE)}" height="{int((y1 - y0) * SCALE)}"',
        svg,
        count=1,
    )
    svg = svg.replace("</svg>", "".join(marks) + "</svg>")
    png = cairosvg.svg2png(bytestring=svg.encode(), background_color="#2b1a55")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    Image.open(io.BytesIO(png)).convert("RGB").save(out / f"grid-{args.preset}.png")
    print(f"wrote {out}/grid-{args.preset}.png, head centre ({cx:.1f}, {cy:.1f}), r {r:.2f}, fall {fall:.3f}")


if __name__ == "__main__":
    main()
