"""D3 of `docs/detail-plan.md`: the face maturity slider, for the owner to judge.

`CharacterParams.face_age` (0 the chibi face, up to 1 maturity) moves everything welded to
the skull onto `Skeleton.face_build`, the retired adult build's face terms
(the skull's taper to a jaw, the eye's shape, size and spacing, the mouth),
plus its own: the eyes a little lower (`_MATURE_EYE_DROP`) and a nose growing
in (`_nose`).

Written to `out/detail/`:

- `maturity_faces.png`: faces, rows maturity 0, 0.5, 1; columns Satoko,
  Katherina (long hair framing the jaw), Satoshi, Gero (a beard on the jaw);
- `maturity_grid.png`: whole figures, maturity 0, 0.5, 1 against height 0.8,
  1.0, 1.3, Satoko and Satoshi, at one head size with the feet on one line;
- `maturity_sweep.png`: Satoko's face at maturity 0 to 1 in steps of 0.1,
  to look for anything that jumps rather than moves.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"


def render(p: c.CharacterParams, scale: float) -> tuple[Image.Image, c.Skeleton]:
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=scale))).convert("RGB"), sk


def face(p: c.CharacterParams, label: str) -> Image.Image:
    im, sk = render(p, 3)
    r, cx, cy = sk.head_r * 3, sk.head_cx * 3, sk.head_cy * 3
    im = im.crop((int(cx - 1.35 * r), int(cy - 1.1 * r), int(cx + 1.35 * r), int(cy + 1.55 * r)))
    ImageDraw.Draw(im).text((3, 3), label, fill=(200, 0, 0))
    return im


def grid(rows: list[list[Image.Image]], path: str) -> None:
    tw = max(t.width for r in rows for t in r)
    th = max(t.height for r in rows for t in r)
    sheet = Image.new("RGB", (len(rows[0]) * (tw + 4), len(rows) * (th + 4)), (190, 190, 190))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            sheet.paste(t, (i * (tw + 4), j * (th + 4)))
    sheet.save(path)
    print(path, sheet.size)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    k = PRESETS["katherina"]
    k = replace(k, outfit=replace(k.outfit, hat_color=None))
    people = [("satoko", PRESETS["satoko"]), ("katherina", k), ("satoshi", PRESETS["satoshi"]), ("gero", PRESETS["gero"])]
    grid(
        [[face(replace(p, face_age=m), f"{n} maturity {m}") for n, p in people] for m in (0.0, 0.5, 1.0)],
        f"{OUT}/maturity_faces.png",
    )

    ref_r = c.skeleton_for(PRESETS["satoko"]).head_r
    rows = []
    for m in (0.0, 0.5, 1.0):
        row = []
        for n in ("satoko", "satoshi"):
            for h in (0.8, 1.0, 1.3):
                im, sk = render(replace(PRESETS[n], face_age=m, height=h), 1.0)
                s = ref_r / sk.head_r
                im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
                foot, cx = sk.foot_y * s, sk.head_cx * s
                w, top = int(2.4 * ref_r), int(foot - 11.5 * ref_r)
                tile = Image.new("RGB", (w, int(12.1 * ref_r)), (255, 255, 255))
                tile.paste(im.crop((int(cx - w / 2), max(0, top), int(cx + w / 2), int(foot + 0.5 * ref_r))), (0, max(0, -top)))
                ImageDraw.Draw(tile).text((3, 3), f"{n} h{h} m{m}", fill=(200, 0, 0))
                row.append(tile)
        rows.append(row)
    grid(rows, f"{OUT}/maturity_grid.png")

    sweep = [face(replace(PRESETS["satoko"], face_age=i / 10), f"{i / 10:.1f}") for i in range(11)]
    grid([sweep[:6], sweep[6:] + [Image.new("RGB", sweep[0].size, (190, 190, 190))]], f"{OUT}/maturity_sweep.png")


if __name__ == "__main__":
    main()
