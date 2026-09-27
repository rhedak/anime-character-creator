"""D2 of `docs/detail-plan.md`: the built lash on the men, at three strengths.

The lash and its flick were picked on women; on the narrow, sharp-cornered
eyes of Satoshi, Daizen and Tenno the flick reads as winged eyeliner. This
scales the lash's outer thickness (above the inner one) and the flick by 1.0,
0.6 and 0.3, Katherina alongside. Writes `out/detail/d2_men.png`.
"""

import sys; sys.path.insert(0, "harness/detail")
from PIL import Image, ImageDraw
import eye_study as es
from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS
OUT0, FL0 = c._LASH_OUTER, c._LASH_FLICK
rows = []
for lash in (1.0, 0.6, 0.3):
    c._LASH_OUTER = c._LASH_INNER + (OUT0 - c._LASH_INNER) * lash
    c._LASH_FLICK = FL0 * lash
    row = []
    for n in ("satoshi", "daizen", "tenno", "katherina"):
        im, _ = es.face(PRESETS[n], 3, (1.25, 0.6, 1.25, 0.35))
        ImageDraw.Draw(im).text((3, 3), f"{n} lash {lash}", fill=(200, 0, 0)); row.append(im)
    rows.append(row)
c._LASH_OUTER, c._LASH_FLICK = OUT0, FL0
w = max(t.width for r in rows for t in r); h = max(t.height for r in rows for t in r)
out = Image.new("RGB", (4 * (w + 4), 3 * (h + 4)), (190, 190, 190))
for j, r in enumerate(rows):
    for i, t in enumerate(r): out.paste(t, (i * (w + 4), j * (h + 4)))
out.save("out/detail/d2_men.png"); print(out.size)
