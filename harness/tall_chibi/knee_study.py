"""R4a K0 of `docs/tall-chibi-plan.md`: where should the tall chibi's knee be?

The profile's `knee_y` is the reference's default boot top, not a knee: above
the hip on `tall_chibi_long_torso`. The legs' outline (`_seat_notch_d`: the
thigh taper, the calf, the inseam's control points) and the trousers' crotch
read it as a knee. This moves the knee for the legs only (the boots keep the
old landmark, which is what their shaft is measured off) to a fraction of the
hip-to-ankle run, and shows the legs:

- bare, on two adults with the underwear stubbed (the mannequin), the knee
  marked in red;
- clothed: Satoshi (trousers, tucked), Tenno (trousers), Satoko (a skirt).

Rows: the landmark as now, then the knee at 0.45, 0.5 and 0.55 of hip to
ankle (0.5 is `_real_knee_y`'s rule). Nothing in `src/` changes. Writes
`out/tall_chibi/knee_study.png`.
"""

import dataclasses
import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OFF = [
    f.name
    for f in dataclasses.fields(c.Outfit)
    if f.name.endswith("_color") and f.name not in ("boot_color", "underwear_color")
]
ROWS = (("landmark (now)", None), ("knee at 0.45", 0.45), ("knee at 0.5", 0.5), ("knee at 0.55", 0.55))
COLUMNS = (("krista", "bare"), ("gero", "bare"), ("satoshi", "dressed"), ("tenno", "dressed"), ("satoko", "dressed"))
SCALE = 3


def knee_for(sk: c.Skeleton, f: float) -> float:
    return sk.hip_y + (sk.ankle_y - sk.hip_y) * f


def render(name: str, view: str, f: float | None) -> Image.Image:
    p = PRESETS[name]
    if view == "bare":
        p = replace(p, outfit=replace(p.outfit, **dict.fromkeys(OFF)))
    sk = c.skeleton_for(p)
    saved = {n: getattr(c, n) for n in ("_legs_and_boots", "_boot", "_underpants", "_underwear_top")}
    try:
        if view == "bare":
            c._underpants = lambda *a, **k: ""
            c._underwear_top = lambda *a, **k: ""
        if f is not None:
            legs, boot = saved["_legs_and_boots"], saved["_boot"]

            def legs_with_knee(s: c.Skeleton, q: c.CharacterParams) -> str:
                return legs(replace(s, knee_y=knee_for(s, f)), q)

            def boot_on_landmark(s: c.Skeleton, *a, **k) -> str:
                return boot(replace(s, knee_y=sk.knee_y), *a, **k)

            c._legs_and_boots, c._boot = legs_with_knee, boot_on_landmark
        svg = c.render_character(p, sk, background="#ffffff")
    finally:
        for n, fn in saved.items():
            setattr(c, n, fn)
    if view == "bare":
        ky = sk.knee_y if f is None else knee_for(sk, f)
        svg = svg.replace(
            "</svg>",
            f'<line x1="{sk.head_cx - sk.head_r * 0.9:.1f}" y1="{ky:.1f}" x2="{sk.head_cx + sk.head_r * 0.9:.1f}" '
            f'y2="{ky:.1f}" stroke="#e02020" stroke-width="0.8" /></svg>',
        )
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGB")
    s, r, cx = SCALE, sk.head_r * SCALE, sk.head_cx * SCALE
    return im.crop((int(cx - 1.0 * r), int(sk.waist_y * s - 0.2 * r), int(cx + 1.0 * r), int(sk.foot_y * s + 0.1 * r)))


def main() -> None:
    os.makedirs("out/tall_chibi", exist_ok=True)
    rows = [(label, [render(n, v, f) for n, v in COLUMNS]) for label, f in ROWS]
    tw = max(t.width for _, ts in rows for t in ts)
    th = max(t.height for _, ts in rows for t in ts)
    pad, head = 6, 18
    sheet = Image.new("RGB", (pad + len(COLUMNS) * (tw + pad), pad + len(rows) * (th + head + pad)), (200, 200, 200))
    d = ImageDraw.Draw(sheet)
    y = pad
    for label, tiles in rows:
        d.text((pad, y + 3), label + "   (" + ", ".join(f"{n} {v}" for n, v in COLUMNS) + ")", fill=(0, 0, 0))
        x = pad
        for t in tiles:
            sheet.paste(t, (x, y + head))
            x += tw + pad
        y += th + head + pad
    sheet.save("out/tall_chibi/knee_study.png")
    print("out/tall_chibi/knee_study.png", sheet.size)


if __name__ == "__main__":
    main()
