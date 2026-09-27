"""D4b of `docs/detail-plan.md`, round three: how far should the taper go at
the tall end? The owner: at 1.3 the upper arm reads much wider than the
forearm. D4a widens the arm 18% there and the full taper takes the wrist in
34% of that, all below the elbow (the upper arm is full width down to it), so
the upper arm comes out about 1.5 times the wrist.

Rows: the taper at 1.3 capped at 1 (the sweep), 0.7, 0.5 (so `clamp((h -
0.8) / 0.5, 0, 1) * cap`); columns: Krista's base layer and Satoshi at 1.3
and 1.0, the arms at 2x. The upper-arm-to-wrist ratio printed on each.
Writes `out/detail/taper_cap.png`.

A record: the taper is now `Skeleton.limb_taper`, set from the height
(`character._limb_taper_at`), and the `_LIMB_TAPER` this patches is gone, so
it no longer draws what it did.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"


def main():
    os.makedirs(OUT, exist_ok=True)
    krista = PRESETS["krista"]
    off = [n for n in c.Outfit.__dataclass_fields__ if n.endswith("_color") and n not in ("underwear_color", "boot_color")]
    base = replace(krista, outfit=replace(krista.outfit, **dict.fromkeys(off)))
    rows = []
    for cap in (1.0, 0.7, 0.5):
        row = []
        for name, p in (("krista base layer", base), ("satoshi", PRESETS["satoshi"])):
            for h in (1.3, 1.0):
                t = min(1.0, max(0.0, (h - 0.8) / 0.5)) * cap
                c._LIMB_TAPER = t
                try:
                    q = replace(p, height=h)
                    sk = c.skeleton_for(q)
                    svg = c.render_character(q, sk, background="#ffffff")
                finally:
                    c._LIMB_TAPER = 0.0
                im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=2))).convert("RGB")
                r, cx = sk.head_r * 2, sk.head_cx * 2
                crop = im.crop((int(cx - 2.1 * r), int(sk.shoulder_y * 2 - 0.2 * r), int(cx + 0.2 * r), int(sk.hip_y * 2 + 1.0 * r)))
                lb = sk.build + t * (1 - sk.build)
                ratio = 1.0 / (1.0 - 0.34 * lb)
                ImageDraw.Draw(crop).text((3, 3), f"{name} h{h} cap {cap} taper {t:.2f} upper/wrist {ratio:.2f}", fill=(200, 0, 0))
                row.append(crop)
        rows.append(row)
    tw = max(x.width for r in rows for x in r)
    th = max(x.height for r in rows for x in r)
    sheet = Image.new("RGB", (len(rows[0]) * (tw + 4), len(rows) * (th + 6)), (190, 190, 190))
    for j, r in enumerate(rows):
        for i, x in enumerate(r):
            sheet.paste(x, (i * (tw + 4), j * (th + 6)))
    sheet.save(f"{OUT}/taper_cap.png")
    print(f"{OUT}/taper_cap.png", sheet.size)


if __name__ == "__main__":
    main()
