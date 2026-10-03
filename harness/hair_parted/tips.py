"""The tips, ours against the reference's, at one scale (`docs/detail-status.md`,
D5 plan, after step 5: the owner, "the tips still look slightly off").

Katherina in `long_parted` without her hat, side tail, bat or staff, at the
trace's own length, so the geometry is the trace's and nothing is stretched;
the reference on `gate.py`'s calibration. Four windows in head radii: each
front lock's tips and each outer fall's tips. Each row: the reference
(brightened), ours, and our drawn ink in red over the reference in its own
frame, which is the comparison that counts.

    ./harness/run.sh harness/hair_parted/tips.py [TAG]

Written to `out/hair_parted/tips[_TAG].png`.
"""

import io
import json
import sys
from dataclasses import replace

sys.path.insert(0, "harness/hair_audit")
sys.path.insert(0, ".claude/skills/trace-reference")

import cairosvg
from PIL import Image, ImageDraw, ImageEnhance

import gate
import trace_lib as tl
from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/hair_parted"
REF = "ref-local/katherina_grok_nohat/katherina_grok_nohat.png"
PXR = 300
WINDOWS = {
    "front lock, left": (-1.05, 1.55, -0.45, 2.40),
    "front lock, right": (0.45, 1.55, 1.05, 2.40),
    "outer fall, left": (-1.75, 1.85, -1.05, 2.90),
    "outer fall, right": (1.05, 1.85, 1.85, 2.90),
}


def crop(img, cx, cy, r, box):
    k = PXR / r
    x0, y0, x1, y1 = box
    region = (cx + x0 * r - 2, cy + y0 * r - 2, cx + x1 * r + 2, cy + y1 * r + 2)
    c0 = img.crop(tuple(round(v) for v in region))
    return c0.resize((round((x1 - x0) * PXR), round((y1 - y0) * PXR)), Image.LANCZOS)


def ours():
    p = PRESETS["katherina"]
    p = replace(
        p,
        hairstyle="long_parted",
        hair_tail=0.0,
        familiar_color=None,
        outfit=replace(p.outfit, hat_color=None, hat_band_color=None, staff_color=None),
    )
    sk = c.skeleton_for(p)
    chin = sk.head_cy + sk.head_r
    p = replace(p, hair_length=(sk.head_cy + c._PARTED_BASE_TIP * sk.head_r - chin) / (sk.hip_y - chin))
    K = PXR / sk.head_r
    png = cairosvg.svg2png(bytestring=c.render_character(p, sk, background="white").encode(), scale=K)
    return Image.open(io.BytesIO(png)).convert("RGB"), (sk.head_cx * K, sk.head_cy * K, sk.head_r * K)


def main() -> None:
    tag = f"_{sys.argv[1]}" if len(sys.argv) > 1 else ""
    s, _, (ox, oy) = gate.calibrate(gate.measure(REF), gate.measure(gate.BASE))
    ref = ImageEnhance.Brightness(Image.open(REF).convert("RGB")).enhance(2.2)
    traced = ref.copy()
    d = ImageDraw.Draw(traced)
    t = json.load(open(f"{OUT}/trace.json"))
    for k, col in (("mass", (255, 255, 255)), ("line", (255, 60, 60)), ("lock_l", (255, 200, 0)), ("lock_r", (255, 200, 0))):
        d.line([(ox + x * s, oy + y * s) for x, y in tl.sample_chain(*t[k], per_segment=24)], fill=col, width=1)
    im, (cx, cy, r) = ours()
    # Our ink (the drawn lines, near black) in red over the reference, in the
    # reference's own frame: the exact comparison, where side-by-side tiles
    # only invite eyeballing.
    import numpy as np

    a = np.asarray(im).astype(int)
    # The outline is #0d0d0d; the jacket (#12152a) and the underside are darker
    # than the hair but not neutral, so only near-black pixels count.
    ink = a.max(2) < 30
    k = s / r
    small = Image.fromarray((ink * 255).astype(np.uint8)).resize(
        (round(im.width * k), round(im.height * k)), Image.LANCZOS
    )
    over = np.asarray(ref).astype(float).copy()
    m = np.zeros(over.shape[:2])
    dx, dy = round(ox - cx * k), round(oy - cy * k)
    sm = np.asarray(small).astype(float) / 255
    h = min(sm.shape[0], m.shape[0] - dy)
    w = min(sm.shape[1], m.shape[1] - dx)
    m[dy : dy + h, dx : dx + w] = sm[:h, :w]
    over = over * (1 - m[..., None] * 0.85) + np.array([255, 0, 0]) * m[..., None] * 0.85
    over = Image.fromarray(over.clip(0, 255).astype(np.uint8))
    rows = []
    for name, box in WINDOWS.items():
        rows.append(
            (
                name,
                [
                    crop(ref, ox, oy, s, box),
                    crop(im, cx, cy, r, box),
                    crop(over, ox, oy, s, box),
                ],
            )
        )
    W = max(sum(t.width + 6 for t in row) for _, row in rows)
    H = sum(max(t.height for t in row) + 20 for _, row in rows)
    sheet = Image.new("RGB", (W, H), (150, 150, 150))
    y = 0
    for name, row in rows:
        ImageDraw.Draw(sheet).text((4, y + 4), f"{name}: reference, ours, our ink (red) over the reference", fill=(0, 0, 0))
        x = 0
        for tile in row:
            sheet.paste(tile, (x, y + 18))
            x += tile.width + 6
        y += max(t.height for t in row) + 20
    path = f"{OUT}/tips{tag}.png"
    sheet.save(path)
    print(path, sheet.size)


if __name__ == "__main__":
    main()
