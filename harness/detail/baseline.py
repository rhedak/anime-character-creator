"""D0 of `docs/detail-plan.md`: the baseline the detail steps are judged against.

Three sheets, written to `out/detail/`:

- `calibration.txt` and `face_vs_reference.png`: Katherina's face next to
  `ref-local/katherina_grok_real/`'s at one head size. The review of
  2026-09-27 cropped the reference by eye; this calibrates it the way the
  trace skill's step 2 does. Our face is measured on our render (the hat off,
  on black, the skin component) in head radii straight off the skeleton; the
  reference's face is its skin component seeded on the cheek. The scale is
  solved twice, from face width and from the widest row to the chin, and both
  are printed: they disagree by design (a round chibi face against a slim
  one), so the comparison uses the face-width scale, the one that answers
  "same head, how is it drawn".
- `smallest.png`: the smallest size `../valley_of_mist` shows a figure at, a
  four-column chapter-insert sheet (`sheet.sh --columns 4`, 2576 px wide)
  shown about 600 CSS px wide in its reader, so a figure about 0.23 of its
  render size. Drawn at 1x and 2x device pixels.
- `height_range.png` is `harness/tall_chibi/height_range.py`'s, run separately.

Nothing in `src/` changes.
"""

import dataclasses
import io
import os

import cairosvg
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS
from anime_character_creator.sheet import SheetParams, render_sheet

REF = "ref-local/katherina_grok_real/katherina_grok_real.png"
OUT = "out/detail"
REF_CHEEK = (628, 360)
K = 4
READER_CSS_W = 600
SHEET_W = 2576
MEMBERS = ("satoko", "satoshi", "krista", "katherina")


def face_component(a: np.ndarray, seed: tuple[int, int]) -> np.ndarray:
    col = a[seed[1], seed[0]]
    mask = np.abs(a - col).sum(2) < 60
    lab, _ = ndi.label(mask)
    face = lab == lab[seed[1], seed[0]]
    return ndi.binary_fill_holes(face)


def widest_and_chin(face: np.ndarray) -> tuple[int, int, int, int]:
    widths = face.sum(1)
    wy = int(np.argmax(widths))
    row = np.nonzero(face[wy])[0]
    chin = int(np.nonzero(face.any(1))[0].max())
    return wy, int(row.min()), int(row.max()), chin


def calibrate(lines: list[str]) -> tuple[float, float, float]:
    p = PRESETS["katherina"]
    p = dataclasses.replace(p, outfit=dataclasses.replace(p.outfit, hat_color=None))
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="black")
    a = np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=K))).convert("RGB")).astype(int)
    cx, cy, r = sk.head_cx * K, sk.head_cy * K, sk.head_r * K
    ours = face_component(a, (int(cx), int(cy + 0.4 * r)))
    wy, x0, x1, chin = widest_and_chin(ours)
    o_half = (x1 - x0) / 2 / r
    o_wy, o_chin = (wy - cy) / r, (chin - cy) / r
    o_cx = ((x0 + x1) / 2 - cx) / r
    lines.append(f"ours (head radii): widest row {o_wy:.3f} half-width {o_half:.3f} centre {o_cx:+.3f}, chin {o_chin:.3f}")

    ref = np.asarray(Image.open(REF).convert("RGB")).astype(int)
    rf = face_component(ref, REF_CHEEK)
    rwy, rx0, rx1, rchin = widest_and_chin(rf)
    lines.append(f"reference (px): widest row {rwy} x {rx0}..{rx1}, chin {rchin}")
    s_width = (rx1 - rx0) / 2 / o_half
    s_run = (rchin - rwy) / (o_chin - o_wy)
    lines.append(f"scale from face width: {s_width:.1f} px per head radius")
    lines.append(f"scale from widest row to chin: {s_run:.1f} px per head radius")
    lines.append(f"disagreement: {abs(s_width - s_run) / s_width:.0%} (the proportions differ by design)")
    ox = (rx0 + rx1) / 2 - o_cx * s_width
    oy = rwy - o_wy * s_width
    lines.append(f"reference head centre at face-width scale: ({ox:.0f}, {oy:.0f})")
    return ox, oy, s_width


def face_sheet(ox: float, oy: float, s: float) -> None:
    p = PRESETS["katherina"]
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=K))).convert("RGB")
    ref = Image.open(REF).convert("RGB")
    box = (-1.6, -1.5, 1.6, 2.3)

    def crop(img: Image.Image, cx: float, cy: float, r: float) -> Image.Image:
        return img.crop((int(cx + box[0] * r), int(cy + box[1] * r), int(cx + box[2] * r), int(cy + box[3] * r)))

    a = crop(im, sk.head_cx * K, sk.head_cy * K, sk.head_r * K)
    b = crop(ref, ox, oy, s)
    h = 760
    a = a.resize((int(a.width * h / a.height), h), Image.LANCZOS)
    b = b.resize((int(b.width * h / b.height), h), Image.LANCZOS)
    out = Image.new("RGB", (a.width + b.width + 10, h + 22), (200, 200, 200))
    out.paste(a, (0, 22))
    out.paste(b, (a.width + 10, 22))
    d = ImageDraw.Draw(out)
    d.text((4, 5), "ours (katherina, height 1.0)", fill=(0, 0, 0))
    d.text((a.width + 14, 5), "reference, calibrated on face width", fill=(0, 0, 0))
    out.save(f"{OUT}/face_vs_reference.png")


def smallest(lines: list[str]) -> None:
    svg = render_sheet(SheetParams(members=MEMBERS, columns=4))
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=SHEET_W)
    full = Image.open(io.BytesIO(png)).convert("RGB")
    k = READER_CSS_W / SHEET_W
    lines.append(f"sheet {full.size}, reader scale {k:.3f} (1x) and {2 * k:.3f} (2x)")
    one = full.resize((int(full.width * k), int(full.height * k)), Image.LANCZOS)
    two = full.resize((int(full.width * 2 * k), int(full.height * 2 * k)), Image.LANCZOS)
    out = Image.new("RGB", (two.width, one.height + two.height + 10), (200, 200, 200))
    out.paste(one, (0, 0))
    out.paste(two, (0, one.height + 10))
    out.save(f"{OUT}/smallest.png")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    lines: list[str] = []
    ox, oy, s = calibrate(lines)
    face_sheet(ox, oy, s)
    smallest(lines)
    with open(f"{OUT}/calibration.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
