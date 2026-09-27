"""D4a of `docs/detail-plan.md`: should the widths follow the height a little?

`stretched` (the height slider) keeps every body width, so a figure at 1.3
has the shoulders of one at 1.0 and reads lanky. The owner's call on
2026-09-27: widths may follow the height a little. This scales the body's
widths (shoulders, waist, hips, hem, arms and where they hang, legs; not the
neck, which belongs with the head) by `1 + k * (height - 1)` after the
stretch, for k = 0 (today), 0.3 and 0.6: at 1.3 that is 9% and 18% wider, at
0.8 6% and 12% narrower. At height 1.0 the stretch is not applied at all, so
nothing there moves.

Drawn at one head size with the feet on one line, which is how heights
compare. Two sheets in `out/detail/`, `width_study_a.png` and `_b.png`, rows
k, each character at 0.8, 1.0 and 1.3. Also reports any render whose ink
reaches its canvas edge.
"""

import io
import os
from dataclasses import replace

import cairosvg
import numpy as np
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"
KS = (0.0, 0.3, 0.6)
HEIGHTS = (0.8, 1.0, 1.3)
WIDTHS = ("shoulder_half_w", "waist_half_w", "hip_half_w", "hem_half_w", "arm_half_w", "arm_x", "leg_half_w")
STRETCHED = c.stretched


def with_k(k: float):
    def stretched(sk, h, refit, legs_share=2 / 3):
        out = STRETCHED(sk, h, refit, legs_share)
        f = 1.0 + k * (h - 1.0)
        cx = out.head_cx
        changes = {n: getattr(out, n) * f for n in WIDTHS if n != "arm_x"}
        changes["arm_x"] = cx + (out.arm_x - cx) * f if out.arm_x > cx * 0.5 else out.arm_x * f
        return replace(out, **changes)

    return stretched


def cases():
    krista = PRESETS["krista"]
    off = [n for n in c.Outfit.__dataclass_fields__ if n.endswith("_color") and n not in ("underwear_color", "boot_color")]
    base = replace(krista, outfit=replace(krista.outfit, **dict.fromkeys(off)))
    return (
        [(n, PRESETS[n]) for n in ("satoko", "satoshi", "krista", "keiko")],
        [(n, PRESETS[n]) for n in ("kyoko", "reika", "katherina")] + [("krista base layer", base)],
    )


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    ref_r = c.skeleton_for(PRESETS["satoko"]).head_r
    notes = []
    for tag, group in zip("ab", cases(), strict=True):
        rows = []
        for k in KS:
            c.stretched = with_k(k)
            try:
                row = []
                for name, p in group:
                    for h in HEIGHTS:
                        q = replace(p, height=h)
                        sk = c.skeleton_for(q)
                        png = cairosvg.svg2png(bytestring=c.render_character(q, sk).encode())
                        im = Image.open(io.BytesIO(png)).convert("RGBA")
                        a = np.array(im)[:, :, 3]
                        if a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any():
                            notes.append(f"{name} h{h} k{k}: ink reaches the canvas edge")
                        white = Image.new("RGBA", im.size, (255, 255, 255, 255))
                        im = Image.alpha_composite(white, im).convert("RGB")
                        s = ref_r / sk.head_r
                        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
                        foot, cx = sk.foot_y * s, sk.head_cx * s
                        w, top = int(2.9 * ref_r), int(foot - 11.5 * ref_r)
                        tile = Image.new("RGB", (w, int(12.1 * ref_r)), (255, 255, 255))
                        crop = im.crop((int(cx - w / 2), max(0, top), int(cx + w / 2), min(im.height, int(foot + 0.5 * ref_r))))
                        tile.paste(crop, (0, max(0, -top)))
                        ImageDraw.Draw(tile).text((3, 3), f"{name} h{h} k{k}", fill=(200, 0, 0))
                        row.append(tile)
                rows.append(row)
            finally:
                c.stretched = STRETCHED
        tw, th = rows[0][0].size
        sheet = Image.new("RGB", (len(rows[0]) * (tw + 3), len(rows) * (th + 6)), (190, 190, 190))
        for j, r in enumerate(rows):
            for i, t in enumerate(r):
                sheet.paste(t, (i * (tw + 3) + (i // 3) * 0, j * (th + 6)))
        sheet.save(f"{OUT}/width_study_{tag}.png")
        print(f"{OUT}/width_study_{tag}.png", sheet.size)
    print("\n".join(notes) or "no figure reaches its canvas edge")


if __name__ == "__main__":
    main()
