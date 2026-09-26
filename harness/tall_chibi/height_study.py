"""R4 of `docs/tall-chibi-plan.md`: how should a height slider stretch the tall
chibi? A study for the owner to pick from; nothing in `src/` changes.

A body profile names its landmarks in head radii from the head centre and its
figure height in heads; the foot is at `2 * heads - 1`. A height `h` keeps the
head, the shoulders and every width, and moves the landmarks below the
shoulder line so the shoulder-to-foot run becomes `h` times as long. The
extra (or missing) length goes:

- **A** evenly, torso and legs alike (every landmark below the shoulder
  scales about it);
- **B** to the legs only (the torso to the hip unchanged, the hip to the foot
  scaled);
- **C** two thirds to the legs, a third to the torso.

`build_skeleton` then fits the new height to the canvas, so on its own canvas
a taller figure has a smaller head. The sheet redraws every figure at one head
size with the feet on one line, which is how heights compare in a lineup.

Satoko (a skirt) and Satoshi (trousers), at heights 0.8, 0.9, 1.0, 1.15, 1.3.
Writes `out/tall_chibi/height_study.png`.
"""

import dataclasses
import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

HEIGHTS = (0.8, 0.9, 1.0, 1.15, 1.3)
NAMES = ("satoko", "satoshi")
VARIANTS = (("A  evenly", None), ("B  legs only", 1.0), ("C  legs two thirds", 2 / 3))
SCALE = 1.0


def stretched(profile: c.BodyProfile, h: float, legs_share: float | None) -> c.BodyProfile:
    sh, hip = profile.shoulder_y, profile.hip_y
    foot = 2 * profile.heads - 1
    run = foot - sh
    extra = run * (h - 1.0)
    if legs_share is None:

        def y(v):
            return None if v is None else sh + (v - sh) * h
    else:
        torso_extra, legs_extra = extra * (1 - legs_share), extra * legs_share

        def y(v):
            if v is None:
                return None
            if v <= hip:
                return sh + (v - sh) * (1 + torso_extra / (hip - sh))
            new_hip = hip + torso_extra
            return new_hip + (v - hip) * (1 + legs_extra / (foot - hip))

    new_foot = y(foot)
    return replace(
        profile,
        heads=(new_foot + 1) / 2,
        waist_y=y(profile.waist_y),
        hip_y=y(profile.hip_y),
        hem_y=y(profile.hem_y),
        knee_y=y(profile.knee_y),
        ankle_y=y(profile.ankle_y),
    )


def figure(name: str, h: float, share) -> tuple[Image.Image, c.Skeleton]:
    p = PRESETS[name]
    key = f"_study_{name}_{h}_{share}"
    c.BODY_TYPES[key] = stretched(c.BODY_TYPES[p.body], h, share)
    try:
        q = replace(p, body=key)
        sk = c.skeleton_for(q)
        svg = c.render_character(q, sk, background="#ffffff")
    finally:
        del c.BODY_TYPES[key]
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE))).convert("RGB")
    return im, sk


def main() -> None:
    os.makedirs("out/tall_chibi", exist_ok=True)
    ref_r = c.skeleton_for(PRESETS["satoko"]).head_r
    rows = []
    for label, share in VARIANTS:
        tiles = []
        for name in NAMES:
            for h in HEIGHTS:
                im, sk = figure(name, h, share)
                k = ref_r / sk.head_r
                im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
                foot = sk.foot_y * k
                cx = sk.head_cx * k
                w = int(2.0 * ref_r)
                top = int(foot - 9.5 * ref_r)
                tile = Image.new("RGB", (w, int(10 * ref_r)), (255, 255, 255))
                tile.paste(im.crop((int(cx - w / 2), max(0, top), int(cx + w / 2), int(foot + 0.5 * ref_r))), (0, max(0, -top)))
                ImageDraw.Draw(tile).text((3, 3), f"{name} {h}", fill=(0, 0, 0))
                tiles.append(tile)
        rows.append((label, tiles))
    tw, th = rows[0][1][0].size
    pad, head = 6, 18
    sheet = Image.new("RGB", (pad + len(rows[0][1]) * (tw + pad), pad + len(rows) * (th + head + pad)), (200, 200, 200))
    d = ImageDraw.Draw(sheet)
    y = pad
    for label, tiles in rows:
        d.text((pad, y + 3), label, fill=(0, 0, 0))
        x = pad
        for t in tiles:
            sheet.paste(t, (x, y + head))
            x += tw + pad
        y += th + head + pad
    sheet.save("out/tall_chibi/height_study.png")
    print("out/tall_chibi/height_study.png", sheet.size)


if __name__ == "__main__":
    main()
