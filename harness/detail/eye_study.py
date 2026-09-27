"""D2 of `docs/detail-plan.md`: the eye, redrawn in the spirit of
`ref-local/katherina_grok_real/`. A study for the owner to pick from; nothing
in `src/` changes (the candidates stand in for `character._eye`).

Every candidate keeps the aperture (`_eye_shape`: width, openness, lower lid,
tilt, corner) and the iris construction, and changes how the eye is lined:

- **A** today, after D1: one outline all the way round.
- **B** the upper lash as a filled band along the lid, thin at the inner
  corner and thick toward the outer one, ending in a flick past the corner;
  a short thin lower lash at the outer corner and the rest of the lower edge
  unlined; the top of the iris in a darker flat band.
- **C** B, with the lower edge kept as a faint interior line, so the white
  does not merge with pale skin.
- **D** C with a heavier lash and a longer flick.
- **E** C with a lid crease over the outer half. Our brows sit close over the
  eye (`brow_y = eye_y - 1.30 * eye_r`), so the crease has little room.

Written to `out/detail/`:

- `eye_study.png`: rows are the candidates; columns are Katherina (amber),
  Krista (teal), a very different palette (red eyes, dark skin), and
  Katherina "hollow" and "sorrow" (lids lowered);
- `eye_study_small.png`: Katherina and Krista at the smallest insert size
  (head radius 21 px) at 1x and 2x.
"""

import io
import math
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.colorutil import shade
from anime_character_creator.presets import EXPRESSIONS, PRESETS

OUT = "out/detail"
ORIGINAL = c._eye


def quad(p0, p1, p2, n):
    return [
        (
            (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1],
        )
        for t in (i / n for i in range(n + 1))
    ]


def aperture(er: float, f: c.FaceStyle):
    """`_eye_shape`'s points, in eye-local units (x outward, y down)."""
    w = er * f.eye_width * c._EYE_ASPECT
    top, bot = er * f.eye_openness, er * f.eye_lower_lid
    tilt = er * f.eye_tilt * 0.30
    reach = 0.55 * f.eye_corner
    inner, apex, outer, base = (-w, tilt), (w * 0.05, -top), (w, -tilt), (-w * 0.10, bot)

    def ctrl(corner, toward, y):
        return (corner[0] + (toward[0] - corner[0]) * reach, y)

    lid = quad(inner, ctrl(inner, apex, -top), apex, 16) + quad(apex, ctrl(outer, apex, -top), outer, 16)[1:]
    lower = quad(outer, ctrl(outer, base, bot), base, 16) + quad(base, ctrl(inner, base, bot), inner, 16)[1:]
    return lid, lower


def normals(pts):
    out = []
    for i in range(len(pts)):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        n = math.hypot(tx, ty) or 1.0
        nx, ny = ty / n, -tx / n
        if ny > 0:
            nx, ny = -nx, -ny
        out.append((nx, ny))
    return out


def poly(pts) -> str:
    return "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"


def line(pts) -> str:
    return "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts)


def candidate(lash_in=0.05, lash_out=0.16, flick=0.28, lower_lash=True, lower_line=False, crease=False, band=True):
    def eye(ex, ey, er, side, f, eye_color, sw, pupil_ratio=0.40):
        d, _lid = c._eye_shape(ex, ey, er, side, f)
        clip_id = f"eye-{'l' if side < 0 else 'r'}"

        def world(p):
            return (ex + side * p[0], ey + p[1])

        lid, lower = aperture(er, f)
        edge_w = c._outline_w(sw, c._EYE_OUTLINE_W)
        thin_w = c._interior_w(sw, 0.8)
        iris_r = f.iris_size * min(er * f.eye_width, er * (f.eye_openness + f.eye_lower_lid) / 2)
        iris_cy = ey + er * (f.eye_lower_lid - f.eye_openness) / 2 - iris_r * 0.10
        parts = [f'<defs><clipPath id="{clip_id}"><path d="{d}" /></clipPath></defs>']
        parts.append(f'<path d="{d}" fill="white" stroke="none" />')
        parts.append(f'<g clip-path="url(#{clip_id})">')
        parts.append(f'<circle cx="{ex:.1f}" cy="{iris_cy:.1f}" r="{iris_r:.1f}" fill="{shade(eye_color, 0.45)}" />')
        parts.append(f'<circle cx="{ex:.1f}" cy="{iris_cy:.1f}" r="{iris_r * 0.84:.1f}" fill="{eye_color}" />')
        if band:
            rr, dd = iris_r * 0.84, iris_r * 0.84 * 0.25
            a = math.sqrt(rr * rr - dd * dd)
            parts.append(
                f'<path d="M {ex - a:.2f} {iris_cy - dd:.2f} A {rr:.2f} {rr:.2f} 0 0 1 {ex + a:.2f} {iris_cy - dd:.2f} Z" '
                f'fill="{shade(eye_color, 0.68)}" />'
            )
        parts.append(
            f'<circle cx="{ex:.1f}" cy="{iris_cy + iris_r * 0.10:.1f}" r="{iris_r * pupil_ratio:.1f}" '
            f'fill="{shade(eye_color, 0.18)}" />'
        )
        parts.append(
            f'<circle cx="{ex - iris_r * 0.42:.1f}" cy="{iris_cy - iris_r * 0.48:.1f}" r="{iris_r * 0.34:.1f}" fill="white" />'
        )
        parts.append(
            f'<circle cx="{ex + iris_r * 0.35:.1f}" cy="{iris_cy + iris_r * 0.42:.1f}" r="{iris_r * 0.16:.1f}" '
            f'fill="white" opacity="0.85" />'
        )
        parts.append("</g>")
        if lower_line:
            parts.append(
                f'<path d="{line([world(p) for p in lower])}" fill="none" stroke="{c.OUTLINE}" '
                f'stroke-width="{thin_w:.2f}" stroke-linecap="round" />'
            )
        if lower_lash:
            k = len(lower) // 2
            seg = lower[: int(k * 0.55) + 1]
            parts.append(
                f'<path d="{line([world(p) for p in seg])}" fill="none" stroke="{c.OUTLINE}" '
                f'stroke-width="{edge_w * 0.8:.2f}" stroke-linecap="round" />'
            )
        ns = normals(lid)
        n = len(lid) - 1
        up, down = [], []
        for i, (p, nn) in enumerate(zip(lid, ns)):
            s = i / n
            t = max(edge_w * 0.5, er * (lash_in + (lash_out - lash_in) * s**1.4))
            if s < 0.12:
                t = max(edge_w * 0.5, t * s / 0.12)
            up.append((p[0] + nn[0] * t, p[1] + nn[1] * t))
            down.append((p[0] - nn[0] * edge_w * 0.5, p[1] - nn[1] * edge_w * 0.5))
        tx, ty = lid[-1][0] - lid[-4][0], lid[-1][1] - lid[-4][1]
        tl = math.hypot(tx, ty)
        tx, ty = tx / tl, ty / tl
        ang = math.radians(-28)
        fx, fy = tx * math.cos(ang) - ty * math.sin(ang), tx * math.sin(ang) + ty * math.cos(ang)
        tip = (lid[-1][0] + fx * er * flick, lid[-1][1] + fy * er * flick - er * lash_out * 0.5)
        shape = up + [tip] + list(reversed(down))
        parts.append(f'<path d="{poly([world(p) for p in shape])}" fill="{c.OUTLINE}" stroke="none" />')
        if crease:
            i0, i1 = int(n * 0.45), int(n * 0.92)
            gap = er * 0.12
            cr = []
            for i in range(i0, i1 + 1):
                s = i / n
                t = er * (lash_in + (lash_out - lash_in) * s**1.4) + gap
                cr.append((lid[i][0] + ns[i][0] * t, lid[i][1] + ns[i][1] * t))
            parts.append(
                f'<path d="{line([world(p) for p in cr])}" fill="none" stroke="{c.OUTLINE}" '
                f'stroke-width="{thin_w:.2f}" stroke-linecap="round" />'
            )
        return "".join(parts)

    return eye


VARIANTS = (
    ("A today", None),
    ("B lash, lower lash, iris band", candidate()),
    ("C B + faint lower edge", candidate(lower_line=True)),
    ("D C, heavier lash", candidate(lash_out=0.24, flick=0.40, lower_line=True)),
    ("E C + crease", candidate(lower_line=True, crease=True)),
)


def cases():
    k = PRESETS["katherina"]
    off = replace(k.outfit, hat_color=None)
    k = replace(k, outfit=off)
    krista = PRESETS["krista"]
    krista = replace(krista, outfit=replace(krista.outfit, goggle_color=None))
    odd = replace(PRESETS["satoko"], eye_color="#b0203a", skin_tone="#6b4a35")
    return [
        ("katherina", k),
        ("krista", krista),
        ("red eyes, dark skin", odd),
        ("katherina hollow", EXPRESSIONS["hollow"].applied_to(k)),
        ("katherina sorrow", EXPRESSIONS["sorrow"].applied_to(k)),
    ]


def face(p, scale, pad=(1.25, 0.95, 1.25, 0.9)):
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB")
    r, cx, cy = sk.head_r * scale, sk.head_cx * scale, sk.head_cy * scale
    return im.crop((int(cx - pad[0] * r), int(cy - pad[1] * r), int(cx + pad[2] * r), int(cy + pad[3] * r))), sk


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    rows, small = [], []
    for label, fn in VARIANTS:
        c._eye = fn or ORIGINAL
        try:
            row = []
            for name, p in cases():
                im, _ = face(p, 3)
                ImageDraw.Draw(im).text((3, 3), f"{label} / {name}", fill=(200, 0, 0))
                row.append(im)
            rows.append(row)
            srow = []
            for name, p in cases()[:2]:
                sk = c.skeleton_for(p)
                tiles = []
                for density in (1, 2):
                    k = 21.0 * density / sk.head_r
                    im, _ = face(p, k * 4, (1.4, 1.2, 1.4, 1.6))
                    tiles.append(im.resize((im.width // 4, im.height // 4), Image.LANCZOS))
                both = Image.new("RGB", (tiles[0].width + tiles[1].width + 4, tiles[1].height), (255, 255, 255))
                both.paste(tiles[0], (0, 0))
                both.paste(tiles[1], (tiles[0].width + 4, 0))
                big = both.resize((both.width * 2, both.height * 2), Image.NEAREST)
                ImageDraw.Draw(big).text((3, 3), f"{label} / {name} (1x, 2x, shown 2x)", fill=(200, 0, 0))
                srow.append(big)
            small.append(srow)
        finally:
            c._eye = ORIGINAL
    for name, grid in (("eye_study", rows), ("eye_study_small", small)):
        tw = max(t.width for r in grid for t in r)
        th = max(t.height for r in grid for t in r)
        sheet = Image.new("RGB", (len(grid[0]) * (tw + 4), len(grid) * (th + 4)), (190, 190, 190))
        for j, r in enumerate(grid):
            for i, t in enumerate(r):
                sheet.paste(t, (i * (tw + 4), j * (th + 4)))
        sheet.save(f"{OUT}/{name}.png")
        print(f"{OUT}/{name}.png", sheet.size)


if __name__ == "__main__":
    main()
